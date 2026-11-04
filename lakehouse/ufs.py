"""Sigla da UF -> codigo numerico do IBGE.

O INMET identifica a UF pela sigla ("SP"); a tabela de municipios do
IBGE usa o codigo numerico ("35"). O resolvedor trabalha com o codigo.
"""

UF_SIGLA_PARA_CODIGO: dict[str, str] = {
    "RO": "11", "AC": "12", "AM": "13", "RR": "14", "PA": "15", "AP": "16", "TO": "17",
    "MA": "21", "PI": "22", "CE": "23", "RN": "24", "PB": "25", "PE": "26", "AL": "27",
    "SE": "28", "BA": "29",
    "MG": "31", "ES": "32", "RJ": "33", "SP": "35",
    "PR": "41", "SC": "42", "RS": "43",
    "MS": "50", "MT": "51", "GO": "52", "DF": "53",
}  # fmt: skip


def codigo_uf(sigla: str | None) -> str | None:
    if sigla is None:
        return None
    return UF_SIGLA_PARA_CODIGO.get(sigla.strip().upper())
