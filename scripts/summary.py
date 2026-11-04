"""Resumo em Markdown de uma execucao local (usado no workflow de
dados reais): metricas de cada etapa, motivos de quarentena e uma
amostra da gold."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lakehouse import gold, io, silver
from lakehouse.spark import get_spark


def table_md(rows, columns) -> str:
    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    for r in rows:
        lines.append("| " + " | ".join("" if r[c] is None else str(r[c]) for c in columns) + " |")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--lake", required=True)
    p.add_argument("--metrics", required=True)
    args = p.parse_args()

    spark = get_spark("lakehouse-summary")
    print("## Execucao sobre dados reais\n")
    for line in Path(args.metrics).read_text().splitlines():
        if line.startswith("{"):
            print(f"- `{line}`")

    q = io.read_table(spark, io.table_path(f"{args.lake}/silver", silver.QUARANTINE_TABLE))
    print("\n### Quarentena por motivo\n")
    print(table_md(q.groupBy("motivo").count().orderBy("motivo").collect(), ["motivo", "count"]))

    g = io.read_table(spark, io.table_path(f"{args.lake}/gold", gold.TABLE))
    cols = ["codigo_ibge", "municipio", "data", "precipitacao_total_mm", "temperatura_media_c", "horas_observadas"]
    print("\n### Amostra da gold (10 linhas)\n")
    print(table_md(g.orderBy("codigo_ibge", "data").limit(10).collect(), cols))


if __name__ == "__main__":
    main()
