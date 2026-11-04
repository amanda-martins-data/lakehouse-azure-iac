"""Testes sem Spark: parser da bronze, colunas canonicas e resolvedor."""

from conftest import FIXTURES

from lakehouse.bronze import parse_content
from lakehouse.municipio_resolver import MunicipioResolver
from lakehouse.silver import canonical_measure, station_municipio
from lakehouse.ufs import codigo_uf

SP_FILE = next((FIXTURES / "inmet").glob("*A701*"))


def test_parse_content_keeps_raw_values():
    parsed = parse_content(SP_FILE.read_bytes())
    assert parsed["erro"] is None
    assert parsed["codigo_estacao"] == "A701"
    assert parsed["nome_estacao"] == "SAO PAULO - MIRANTE"
    assert parsed["latitude_raw"] == "-23,49638888"
    assert len(parsed["linhas"]) == 7
    first = parsed["linhas"][0]
    assert first["data_raw"] == "2024/01/01"
    assert first["hora_raw"] == "0000 UTC"
    # bronze guarda o texto original, inclusive o sentinela
    assert parsed["linhas"][1]["medidas"]["TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)"] == "-9999"
    # a coluna fantasma criada pelo ';' final nao vira medida
    assert "" not in first["medidas"]


def test_parse_content_reports_error_instead_of_raising():
    parsed = parse_content(b"arquivo sem cabecalho\r\n")
    assert parsed["linhas"] == []
    assert "ValueError" in parsed["erro"]


def test_canonical_measure_ignores_accents_and_units():
    assert canonical_measure("PRECIPITAÇÃO TOTAL, HORÁRIO (mm)") == "precipitacao_mm"
    assert canonical_measure("PRECIPITACAO TOTAL, HORARIO (mm)") == "precipitacao_mm"
    assert canonical_measure("TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)") == "temperatura_c"
    assert canonical_measure("TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C)") is None


def test_station_name_to_municipio():
    assert station_municipio("SAO PAULO - MIRANTE") == "SAO PAULO"
    assert station_municipio("SAO GONCALO") == "SAO GONCALO"


def test_uf_guard_sends_sao_goncalo_pb_to_quarantine():
    resolver = MunicipioResolver.from_csv(FIXTURES / "municipios_ibge_amostra.csv")
    sp = resolver.resolve(name="SAO PAULO", uf=codigo_uf("SP"))
    assert sp.resolved and sp.municipio.codigo_ibge == "3550308"
    # existe Sao Goncalo no RJ, mas a estacao e da PB: nao pode resolver
    pb = resolver.resolve(name="SAO GONCALO", uf=codigo_uf("PB"))
    assert not pb.resolved
