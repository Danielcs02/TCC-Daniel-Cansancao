"""Inep, Indicadores Educacionais 2022: E1 (distorção idade-série) e E2 (formação docente).

Arquivos usados (planilhas municipais do Inep, uma linha por município,
localização e dependência administrativa):

- ``TDI_2022_MUNICIPIOS.zip``: taxa de distorção idade-série. E1 é a coluna
  ``FUN_CAT_0`` (ensino fundamental, total).
- ``AFD_2022_MUNICIPIOS.zip``: adequação da formação docente. E2 é a coluna
  ``FUN_CAT_1`` (ensino fundamental, total, grupo 1). Pela nota da própria
  planilha, o grupo 1 reúne docentes com licenciatura (ou bacharelado com
  complementação pedagógica) na mesma área da disciplina que lecionam, e o
  percentual é de docências (o docente conta uma vez por turma e disciplina).

Nos dois casos usa-se a linha com localização "Total" e dependência "Total".
Os arquivos ficam em ``data/bruto/inep/``: o pipeline tenta baixá-los pelo link
direto e, se o servidor do Inep não responder, eles podem ser baixados à mão
(ver ``docs/fontes.md``). A integridade é conferida pelo MD5 que o próprio Inep
inclui no arquivo compactado.
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from tcc import catalogo

PAGINA = ("https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/"
          "indicadores-educacionais")
URL_BASE = "https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2022"

SEM_VALOR = {"--", "-", ""}


@dataclass(frozen=True)
class IndicadorInep:
    codigo: str
    arquivo: str  # nome do .zip, sem extensão
    coluna: str


INDICADORES_INEP: tuple[IndicadorInep, ...] = (
    IndicadorInep("E1", "TDI_2022_MUNICIPIOS", "FUN_CAT_0"),
    IndicadorInep("E2", "AFD_2022_MUNICIPIOS", "FUN_CAT_1"),
)


def url_arquivo(ind: IndicadorInep) -> str:
    """Link direto do .zip (registrado a partir do download feito no navegador)."""
    return f"{URL_BASE}/{ind.arquivo}.zip"


class ArquivoCorrompido(ValueError):
    """O MD5 da planilha não confere com o informado pelo Inep."""


def ler_zip(caminho: Path) -> pd.DataFrame:
    """Lê a planilha .xlsx de dentro do .zip do Inep, conferindo o MD5."""
    with zipfile.ZipFile(caminho) as z:
        nomes = z.namelist()
        xlsx = _unico(nomes, ".xlsx", caminho)
        conteudo = z.read(xlsx)
        md5 = [n for n in nomes if Path(n).name.upper().startswith("MD5")]
        if md5:
            esperado = z.read(md5[0]).decode("latin-1")
            if hashlib.md5(conteudo).hexdigest() not in esperado:
                raise ArquivoCorrompido(f"MD5 de {xlsx} não confere com {md5[0]}")
    return ler_planilha(conteudo)


def _unico(nomes: list[str], extensao: str, caminho: Path) -> str:
    achados = [n for n in nomes if n.lower().endswith(extensao)]
    if len(achados) != 1:
        raise ValueError(f"{caminho}: esperado um arquivo {extensao}, achados {achados}")
    return achados[0]


def ler_planilha(conteudo: bytes) -> pd.DataFrame:
    """Converte a planilha do Inep em tabela, usando a linha de nomes técnicos
    (``NU_ANO_CENSO``, ``CO_MUNICIPIO``...) como cabeçalho e descartando títulos
    e notas de rodapé."""
    bruto = pd.read_excel(io.BytesIO(conteudo), header=None, dtype=str)
    linha = bruto.index[bruto.eq("CO_MUNICIPIO").any(axis=1)]
    if len(linha) != 1:
        raise ValueError("Cabeçalho com CO_MUNICIPIO não encontrado na planilha do Inep.")
    df = bruto.iloc[linha[0] + 1:].copy()
    df.columns = bruto.iloc[linha[0]]
    df = df.loc[:, df.columns.notna()]
    df["CO_MUNICIPIO"] = df["CO_MUNICIPIO"].str.strip()
    return df[df["CO_MUNICIPIO"].str.fullmatch(r"\d{7}").fillna(False)].reset_index(drop=True)


def calcular_indicador(ind: IndicadorInep, planilha: pd.DataFrame,
                       uf: str | None = None) -> pd.DataFrame:
    """Valor do indicador por município, no formato da camada padronizada.

    Municípios sem valor publicado (``--``) ficam de fora, sem imputação.
    """
    df = planilha[(planilha["NO_CATEGORIA"] == "Total") & (planilha["NO_DEPENDENCIA"] == "Total")]
    anos = set(df["NU_ANO_CENSO"].astype(int))
    if anos != {catalogo.ANO_REFERENCIA}:
        raise ValueError(f"{ind.codigo}: ano do Censo Escolar inesperado: {sorted(anos)}")
    if uf:
        df = df[df["SG_UF"] == uf.upper()]
    if df["CO_MUNICIPIO"].duplicated().any():
        raise ValueError(f"{ind.codigo}: mais de uma linha Total/Total por município.")
    valor = df[ind.coluna].str.strip()
    valor = pd.to_numeric(valor.where(~valor.isin(SEM_VALOR)), errors="raise")
    out = pd.DataFrame({
        "codigo_municipio": df["CO_MUNICIPIO"].to_numpy(),
        "codigo_indicador": ind.codigo,
        "ano_referencia": catalogo.ANO_REFERENCIA,
        "valor": valor.to_numpy(dtype=float),
    })
    return out.dropna(subset=["valor"]).reset_index(drop=True)
