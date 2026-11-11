"""Ativos da camada bruta: baixam as fontes oficiais e geram a camada padronizada.

Cada ativo grava os arquivos originais em ``data/bruto/<fonte>/`` e o CSV
padronizado em ``data/padronizado/`` (formato em ``data/README.md``). O escopo
geográfico vem de ``TCC_UF`` (padrão RJ; ``BR`` para o país inteiro).
"""

# Sem "from __future__ import annotations": o Dagster precisa ler a anotação de
# ``context`` como classe, não como texto.
import pandas as pd
from dagster import AssetExecutionContext, MaterializeResult, MetadataValue, asset

from tcc import config
from tcc.fontes import ibge, sidra
from tcc.fontes.download import baixar

GRUPO = "extracao"


def _sufixo(codigo_uf: int | None) -> str:
    return f"uf{codigo_uf}" if codigo_uf else "br"


def _localidades_e_uf() -> tuple[pd.DataFrame, int | None]:
    bruto = config.dir_bruto("ibge")
    loc = ibge.ler_localidades(baixar(ibge.URL_LOCALIDADES, bruto / "localidades_municipios.json"))
    sigla = config.escopo_uf()
    codigo_uf = ibge.codigo_da_uf(loc, sigla) if sigla else None
    return loc, codigo_uf


def _gravar(df: pd.DataFrame, nome: str) -> str:
    destino = config.dir_padronizado() / nome
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(destino, index=False)
    return str(destino)


@asset(group_name=GRUPO,
       description="Lista de municípios e população do Censo 2022 (IBGE) -> dim_municipio.csv")
def padronizado_dim_municipio(context: AssetExecutionContext) -> MaterializeResult:
    loc, codigo_uf = _localidades_e_uf()
    url = ibge.url_populacao(codigo_uf)
    arquivo = baixar(url, config.dir_bruto("ibge")
                     / f"sidra_{ibge.TABELA_POPULACAO}_{_sufixo(codigo_uf)}.json")
    dim = ibge.montar_dim_municipio(sidra.ler_resultado(arquivo), loc)
    context.log.info(f"{len(dim)} municípios, população total {dim['populacao'].sum():,}")
    return MaterializeResult(metadata={
        "municipios": len(dim),
        "populacao_total": int(dim["populacao"].sum()),
        "arquivo": _gravar(dim, "dim_municipio.csv"),
        "fonte": MetadataValue.url(url),
    })


@asset(group_name=GRUPO, deps=[padronizado_dim_municipio],
       description="Censo 2022: S1 e S2 (universo) e C2 (amostra), via SIDRA -> fato_censo.csv")
def padronizado_censo(context: AssetExecutionContext) -> MaterializeResult:
    _, codigo_uf = _localidades_e_uf()
    partes, urls = [], {}
    for ind in ibge.INDICADORES_CENSO:
        url = ibge.url_indicador(ind, codigo_uf)
        arquivo = baixar(url, config.dir_bruto("ibge") / f"sidra_{ind.tabela}_{_sufixo(codigo_uf)}.json")
        partes.append(ibge.calcular_indicador(ind, sidra.ler_resultado(arquivo)))
        urls[ind.codigo] = url
    fato = pd.concat(partes, ignore_index=True)
    contagem = fato.groupby("codigo_indicador").size().to_dict()
    context.log.info(f"Municípios por indicador: {contagem}")
    return MaterializeResult(metadata={
        "municipios_por_indicador": MetadataValue.json(contagem),
        "arquivo": _gravar(fato, "fato_censo.csv"),
        "fontes": MetadataValue.json(urls),
    })
