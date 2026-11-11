"""Anatel, Índice Brasileiro de Conectividade (IBC): C1.

Arquivo usado: o .zip do conjunto "Meu Município: Índice Brasileiro de
Conectividade" do Portal Brasileiro de Dados Abertos, gravado em
``data/bruto/anatel/ibc.zip`` (link direto em ``URL``; ver ``docs/fontes.md``).
A Anatel substitui esse arquivo a cada edição; o arquivo já gravado não é
baixado de novo, e o SHA-256 da versão usada fica registrado. Ele traz a
série 2021 a 2025 por município, em ``IBC_municipios_indicadores_normalizados.csv``
(separador ponto e vírgula, vírgula decimal, UTF-8 com BOM).

C1 é a coluna ``IBC`` do ano 2022. Os anos de 2021 a 2023 seguem a metodologia
original do índice (normalização pelo mínimo e máximo do próprio ano, sem o
componente de conectividade rural); a revisão metodológica vale a partir de 2024.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

from tcc import catalogo

PAGINA = ("https://dados.gov.br/dados/conjuntos-dados/"
          "meu-municipio---indice-brasileiro-de-conectividade")
URL = "https://www.anatel.gov.br/dadosabertos/paineis_de_dados/meu_municipio/ibc.zip"
ARQUIVO_ZIP = "ibc.zip"
ARQUIVO_CSV = "IBC_municipios_indicadores_normalizados.csv"

COL_ANO, COL_CODIGO, COL_UF, COL_IBC = "Ano", "Código Município", "UF", "IBC"


def ler_zip(caminho: Path) -> pd.DataFrame:
    """Lê a tabela municipal do IBC de dentro do .zip da Anatel."""
    with zipfile.ZipFile(caminho) as z:
        if ARQUIVO_CSV not in z.namelist():
            raise ValueError(f"{caminho}: {ARQUIVO_CSV} não encontrado; há {z.namelist()}")
        conteudo = z.read(ARQUIVO_CSV)
    return ler_csv(conteudo)


def ler_csv(conteudo: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(conteudo), sep=";", decimal=",", encoding="utf-8-sig",
                     dtype={COL_CODIGO: str})
    faltando = {COL_ANO, COL_CODIGO, COL_UF, COL_IBC} - set(df.columns)
    if faltando:
        raise ValueError(f"Colunas ausentes no arquivo do IBC: {sorted(faltando)}")
    return df


def calcular_c1(ibc: pd.DataFrame, uf: str | None = None) -> pd.DataFrame:
    """IBC de 2022 por município, no formato da camada padronizada."""
    df = ibc[ibc[COL_ANO] == catalogo.ANO_REFERENCIA]
    if df.empty:
        raise ValueError(f"O arquivo do IBC não tem o ano {catalogo.ANO_REFERENCIA}.")
    if uf:
        df = df[df[COL_UF] == uf.upper()]
    codigo = df[COL_CODIGO].str.strip()
    if codigo.duplicated().any():
        raise ValueError("IBC: município repetido no mesmo ano.")
    out = pd.DataFrame({
        "codigo_municipio": codigo.to_numpy(),
        "codigo_indicador": "C1",
        "ano_referencia": catalogo.ANO_REFERENCIA,
        "valor": pd.to_numeric(df[COL_IBC]).to_numpy(dtype=float),
    })
    if not out["valor"].dropna().between(0, 100).all():
        raise ValueError("IBC fora da escala de 0 a 100.")
    return out.dropna(subset=["valor"]).reset_index(drop=True)
