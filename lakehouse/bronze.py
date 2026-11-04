"""Bronze: o arquivo do INMET como chegou, uma linha por medicao.

Nada e tipado aqui. Os valores ficam como texto num MAP<string,string>
com o nome original da coluna, porque o cabecalho do INMET muda entre
anos e a bronze nao deve quebrar por isso. Cada arquivo recebe um
_source_id estavel (hash do nome do arquivo): reprocessar o mesmo
arquivo substitui as linhas dele e nao duplica nada.

Arquivos que nao parseiam vao para arquivos_rejeitados com o erro.
"""

from __future__ import annotations

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

from lakehouse import io
from lakehouse.inmet_parser import ENCODING, split_text

TABLE = "inmet_horario"
REJECTED_TABLE = "arquivos_rejeitados"

_ROW = T.StructType(
    [
        T.StructField("data_raw", T.StringType()),
        T.StructField("hora_raw", T.StringType()),
        T.StructField("medidas", T.MapType(T.StringType(), T.StringType())),
    ]
)

_PARSED = T.StructType(
    [
        T.StructField("regiao", T.StringType()),
        T.StructField("uf", T.StringType()),
        T.StructField("nome_estacao", T.StringType()),
        T.StructField("codigo_estacao", T.StringType()),
        T.StructField("latitude_raw", T.StringType()),
        T.StructField("longitude_raw", T.StringType()),
        T.StructField("altitude_raw", T.StringType()),
        T.StructField("linhas", T.ArrayType(_ROW)),
        T.StructField("erro", T.StringType()),
    ]
)


def parse_content(content: bytes) -> dict:
    """Funcao pura (testavel sem Spark) usada pela UDF da bronze."""
    try:
        text = bytes(content).decode(ENCODING)
        meta, header, rows = split_text(text)
        raw_meta = [line.split(";") for line in text.splitlines()[4:7]]
        lat, lon, alt = (parts[1].strip() if len(parts) > 1 else None for parts in raw_meta)
        linhas = []
        for row in rows:
            values = dict(zip(header, row, strict=False))
            linhas.append(
                {
                    "data_raw": values.pop("Data", None),
                    "hora_raw": values.pop("Hora UTC", None),
                    "medidas": values,
                }
            )
        return {
            "regiao": meta.regiao,
            "uf": meta.uf,
            "nome_estacao": meta.nome_estacao,
            "codigo_estacao": meta.codigo_estacao,
            "latitude_raw": lat,
            "longitude_raw": lon,
            "altitude_raw": alt,
            "linhas": linhas,
            "erro": None,
        }
    except Exception as exc:  # noqa: BLE001 - o erro vira dado auditavel
        return {"linhas": [], "erro": f"{type(exc).__name__}: {exc}"}


def run(spark: SparkSession, input_path: str, bronze_root: str, catalog: str | None = None) -> dict:
    parse = F.udf(parse_content, _PARSED)

    files = (
        spark.read.format("binaryFile")
        .option("pathGlobFilter", "*.[cC][sS][vV]")
        .option("recursiveFileLookup", "true")
        .load(input_path)
        .select(
            F.col("path").alias("_source_file"),
            F.substring(F.sha1(F.element_at(F.split("path", "/"), -1)), 1, 16).alias("_source_id"),
            F.sha2("content", 256).alias("_content_sha256"),
            parse("content").alias("p"),
        )
    )
    files = io.with_ingestion_time(files).cache()

    rejected = files.filter(F.col("p.erro").isNotNull()).select(
        "_source_file", "_source_id", "_content_sha256", F.col("p.erro").alias("erro"), "_ingested_at"
    )
    accepted = files.filter(F.col("p.erro").isNull())

    rows = accepted.select(
        "_source_id",
        "_source_file",
        "_content_sha256",
        "_ingested_at",
        "p.regiao",
        "p.uf",
        "p.nome_estacao",
        "p.codigo_estacao",
        "p.latitude_raw",
        "p.longitude_raw",
        "p.altitude_raw",
        F.explode("p.linhas").alias("l"),
    ).select("*", "l.data_raw", "l.hora_raw", "l.medidas").drop("l")

    source_ids = [r["_source_id"] for r in accepted.select("_source_id").distinct().collect()]
    path = io.table_path(bronze_root, TABLE)
    io.replace_sources(spark, rows, path, source_ids)
    io.register_table(spark, catalog, "bronze", TABLE, path)

    rejected_ids = [r["_source_id"] for r in rejected.select("_source_id").collect()]
    rejected_path = io.table_path(bronze_root, REJECTED_TABLE)
    if rejected_ids:
        io.replace_sources(spark, rejected, rejected_path, rejected_ids)
        io.register_table(spark, catalog, "bronze", REJECTED_TABLE, rejected_path)

    result = {
        "arquivos_aceitos": len(source_ids),
        "arquivos_rejeitados": len(rejected_ids),
        "linhas": rows.count(),
    }
    files.unpersist()
    return result
