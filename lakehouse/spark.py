"""Sessao Spark e formato de tabela.

No Databricks a sessao ja existe e o formato e sempre Delta. Fora dele
(CI e maquina local) a sessao e criada aqui, com Delta via delta-spark
quando LAKEHOUSE_FORMAT=delta (padrao) ou Parquet puro quando
LAKEHOUSE_FORMAT=parquet - util onde os jars do Delta nao podem ser
baixados. O modo Parquet existe so para teste; o caminho de producao
e o Delta.
"""

from __future__ import annotations

import os

DELTA = "delta"
PARQUET = "parquet"


def on_databricks() -> bool:
    return "DATABRICKS_RUNTIME_VERSION" in os.environ


def table_format() -> str:
    if on_databricks():
        return DELTA
    fmt = os.environ.get("LAKEHOUSE_FORMAT", DELTA).strip().lower()
    if fmt not in (DELTA, PARQUET):
        raise ValueError(f"LAKEHOUSE_FORMAT invalido: {fmt!r} (use delta ou parquet)")
    return fmt


def get_spark(app_name: str = "lakehouse"):
    from pyspark.sql import SparkSession

    if on_databricks():
        return SparkSession.builder.getOrCreate()

    builder = (
        SparkSession.builder.appName(app_name)
        .master(os.environ.get("SPARK_MASTER", "local[2]"))
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.ui.enabled", "false")
    )
    if table_format() == DELTA:
        from delta import configure_spark_with_delta_pip

        builder = configure_spark_with_delta_pip(
            builder.config(
                "spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension"
            ).config(
                "spark.sql.catalog.spark_catalog",
                "org.apache.spark.sql.delta.catalog.DeltaCatalog",
            )
        )
    return builder.getOrCreate()
