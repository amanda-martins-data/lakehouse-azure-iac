"""Argumentos comuns aos tres jobs.

Os tres recebem a mesma lista de parametros (e assim que o job do
Databricks os chama, ver infra/envs/dev/catalog/jobs.tf); cada um usa
so o que precisa. Localmente, --lake <pasta> define as tres raizes.
"""

from __future__ import annotations

import argparse
import json


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="lakehouse INMET/IBGE")
    p.add_argument("--input", help="pasta com os CSVs do INMET (landing)")
    p.add_argument("--reference", help="CSV de municipios do IBGE")
    p.add_argument("--lake", help="raiz local; define bronze/, silver/ e gold/ dentro dela")
    p.add_argument("--bronze-root")
    p.add_argument("--silver-root")
    p.add_argument("--gold-root")
    p.add_argument("--catalog", help="catalogo do Unity Catalog para registrar as tabelas")
    args = p.parse_args(argv)

    for layer in ("bronze", "silver", "gold"):
        attr = f"{layer}_root"
        if getattr(args, attr) is None:
            if args.lake is None:
                p.error(f"informe --{layer}-root ou --lake")
            setattr(args, attr, f"{args.lake.rstrip('/')}/{layer}")
    return args


def report(step: str, result: dict) -> None:
    print(json.dumps({"etapa": step, **result}, ensure_ascii=False))
