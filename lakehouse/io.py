"""Escrita idempotente nas camadas.

Cada camada tem uma regra de reprocessamento diferente, e as tres sao
idempotentes: rodar duas vezes com a mesma entrada da o mesmo estado.

- bronze: substitui as linhas dos arquivos reprocessados (_source_id)
  e mantem o resto. Delta usa replaceWhere; Parquet usa overwrite
  dinamico de particao.
- silver: recalculada inteira a partir da bronze (overwrite).
- gold: MERGE pela chave de negocio.
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from lakehouse.spark import DELTA, table_format


def table_path(root: str, name: str) -> str:
    return f"{root.rstrip('/')}/{name}"


def _exists(spark: SparkSession, path: str, fmt: str) -> bool:
    if fmt == DELTA:
        from delta.tables import DeltaTable

        return DeltaTable.isDeltaTable(spark, path)
    try:
        spark.read.parquet(path).limit(1).collect()
        return True
    except Exception:  # noqa: BLE001 - caminho inexistente ou vazio
        return False


def read_table(spark: SparkSession, path: str) -> DataFrame:
    return spark.read.format(table_format()).load(path)


def replace_sources(spark: SparkSession, df: DataFrame, path: str, source_ids: list[str]) -> None:
    """Bronze: grava df substituindo apenas os _source_id informados."""
    fmt = table_format()
    if not source_ids:
        return
    if fmt == DELTA:
        writer = df.write.format("delta")
        if _exists(spark, path, fmt):
            quoted = ", ".join(f"'{s}'" for s in source_ids)
            writer = writer.mode("overwrite").option("replaceWhere", f"_source_id IN ({quoted})")
        else:
            writer = writer.mode("overwrite")
        writer.save(path)
    else:
        (
            df.write.mode("overwrite")
            .option("partitionOverwriteMode", "dynamic")
            .partitionBy("_source_id")
            .parquet(path)
        )


def overwrite(df: DataFrame, path: str) -> None:
    """Silver: substitui a tabela inteira (atomico no Delta)."""
    fmt = table_format()
    writer = df.write.format(fmt).mode("overwrite")
    if fmt == DELTA:
        writer = writer.option("overwriteSchema", "true")
    writer.save(path)


def merge(spark: SparkSession, df: DataFrame, path: str, keys: list[str]) -> None:
    """Gold: upsert pela chave de negocio."""
    fmt = table_format()
    if not _exists(spark, path, fmt):
        df.write.format(fmt).mode("overwrite").save(path)
        return

    if fmt == DELTA:
        from delta.tables import DeltaTable

        condition = " AND ".join(f"t.{k} = s.{k}" for k in keys)
        (
            DeltaTable.forPath(spark, path)
            .alias("t")
            .merge(df.alias("s"), condition)
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )
        return

    # Parquet nao tem MERGE: remove as chaves que chegaram, une com o
    # novo lote e materializa antes de sobrescrever o mesmo caminho.
    existing = spark.read.parquet(path)
    kept = existing.join(df.select(*keys).distinct(), on=keys, how="left_anti")
    combined = kept.unionByName(df).localCheckpoint(eager=True)
    combined.write.mode("overwrite").parquet(path)


def register_table(spark: SparkSession, catalog: str | None, schema: str, name: str, path: str) -> None:
    """Registra a tabela no Unity Catalog como tabela externa sobre o
    caminho ja escrito. Sem catalogo (execucao local), nao faz nada."""
    if not catalog:
        return
    spark.sql(
        f"CREATE TABLE IF NOT EXISTS `{catalog}`.`{schema}`.`{name}` "
        f"USING DELTA LOCATION '{path}'"
    )


def with_ingestion_time(df: DataFrame) -> DataFrame:
    return df.withColumn("_ingested_at", F.current_timestamp())
