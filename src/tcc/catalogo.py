"""Catálogo dos indicadores usados no trabalho (Quadro 1 do artigo).

Este módulo é a fonte única de verdade sobre cada indicador: código, dimensão,
fonte, período de referência e sentido. O pipeline, as regras de qualidade e o
cálculo do índice leem daqui, para que nenhuma definição fique duplicada.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

ANO_REFERENCIA = 2022

# Dimensões que compõem o Índice de Infraestrutura Social (IIS).
DIMENSOES_IIS = ("saneamento", "saude", "educacao")


@dataclass(frozen=True)
class Indicador:
    codigo: str
    nome: str
    dimensao: str
    fonte: str
    referencia: str
    unidade: str
    sentido: int  # +1 quanto maior, melhor; -1 quanto menor, melhor
    no_iis: bool  # True se entra no índice de infraestrutura social

    def __post_init__(self) -> None:
        if self.sentido not in (1, -1):
            raise ValueError(f"{self.codigo}: sentido deve ser 1 ou -1")


INDICADORES: tuple[Indicador, ...] = (
    Indicador("C1", "Índice Brasileiro de Conectividade (IBC)", "conectividade",
              "Anatel", "edição 2022", "pontos (0 a 100)", 1, False),
    Indicador("C2", "Moradores em domicílios com acesso à Internet", "conectividade",
              "IBGE, Censo 2022 (amostra)", "2022", "%", 1, False),
    Indicador("S1", "Moradores em domicílios abastecidos por rede geral de água", "saneamento",
              "IBGE, Censo 2022 (universo)", "2022", "%", 1, True),
    Indicador("S2", "Moradores em domicílios com esgotamento por rede geral, pluvial ou "
                    "fossa séptica ligada à rede", "saneamento",
              "IBGE, Censo 2022 (universo)", "2022", "%", 1, True),
    Indicador("H1", "Unidades básicas de saúde por 10 mil habitantes", "saude",
              "CNES", "dez. 2022", "por 10 mil hab.", 1, True),
    Indicador("H2", "Médicos com vínculo ativo por mil habitantes", "saude",
              "CNES", "dez. 2022", "por mil hab.", 1, True),
    Indicador("E1", "Taxa de distorção idade-série no ensino fundamental", "educacao",
              "Inep, Indicadores Educacionais", "2022", "%", -1, True),
    Indicador("E2", "Docentes do ensino fundamental com formação adequada", "educacao",
              "Inep, Indicadores Educacionais", "2022", "%", 1, True),
)

POR_CODIGO: dict[str, Indicador] = {i.codigo: i for i in INDICADORES}

# Indicadores calculados por habitante, que recebem winsorização antes da
# normalização (valores extremos em municípios de população muito pequena).
POR_HABITANTE = ("H1", "H2")


def indicadores_do_iis() -> list[Indicador]:
    return [i for i in INDICADORES if i.no_iis]


def indicadores_percentuais() -> list[str]:
    return [i.codigo for i in INDICADORES if i.unidade == "%"]


def como_dataframe() -> pd.DataFrame:
    """Catálogo em formato tabular, usado para carregar a dimensão de indicador."""
    return pd.DataFrame([i.__dict__ for i in INDICADORES])
