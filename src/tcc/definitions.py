"""Definições do Dagster: os ativos de dados do pipeline e suas dependências.

Fluxo atual (camadas padronizada e analítica):

    dim_indicador, dim_municipio -> fato_indicador_municipal
    fato_indicador_municipal -> completude
    fato_indicador_municipal -> indicadores_largo -> iis -> quadrantes
    indicadores_largo -> sensibilidade

Os ativos da camada bruta (grupo ``extracao``, em ``tcc.extracao``) baixam cada
fonte oficial e geram os arquivos de ``data/padronizado`` (formato em
``data/README.md``), que os ativos abaixo leem:

    padronizado_dim_municipio -> dim_municipio
    padronizado_censo -> fato_indicador_municipal

Execute com ``dagster dev`` na raiz do repositório.
"""

import pandas as pd
from dagster import (AssetExecutionContext, Definitions, MetadataValue, asset,
                     load_assets_from_current_module, load_assets_from_modules)

from tcc import catalogo, config, extracao, indice, municipio, qualidade

GRUPO = "tcc"


def _ler_csv(nome: str) -> pd.DataFrame:
    caminho = config.dir_padronizado() / nome
    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo {caminho} não encontrado. Veja data/README.md para o formato esperado."
        )
    return pd.read_csv(caminho, dtype={"codigo_municipio": str})


@asset(group_name=GRUPO, description="Dimensão de indicador, a partir do catálogo do Quadro 1.")
def dim_indicador() -> pd.DataFrame:
    return catalogo.como_dataframe()


@asset(group_name=GRUPO, deps=[extracao.padronizado_dim_municipio],
       description="Dimensão de município, com faixa de porte populacional.")
def dim_municipio(context: AssetExecutionContext) -> pd.DataFrame:
    df = _ler_csv("dim_municipio.csv")
    df["porte"] = municipio.faixa_porte(df["populacao"])
    context.add_output_metadata({"municipios": len(df)})
    return df


@asset(group_name=GRUPO, deps=[extracao.padronizado_censo],
       description="Tabela de fatos no formato longo, validada.")
def fato_indicador_municipal(context: AssetExecutionContext, dim_municipio: pd.DataFrame,
                             dim_indicador: pd.DataFrame) -> pd.DataFrame:
    arquivos = sorted(config.dir_padronizado().glob("fato_*.csv"))
    if not arquivos:
        raise FileNotFoundError("Nenhum arquivo fato_*.csv em data/padronizado.")
    fato = pd.concat([pd.read_csv(a, dtype={"codigo_municipio": str}) for a in arquivos],
                     ignore_index=True)
    oficiais = dim_municipio["codigo_municipio"]
    fato["codigo_municipio"] = municipio.normalizar_codigo(fato["codigo_municipio"], oficiais)
    fato = qualidade.validar_fato(fato[qualidade.COLUNAS_FATO], oficiais)
    context.add_output_metadata({
        "linhas": len(fato),
        "arquivos": MetadataValue.json([a.name for a in arquivos]),
    })
    return fato


@asset(group_name=GRUPO, description="Cobertura de municípios por indicador.")
def completude(fato_indicador_municipal: pd.DataFrame, dim_municipio: pd.DataFrame) -> pd.DataFrame:
    return qualidade.relatorio_completude(fato_indicador_municipal,
                                          dim_municipio["codigo_municipio"])


@asset(group_name=GRUPO, description="Uma linha por município e uma coluna por indicador.")
def indicadores_largo(fato_indicador_municipal: pd.DataFrame) -> pd.DataFrame:
    return fato_indicador_municipal.pivot(index="codigo_municipio",
                                          columns="codigo_indicador", values="valor")


@asset(group_name=GRUPO, description="Subíndices e Índice de Infraestrutura Social (referência).")
def iis(context: AssetExecutionContext, indicadores_largo: pd.DataFrame) -> pd.DataFrame:
    codigos = [i.codigo for i in catalogo.indicadores_do_iis()]
    completos, excluidos = qualidade.municipios_completos(indicadores_largo, codigos)
    context.add_output_metadata({
        "municipios_no_indice": len(completos),
        "municipios_excluidos": len(excluidos),
    })
    return indice.calcular_iis(completos)


@asset(group_name=GRUPO, description="Comparação da referência com os cenários alternativos.")
def sensibilidade(indicadores_largo: pd.DataFrame) -> pd.DataFrame:
    codigos = [i.codigo for i in catalogo.indicadores_do_iis()]
    completos, _ = qualidade.municipios_completos(indicadores_largo, codigos)
    return indice.analise_sensibilidade(completos)


@asset(group_name=GRUPO, description="Classificação em quadrantes para C1 (IBC) e C2 (Censo).")
def quadrantes(indicadores_largo: pd.DataFrame, iis: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        f"quadrante_{c}": indice.classificar_quadrantes(indicadores_largo[c].dropna(), iis["iis"])
        for c in ("C1", "C2")
    })


ATIVOS = [*load_assets_from_current_module(), *load_assets_from_modules([extracao])]

defs = Definitions(assets=ATIVOS)
