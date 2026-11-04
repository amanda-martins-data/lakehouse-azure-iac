"""Gold: clima diario por municipio, pronto para consumo.

A data e a do INMET, em UTC (as horas do arquivo sao UTC). A agregacao
nao inventa valor: soma e media ignoram NULL, e horas_observadas mostra
quantas horas sustentam cada numero.
"""

from __future__ import annotations

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from lakehouse import io
from lakehouse.silver import TABLE as SILVER_TABLE

TABLE = "clima_diario_municipio"
KEYS = ["codigo_ibge", "data"]


def build(silver):
    return silver.groupBy("codigo_ibge", "municipio", "uf", "data").agg(
        F.round(F.sum("precipitacao_mm"), 2).alias("precipitacao_total_mm"),
        F.round(F.avg("temperatura_c"), 2).alias("temperatura_media_c"),
        F.max("temperatura_c").alias("temperatura_max_c"),
        F.min("temperatura_c").alias("temperatura_min_c"),
        F.round(F.avg("umidade_pct"), 2).alias("umidade_media_pct"),
        F.count(F.lit(1)).alias("horas_observadas"),
        F.countDistinct("codigo_estacao").alias("estacoes"),
        F.current_timestamp().alias("_updated_at"),
    )


def run(spark: SparkSession, silver_root: str, gold_root: str, catalog: str | None = None) -> dict:
    silver = io.read_table(spark, io.table_path(silver_root, SILVER_TABLE))
    daily = build(silver)
    path = io.table_path(gold_root, TABLE)
    io.merge(spark, daily, path, KEYS)
    io.register_table(spark, catalog, "gold", TABLE, path)
    return {"linhas": io.read_table(spark, path).count()}
