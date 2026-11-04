"""Silver: medicoes tipadas, sem duplicatas, com municipio IBGE.

- Tipagem nativa do Spark (sem UDF): virgula decimal, sentinela -9999
  e string vazia viram NULL; datas em tres formatos; hora "HHMM UTC"
  ou "HH:MM". Tudo com try_*, para funcionar tambem com ANSI ligado.
- O cabecalho do INMET muda entre anos, entao as colunas de interesse
  sao localizadas pelo nome normalizado, nao pela grafia exata.
- Duplicatas (mesma estacao, data e hora) ficam com a ingestao mais
  recente.
- O municipio e resolvido com o MunicipioResolver do projeto 13 (com a
  guarda de UF). O que nao resolve com seguranca vai para a tabela
  quarentena com o motivo - nada e descartado em silencio.
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql import types as T

from lakehouse import io
from lakehouse.bronze import TABLE as BRONZE_TABLE
from lakehouse.municipio_resolver import MunicipioResolver, normalize_name
from lakehouse.ufs import codigo_uf

TABLE = "medicoes_horarias"
QUARANTINE_TABLE = "quarentena"

# prefixo do nome normalizado da coluna no INMET -> coluna canonica
MEASURES = {
    "PRECIPITACAO TOTAL HORARIO": "precipitacao_mm",
    "TEMPERATURA DO AR BULBO SECO HORARIA": "temperatura_c",
    "UMIDADE RELATIVA DO AR HORARIA": "umidade_pct",
    "VENTO VELOCIDADE HORARIA": "vento_ms",
}

DATE_PATTERNS = ("yyyy/MM/dd", "yyyy-MM-dd", "dd/MM/yyyy")


def canonical_measure(header: str) -> str | None:
    norm = normalize_name(header)
    for prefix, name in MEASURES.items():
        if norm.startswith(prefix):
            return name
    return None


def station_municipio(nome_estacao: str | None) -> str | None:
    """'SAO PAULO - MIRANTE' -> 'SAO PAULO'. O INMET usa ' - ' para
    separar o municipio do nome do posto."""
    if not nome_estacao:
        return None
    return nome_estacao.split(" - ")[0].strip()


def _decimal_br(column: str) -> F.Column:
    """Texto no formato brasileiro -> DOUBLE; vazio e -9999 -> NULL."""
    value = F.expr(f"try_cast(replace(trim({column}), ',', '.') AS DOUBLE)")
    return F.when(value == F.lit(-9999.0), F.lit(None)).otherwise(value).cast("double")


def _date(column: str) -> F.Column:
    return F.coalesce(
        *[F.to_date(F.expr(f"try_to_timestamp({column}, '{p}')")) for p in DATE_PATTERNS]
    )


def _hour(column: str) -> F.Column:
    hh = F.expr(f"try_cast(regexp_extract({column}, '^\\\\s*(\\\\d{{2}}):?\\\\d{{2}}', 1) AS INT)")
    return F.when(hh.between(0, 23), hh)


def typed(bronze: DataFrame) -> DataFrame:
    """Bronze -> colunas tipadas (sem municipio, sem dedup)."""
    keys = [r["k"] for r in bronze.select(F.explode(F.map_keys("medidas")).alias("k")).distinct().collect()]
    by_measure: dict[str, list[str]] = {}
    for key in keys:
        name = canonical_measure(key)
        if name:
            by_measure.setdefault(name, []).append(key)

    raw_measures = []
    for name in MEASURES.values():
        variants = sorted(by_measure.get(name, []))
        if variants:
            expr = F.coalesce(*[F.col("medidas").getItem(v) for v in variants])
        else:
            expr = F.lit(None).cast("string")
        raw_measures.append(expr.alias(f"{name}__raw"))

    staged = bronze.select("*", *raw_measures)
    return staged.select(
        "_source_file",
        "_ingested_at",
        "codigo_estacao",
        "nome_estacao",
        F.upper(F.trim("uf")).alias("uf"),
        _decimal_br("latitude_raw").alias("latitude"),
        _decimal_br("longitude_raw").alias("longitude"),
        "data_raw",
        "hora_raw",
        _date("data_raw").alias("data"),
        _hour("hora_raw").alias("hora_utc"),
        *[_decimal_br(f"{name}__raw").alias(name) for name in MEASURES.values()],
    )


def dedupe(df: DataFrame) -> DataFrame:
    w = Window.partitionBy("codigo_estacao", "data", "hora_utc").orderBy(
        F.col("_ingested_at").desc(), F.col("_source_file").desc()
    )
    return df.withColumn("_rn", F.row_number().over(w)).filter("_rn = 1").drop("_rn")


_STATION_SCHEMA = T.StructType(
    [
        T.StructField("codigo_estacao", T.StringType()),
        T.StructField("codigo_ibge", T.StringType()),
        T.StructField("municipio", T.StringType()),
        T.StructField("estrategia_municipio", T.StringType()),
        T.StructField("motivo", T.StringType()),
    ]
)


def resolve_stations(spark: SparkSession, df: DataFrame, resolver: MunicipioResolver) -> DataFrame:
    """Resolve no driver: sao poucas centenas de estacoes, e o resolvedor
    do projeto 13 ja e testado em Python puro."""
    out = []
    stations = df.select("codigo_estacao", "nome_estacao", "uf").distinct().collect()
    for s in stations:
        res = resolver.resolve(name=station_municipio(s["nome_estacao"]), uf=codigo_uf(s["uf"]))
        if res.resolved:
            out.append((s["codigo_estacao"], res.municipio.codigo_ibge, res.municipio.nome, res.strategy.value, None))
        else:
            motivo = "municipio_ambiguo" if res.ambiguous else "municipio_nao_encontrado"
            out.append((s["codigo_estacao"], None, None, res.strategy.value, motivo))
    return spark.createDataFrame(out, _STATION_SCHEMA)


def load_resolver(spark: SparkSession, reference_path: str) -> MunicipioResolver:
    rows = spark.read.option("header", "true").csv(reference_path).collect()
    return MunicipioResolver.from_rows(r.asDict() for r in rows)


def run(
    spark: SparkSession,
    bronze_root: str,
    silver_root: str,
    reference_path: str,
    catalog: str | None = None,
) -> dict:
    bronze = io.read_table(spark, io.table_path(bronze_root, BRONZE_TABLE))
    t = typed(bronze).cache()

    invalid = t.filter(F.col("data").isNull() | F.col("hora_utc").isNull()).withColumn(
        "motivo", F.lit("data_ou_hora_invalida")
    )
    valid = dedupe(t.filter(F.col("data").isNotNull() & F.col("hora_utc").isNotNull()))

    stations = resolve_stations(spark, valid, load_resolver(spark, reference_path))
    joined = valid.join(stations, on="codigo_estacao", how="left")

    unresolved = joined.filter(F.col("codigo_ibge").isNull())
    resolved = joined.filter(F.col("codigo_ibge").isNotNull()).drop("motivo", "data_raw", "hora_raw")

    quarantine_cols = ["_source_file", "codigo_estacao", "nome_estacao", "uf", "data_raw", "hora_raw", "motivo"]
    quarantine = invalid.select(*quarantine_cols).unionByName(unresolved.select(*quarantine_cols))

    path = io.table_path(silver_root, TABLE)
    q_path = io.table_path(silver_root, QUARANTINE_TABLE)
    io.overwrite(resolved, path)
    io.overwrite(quarantine, q_path)
    io.register_table(spark, catalog, "silver", TABLE, path)
    io.register_table(spark, catalog, "silver", QUARANTINE_TABLE, q_path)

    result = {"linhas": io.read_table(spark, path).count(), "quarentena": io.read_table(spark, q_path).count()}
    t.unpersist()
    return result
