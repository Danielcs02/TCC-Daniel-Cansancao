"""CNES (DATASUS), competência dezembro de 2022: H1 (UBS) e H2 (médicos).

Arquivos usados, do FTP do DATASUS (formato .dbc, um por UF e competência):

- ``ST<UF>2212.dbc``: estabelecimentos. H1 conta os estabelecimentos com
  ``TP_UNID`` 01 (posto de saúde) ou 02 (centro de saúde/unidade básica),
  conforme a tabela ``TP_ESTAB.CNV`` do próprio DATASUS.
- ``PF<UF>2212.dbc``: profissionais, um registro por vínculo. H2 conta os
  profissionais distintos (pelo Cartão Nacional de Saúde) com CBO de médico em
  estabelecimentos do município; quem atua em dois municípios conta nos dois.

CBO de médico: começa com 225 (subgrupo "Médicos" da CBO 2002) ou 2231 (códigos
anteriores ainda usados no SUS). Essa regra contém todos os códigos do
agrupamento "Médicos" do TabNet (``medico02.CNV``) e acrescenta códigos mais
novos da CBO que a tabela do TabNet não lista (ver ``docs/fontes.md``).

O CNES identifica o município com 6 dígitos (``CODUFMUN``); a conversão para 7
dígitos usa ``tcc.municipio.normalizar_codigo``.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

from tcc import catalogo, municipio

FTP_BASE = "ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados"
COMPETENCIA = "202212"

TIPOS_UBS = ("01", "02")
PREFIXOS_CBO_MEDICO = ("225", "2231")

COLUNAS_ST = ["CNES", "CODUFMUN", "TP_UNID", "COMPETEN"]
COLUNAS_PF = ["CNES", "CODUFMUN", "CBO", "CNS_PROF", "CPF_PROF", "COMPETEN"]


def url_arquivo(grupo: str, uf: str) -> str:
    """URL do arquivo do grupo (ST ou PF) para a UF, na competência de dez. 2022."""
    return f"{FTP_BASE}/{grupo}/{nome_arquivo(grupo, uf)}"


def nome_arquivo(grupo: str, uf: str) -> str:
    return f"{grupo}{uf.upper()}{COMPETENCIA[2:]}.dbc"


def ler_dbc(caminho: Path, colunas: list[str]) -> pd.DataFrame:
    """Lê um .dbc do DATASUS (DBF compactado), só com as colunas pedidas."""
    from dbfread import DBF
    from pyreaddbc import dbc2dbf

    with tempfile.TemporaryDirectory() as tmp:
        dbf = Path(tmp) / (Path(caminho).stem + ".dbf")
        dbc2dbf(str(caminho), str(dbf))
        tabela = DBF(dbf, encoding="latin-1", char_decode_errors="replace")
        faltando = set(colunas) - set(tabela.field_names)
        if faltando:
            raise ValueError(f"{caminho}: colunas ausentes {sorted(faltando)}")
        linhas = ({c: r[c] for c in colunas} for r in tabela)
        return pd.DataFrame(linhas, columns=colunas).astype("string")


def _conferir_competencia(df: pd.DataFrame, nome: str) -> None:
    competencias = set(df["COMPETEN"].dropna().str.strip())
    if competencias != {COMPETENCIA}:
        raise ValueError(f"{nome}: competência inesperada {sorted(competencias)}")


def contar_ubs(st: pd.DataFrame) -> pd.Series:
    """Número de UBS por município (código de 6 dígitos)."""
    _conferir_competencia(st, "ST")
    if st["CNES"].duplicated().any():
        raise ValueError("ST: estabelecimento repetido na mesma competência.")
    ubs = st[st["TP_UNID"].str.strip().isin(TIPOS_UBS)]
    return ubs.groupby(ubs["CODUFMUN"].str.strip()).size()


def contar_medicos(pf: pd.DataFrame) -> pd.Series:
    """Número de médicos distintos por município (código de 6 dígitos).

    O profissional é identificado pelo CNS; na falta dele, pelo CPF (que o
    DATASUS publica codificado, mas de forma consistente dentro do arquivo).
    """
    _conferir_competencia(pf, "PF")
    medico = pf[pf["CBO"].str.strip().str.startswith(PREFIXOS_CBO_MEDICO)]
    cns = medico["CNS_PROF"].str.strip()
    pessoa = ("CNS:" + cns).where(cns.fillna("") != "", "CPF:" + medico["CPF_PROF"])
    return pessoa.groupby(medico["CODUFMUN"].str.strip()).nunique()


def calcular_indicadores(ubs: pd.Series, medicos: pd.Series,
                         dim_municipio: pd.DataFrame) -> pd.DataFrame:
    """H1 (UBS por 10 mil hab.) e H2 (médicos por mil hab.), na camada padronizada.

    ``dim_municipio`` define os municípios do escopo e a população (Censo 2022).
    Município do escopo sem nenhum registro no arquivo recebe contagem zero: o
    CNES lista todos os estabelecimentos cadastrados, então ausência de registro
    significa ausência de UBS ou de médico, e não dado faltante.
    """
    oficiais = dim_municipio["codigo_municipio"].astype(str)
    contagens = {}
    for nome, serie in (("ubs", ubs), ("medicos", medicos)):
        codigos = municipio.normalizar_codigo(pd.Series(serie.index), oficiais, estrito=True)
        contagens[nome] = pd.Series(serie.to_numpy(), index=codigos.to_numpy()).groupby(level=0).sum()

    pop = dim_municipio.set_index(oficiais)["populacao"].astype(float)
    if (pop <= 0).any():
        raise ValueError("População nula ou negativa na dimensão de município.")
    n_ubs = contagens["ubs"].reindex(pop.index, fill_value=0)
    n_med = contagens["medicos"].reindex(pop.index, fill_value=0)

    partes = []
    for codigo, valor in (("H1", n_ubs / pop * 10_000), ("H2", n_med / pop * 1_000)):
        partes.append(pd.DataFrame({
            "codigo_municipio": pop.index,
            "codigo_indicador": codigo,
            "ano_referencia": catalogo.ANO_REFERENCIA,
            "valor": valor.to_numpy(),
        }))
    return pd.concat(partes, ignore_index=True)
