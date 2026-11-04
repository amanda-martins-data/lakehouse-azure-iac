"""Baixa uma amostra real: o zip anual do INMET (so as estacoes pedidas)
e a tabela de municipios do IBGE.

Uso: python scripts/fetch_sample.py --year 2024 --stations A701,A652 --out data/raw
"""

from __future__ import annotations

import argparse
import io
import urllib.request
import zipfile
from pathlib import Path

INMET_URL = "https://portal.inmet.gov.br/uploads/dadoshistoricos/{year}.zip"
# Tabela de municipios com codigo IBGE e codigo numerico da UF.
IBGE_URL = "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv"


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "lakehouse-azure-iac"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.read()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", default="2024")
    p.add_argument("--stations", default="A701")
    p.add_argument("--out", default="data/raw")
    args = p.parse_args()

    out = Path(args.out)
    (out / "inmet").mkdir(parents=True, exist_ok=True)
    codes = {c.strip().upper() for c in args.stations.split(",") if c.strip()}

    archive = zipfile.ZipFile(io.BytesIO(download(INMET_URL.format(year=args.year))))
    found = set()
    for info in archive.infolist():
        name = Path(info.filename).name
        parts = name.upper().split("_")
        code = parts[3] if len(parts) > 3 else ""
        if code in codes and name.upper().endswith(".CSV"):
            (out / "inmet" / name).write_bytes(archive.read(info))
            found.add(code)
            print(f"INMET: {name}")

    missing = codes - found
    if missing:
        print(f"aviso: estacoes sem arquivo em {args.year}: {sorted(missing)}")
    if not found:
        raise SystemExit("nenhuma estacao encontrada no zip do INMET")

    (out / "municipios.csv").write_bytes(download(IBGE_URL))
    print("IBGE: municipios.csv")


if __name__ == "__main__":
    main()
