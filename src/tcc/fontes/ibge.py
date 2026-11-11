"""IBGE: lista de municípios, população e indicadores do Censo 2022 (S1, S2, C2).

Tabelas do SIDRA usadas (conferidas em 11/11/2026 pela API de metadados; ver
``docs/fontes.md``):

- 4714: população residente (variável 93), Censo 2022.
- 6894: moradores em domicílios particulares permanentes ocupados, por ligação à
  rede geral de água e principal forma de abastecimento (universo).
- 7555: moradores em domicílios particulares permanentes ocupados, por tipo de
  esgotamento sanitário (universo).
- 9942: moradores em domicílios particulares permanentes ocupados, por existência
  de conexão domiciliar à Internet (amostra).

Os indicadores são calculados a partir das contagens de moradores (variável 382)
e conferidos contra o percentual publicado pelo próprio IBGE (variável 1000382).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from tcc import catalogo
from tcc.fontes import sidra

URL_LOCALIDADES = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?view=nivelado"

TABELA_POPULACAO = 4714
VARIAVEL_POPULACAO = 93

VARIAVEL_MORADORES = 382
VARIAVEL_MORADORES_PCT = 1000382

# Categorias "Total" de grupo de idade (58) e cor ou raça (86).
SEM_RECORTE = {58: [95253], 86: [95251]}

# Tolerância, em pontos percentuais, entre o valor calculado e o publicado (que
# vem arredondado com duas casas).
TOLERANCIA_PCT = 0.01


@dataclass(frozen=True)
class IndicadorCenso:
    codigo: str
    tabela: int
    classificacao: int
    categoria_total: int
    categorias_numerador: tuple[int, ...]
    fixas: dict[int, list[int]] = field(default_factory=lambda: dict(SEM_RECORTE))

    def classificacoes(self) -> dict[int, list[int]]:
        alvo = [self.categoria_total, *self.categorias_numerador]
        return {self.classificacao: alvo, **self.fixas}


INDICADORES_CENSO: tuple[IndicadorCenso, ...] = (
    # S1: 72144 = "Possui ligação à rede geral e a utiliza como forma principal".
    IndicadorCenso("S1", 6894, 1821, 72129, (72144,)),
    # S2: 46290 = "Rede geral, rede pluvial ou fossa ligada à rede".
    IndicadorCenso("S2", 7555, 11558, 46292, (46290,)),
    # C2: 77585 = "Sim" (existe conexão domiciliar à Internet).
    IndicadorCenso("C2", 9942, 2072, 77584, (77585,)),
)


class DivergenciaPublicacao(ValueError):
    """O percentual calculado não confere com o publicado pelo IBGE."""


# ---------------------------------------------------------------- URLs

def url_populacao(codigo_uf: int | None) -> str:
    return sidra.url_agregado(TABELA_POPULACAO, catalogo.ANO_REFERENCIA, [VARIAVEL_POPULACAO],
                              sidra.localidades_municipios(codigo_uf))


def url_indicador(ind: IndicadorCenso, codigo_uf: int | None) -> str:
    return sidra.url_agregado(ind.tabela, catalogo.ANO_REFERENCIA,
                              [VARIAVEL_MORADORES, VARIAVEL_MORADORES_PCT],
                              sidra.localidades_municipios(codigo_uf), ind.classificacoes())


# ---------------------------------------------------------------- conversões

def ler_localidades(conteudo: str | bytes | Path) -> pd.DataFrame:
    """Lista de municípios da API de localidades: código, nome, UF e região."""
    if isinstance(conteudo, Path):
        conteudo = conteudo.read_bytes()
    df = pd.DataFrame(json.loads(conteudo))
    return pd.DataFrame({
        "codigo_municipio": df["municipio-id"].astype(str),
        "nome": df["municipio-nome"],
        "uf": df["UF-sigla"],
        "codigo_uf": df["UF-id"].astype(int),
        "regiao": df["regiao-nome"],
    })


def codigo_da_uf(localidades: pd.DataFrame, sigla: str) -> int:
    codigos = localidades.loc[localidades["uf"] == sigla.upper(), "codigo_uf"].unique()
    if len(codigos) != 1:
        raise ValueError(f"UF desconhecida: {sigla}")
    return int(codigos[0])


def montar_dim_municipio(populacao_sidra: pd.DataFrame, localidades: pd.DataFrame) -> pd.DataFrame:
    """Dimensão de município no formato de ``data/README.md``.

    A base é a lista de municípios do Censo 2022 (tabela de população). A API de
    localidades fornece nome, UF e região; ela inclui municípios criados depois
    do Censo, que ficam de fora por não terem população em 2022.
    """
    pop = populacao_sidra.loc[populacao_sidra["variavel"] == str(VARIAVEL_POPULACAO),
                              ["codigo_localidade", "valor"]]
    pop = pop.rename(columns={"codigo_localidade": "codigo_municipio", "valor": "populacao"})
    if pop["populacao"].isna().any():
        raise ValueError("Município sem população na tabela do Censo.")
    dim = pop.merge(localidades, on="codigo_municipio", how="left", validate="one_to_one")
    sem_cadastro = dim.loc[dim["nome"].isna(), "codigo_municipio"].tolist()
    if sem_cadastro:
        raise ValueError(f"Municípios do Censo sem cadastro na API de localidades: {sem_cadastro}")
    dim["populacao"] = dim["populacao"].astype(int)
    colunas = ["codigo_municipio", "nome", "uf", "regiao", "populacao"]
    return dim[colunas].sort_values("codigo_municipio").reset_index(drop=True)


def calcular_indicador(ind: IndicadorCenso, resultado: pd.DataFrame) -> pd.DataFrame:
    """Percentual de moradores na(s) categoria(s) do numerador, por município.

    Devolve as colunas da camada padronizada. Municípios sem contagem publicada
    ficam de fora (não há imputação); o relatório de completude os mostra.
    """
    col = f"c{ind.classificacao}"
    for c, cats in ind.fixas.items():
        resultado = resultado[resultado[f"c{c}"].isin([str(x) for x in cats])]

    contagem = resultado[resultado["variavel"] == str(VARIAVEL_MORADORES)]
    largo = contagem.pivot(index="codigo_localidade", columns=col, values="valor")
    total = largo[str(ind.categoria_total)]
    numerador = largo[[str(c) for c in ind.categorias_numerador]].sum(axis=1, min_count=1)
    valor = (numerador / total * 100).where(total > 0)

    publicado = resultado[resultado["variavel"] == str(VARIAVEL_MORADORES_PCT)]
    if not publicado.empty:
        _conferir_com_publicado(ind, valor, publicado)

    valor = valor.dropna()
    return pd.DataFrame({
        "codigo_municipio": valor.index.astype(str),
        "codigo_indicador": ind.codigo,
        "ano_referencia": catalogo.ANO_REFERENCIA,
        "valor": valor.to_numpy(),
    })


def _conferir_com_publicado(ind: IndicadorCenso, calculado: pd.Series,
                            publicado: pd.DataFrame) -> None:
    """Compara o percentual calculado com o publicado (soma das categorias).

    O percentual publicado é sobre o total geral, então a soma das categorias do
    numerador deve coincidir com o cálculo, a menos do arredondamento.
    """
    col = f"c{ind.classificacao}"
    pub = publicado[publicado[col].isin([str(c) for c in ind.categorias_numerador])]
    pub = pub.groupby("codigo_localidade")["valor"].sum(min_count=1)
    comparacao = pd.concat({"calculado": calculado, "publicado": pub}, axis=1).dropna()
    tolerancia = TOLERANCIA_PCT * len(ind.categorias_numerador)
    divergentes = comparacao[(comparacao["calculado"] - comparacao["publicado"]).abs()
                             > tolerancia + 1e-9]
    if not divergentes.empty:
        raise DivergenciaPublicacao(
            f"{ind.codigo}: {len(divergentes)} município(s) divergem do percentual publicado; "
            f"exemplos: {divergentes.head().to_dict('index')}")
