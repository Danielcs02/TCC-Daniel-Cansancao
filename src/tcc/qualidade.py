"""Regras de qualidade aplicadas à tabela de fatos (seção 3.5 do artigo).

A tabela de fatos está no formato longo: uma linha por município, indicador e
ano de referência. As verificações cobrem esquema, chave, unicidade, domínio dos
valores, período de referência e completude.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
import pandera.pandas as pa

from tcc import catalogo

COLUNAS_FATO = ["codigo_municipio", "codigo_indicador", "ano_referencia", "valor"]


def _percentual_no_intervalo(df: pd.DataFrame) -> pd.Series:
    pct = df["codigo_indicador"].isin(catalogo.indicadores_percentuais())
    return ~pct | df["valor"].between(0, 100)


def schema_fato(codigos_municipio: Iterable[str]) -> pa.DataFrameSchema:
    """Esquema da tabela de fatos, já amarrado à lista oficial de municípios."""
    municipios = list(codigos_municipio)
    return pa.DataFrameSchema(
        {
            "codigo_municipio": pa.Column(
                str,
                [pa.Check.str_matches(r"^\d{7}$"), pa.Check.isin(municipios)],
                description="Código IBGE de 7 dígitos presente na dimensão de município",
            ),
            "codigo_indicador": pa.Column(str, pa.Check.isin(list(catalogo.POR_CODIGO))),
            "ano_referencia": pa.Column(int, pa.Check.eq(catalogo.ANO_REFERENCIA)),
            "valor": pa.Column(float, pa.Check.ge(0), nullable=False),
        },
        checks=[
            pa.Check(_percentual_no_intervalo, error="percentual fora do intervalo 0 a 100"),
        ],
        unique=["codigo_municipio", "codigo_indicador", "ano_referencia"],
        strict=True,
        coerce=True,
    )


def validar_fato(fato: pd.DataFrame, codigos_municipio: Iterable[str]) -> pd.DataFrame:
    """Valida a tabela de fatos e devolve todos os erros de uma vez (lazy)."""
    return schema_fato(codigos_municipio).validate(fato, lazy=True)


def relatorio_completude(fato: pd.DataFrame, codigos_municipio: Iterable[str]) -> pd.DataFrame:
    """Quantos municípios têm valor em cada indicador e quantos estão ausentes."""
    total = len(set(codigos_municipio))
    contagem = (fato.groupby("codigo_indicador")["codigo_municipio"].nunique()
                .reindex(list(catalogo.POR_CODIGO), fill_value=0))
    return pd.DataFrame({
        "municipios_com_valor": contagem,
        "municipios_ausentes": total - contagem,
        "cobertura_pct": (contagem / total * 100).round(2),
    })


def municipios_completos(largo: pd.DataFrame, codigos: Iterable[str]) -> tuple[pd.DataFrame, pd.Index]:
    """Separa os municípios com todos os indicadores do IIS dos excluídos por ausência.

    Valores ausentes não são imputados (seção 3.5): o município sem algum indicador
    fica fora do índice e é reportado.
    """
    codigos = list(codigos)
    completo = largo[codigos].notna().all(axis=1)
    return largo[completo], largo.index[~completo]
