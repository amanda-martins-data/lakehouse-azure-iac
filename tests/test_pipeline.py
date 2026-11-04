"""Ponta a ponta local: bronze -> silver -> gold sobre os fixtures.

Roda em Delta (padrao, como no CI) ou em Parquet com
LAKEHOUSE_FORMAT=parquet.
"""

import shutil

import pytest
from conftest import FIXTURES

from lakehouse import bronze, gold, io, silver


def run_all(spark, lake):
    b = bronze.run(spark, lake["input"], lake["bronze"])
    s = silver.run(spark, lake["bronze"], lake["silver"], lake["reference"])
    g = gold.run(spark, lake["silver"], lake["gold"])
    return b, s, g


def read(spark, root, table):
    return io.read_table(spark, io.table_path(root, table))


def test_end_to_end_counts(spark, lake):
    b, s, g = run_all(spark, lake)
    assert b == {"arquivos_aceitos": 2, "arquivos_rejeitados": 0, "linhas": 9}
    # SP: 7 linhas - 1 duplicada - 1 hora invalida = 5
    assert s == {"linhas": 5, "quarentena": 3}
    assert g == {"linhas": 2}


def test_quarantine_reasons(spark, lake):
    run_all(spark, lake)
    q = read(spark, lake["silver"], silver.QUARANTINE_TABLE)
    counts = q.groupBy("codigo_estacao", "motivo").count().collect()
    reasons = {(r["codigo_estacao"], r["motivo"]): r["count"] for r in counts}
    assert reasons == {("A701", "data_ou_hora_invalida"): 1, ("X001", "municipio_nao_encontrado"): 2}


def test_missing_values_become_null(spark, lake):
    run_all(spark, lake)
    rows = read(spark, lake["silver"], silver.TABLE).filter("hora_utc = 1").orderBy("data").collect()
    assert rows[0]["temperatura_c"] is None  # -9999
    assert rows[1]["umidade_pct"] is None  # -9999
    two = read(spark, lake["silver"], silver.TABLE).filter("hora_utc = 2").collect()[0]
    assert two["precipitacao_mm"] is None  # vazio
    assert rows[0]["latitude"] == pytest.approx(-23.49638888)


def test_gold_daily_metrics(spark, lake):
    run_all(spark, lake)
    rows = {str(r["data"]): r for r in read(spark, lake["gold"], gold.TABLE).collect()}
    d1 = rows["2024-01-01"]
    assert d1["codigo_ibge"] == "3550308"
    assert d1["municipio"] == "São Paulo"
    assert d1["precipitacao_total_mm"] == pytest.approx(2.4)
    assert d1["temperatura_media_c"] == pytest.approx(21.3)
    assert d1["temperatura_max_c"] == pytest.approx(22.1)
    assert d1["temperatura_min_c"] == pytest.approx(20.5)
    assert d1["umidade_media_pct"] == pytest.approx(85.0)
    assert d1["horas_observadas"] == 3
    assert rows["2024-01-02"]["temperatura_media_c"] == pytest.approx(23.5)


def test_rerun_is_idempotent(spark, lake):
    first = run_all(spark, lake)
    second = run_all(spark, lake)
    assert first == second
    assert read(spark, lake["bronze"], bronze.TABLE).count() == 9
    assert read(spark, lake["gold"], gold.TABLE).count() == 2


def test_new_file_only_adds_its_rows(spark, lake):
    run_all(spark, lake)
    extra = lake["tmp"] / "landing2"
    extra.mkdir()
    src = next((FIXTURES / "inmet").glob("*A701*"))
    shutil.copy(src, extra / src.name)
    # reentrega do mesmo arquivo: substitui, nao duplica
    bronze.run(spark, str(extra), lake["bronze"])
    assert read(spark, lake["bronze"], bronze.TABLE).count() == 9


def test_corrupt_file_is_rejected_not_fatal(spark, lake):
    shutil.copy(FIXTURES / "corrompido" / "INMET_QUEBRADO.CSV", lake["input"])
    b = bronze.run(spark, lake["input"], lake["bronze"])
    assert b["arquivos_aceitos"] == 2
    assert b["arquivos_rejeitados"] == 1
    rej = read(spark, lake["bronze"], bronze.REJECTED_TABLE).collect()
    assert "ValueError" in rej[0]["erro"]
