"""Etapa bronze: CSVs do INMET -> bronze.inmet_horario."""

import os
import sys

# No Databricks (git_source) e localmente, o pacote lakehouse/ fica na
# raiz do repositorio, um nivel acima deste arquivo.
try:
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:  # __file__ nem sempre existe em spark_python_task
    _ROOT = os.getcwd()
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from lakehouse import bronze
from lakehouse.cli import parse_args, report
from lakehouse.spark import get_spark


def main(argv=None) -> None:
    args = parse_args(argv)
    spark = get_spark("lakehouse-bronze")
    report("bronze", bronze.run(spark, args.input, args.bronze_root, args.catalog))


if __name__ == "__main__":
    main()
