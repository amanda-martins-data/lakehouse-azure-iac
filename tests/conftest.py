import os
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(ROOT))
# worker do Spark com o mesmo interpretador do pytest
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)


@pytest.fixture(scope="session")
def spark():
    from lakehouse.spark import get_spark

    session = get_spark("lakehouse-tests")
    yield session
    session.stop()


@pytest.fixture()
def lake(tmp_path):
    """Landing com os fixtures + raizes das tres camadas num tmp."""
    landing = tmp_path / "landing"
    shutil.copytree(FIXTURES / "inmet", landing)
    return {
        "input": str(landing),
        "reference": str(FIXTURES / "municipios_ibge_amostra.csv"),
        "bronze": str(tmp_path / "bronze"),
        "silver": str(tmp_path / "silver"),
        "gold": str(tmp_path / "gold"),
        "tmp": tmp_path,
    }
