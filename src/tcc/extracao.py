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
from tcc.fontes import anatel, cnes, ibge, inep, sidra
from tcc.fontes.download import baixar, sha256

GRUPO = "extracao"


def _sufixo(codigo_uf: int | None) -> str:
    return f"uf{codigo_uf}" if codigo_uf else "br"


def _localidades_e_uf() -> tuple[pd.DataFrame, int | None]:
    bruto = config.dir_bruto("ibge")
    loc = ibge.ler_localidades(baixar(ibge.URL_LOCALIDADES, bruto / "localidades_municipios.json"))
    sigla = config.escopo_uf()
    codigo_uf = ibge.codigo_da_uf(loc, sigla) if sigla else None
    return loc, codigo_uf


def _obter(url: str, destino, pagina: str):
    """Usa o arquivo já gravado ou baixa pelo link direto; se o download falhar,
    explica como obter o arquivo à mão."""
    try:
        return baixar(url, destino)
    except RuntimeError as erro:
        raise FileNotFoundError(
            f"Não foi possível baixar {url} ({erro}). Baixe o arquivo pelo navegador "
            f"(página: {pagina}) e grave-o em {destino}.") from erro


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


@asset(group_name=GRUPO, deps=[padronizado_dim_municipio],
       description="Inep, Indicadores Educacionais 2022: E1 e E2 -> fato_inep.csv")
def padronizado_inep(context: AssetExecutionContext) -> MaterializeResult:
    uf = config.escopo_uf()
    partes, hashes = [], {}
    for ind in inep.INDICADORES_INEP:
        destino = config.dir_bruto("inep") / f"{ind.arquivo}.zip"
        arquivo = _obter(inep.url_arquivo(ind), destino, inep.PAGINA)
        hashes[arquivo.name] = sha256(arquivo)
        partes.append(inep.calcular_indicador(ind, inep.ler_zip(arquivo), uf))
    fato = pd.concat(partes, ignore_index=True)
    contagem = fato.groupby("codigo_indicador").size().to_dict()
    context.log.info(f"Municípios por indicador: {contagem}")
    return MaterializeResult(metadata={
        "municipios_por_indicador": MetadataValue.json(contagem),
        "arquivo": _gravar(fato, "fato_inep.csv"),
        "sha256": MetadataValue.json(hashes),
    })


@asset(group_name=GRUPO, deps=[padronizado_dim_municipio],
       description="CNES, competência dez. 2022: H1 (UBS) e H2 (médicos) -> fato_cnes.csv")
def padronizado_cnes(context: AssetExecutionContext) -> MaterializeResult:
    dim = pd.read_csv(config.dir_padronizado() / "dim_municipio.csv",
                      dtype={"codigo_municipio": str})
    ubs, medicos, urls = [], [], []
    for uf in sorted(dim["uf"].unique()):
        arquivos = {}
        for grupo in ("ST", "PF"):
            url = cnes.url_arquivo(grupo, uf)
            arquivos[grupo] = baixar(url, config.dir_bruto("cnes") / cnes.nome_arquivo(grupo, uf))
            urls.append(url)
        ubs.append(cnes.contar_ubs(cnes.ler_dbc(arquivos["ST"], cnes.COLUNAS_ST)))
        medicos.append(cnes.contar_medicos(cnes.ler_dbc(arquivos["PF"], cnes.COLUNAS_PF)))
        context.log.info(f"{uf}: {int(ubs[-1].sum())} UBS, {int(medicos[-1].sum())} médicos")
    fato = cnes.calcular_indicadores(pd.concat(ubs), pd.concat(medicos), dim)
    return MaterializeResult(metadata={
        "ubs": int(sum(s.sum() for s in ubs)),
        "medicos_municipio": int(sum(s.sum() for s in medicos)),
        "arquivo": _gravar(fato, "fato_cnes.csv"),
        "fontes": MetadataValue.json(urls),
    })


@asset(group_name=GRUPO, deps=[padronizado_dim_municipio],
       description="Anatel, IBC de 2022: C1 -> fato_anatel.csv")
def padronizado_anatel(context: AssetExecutionContext) -> MaterializeResult:
    destino = config.dir_bruto("anatel") / anatel.ARQUIVO_ZIP
    caminho = _obter(anatel.URL, destino, anatel.PAGINA)
    fato = anatel.calcular_c1(anatel.ler_zip(caminho), config.escopo_uf())
    context.log.info(f"IBC 2022: {len(fato)} municípios")
    return MaterializeResult(metadata={
        "municipios": len(fato),
        "arquivo": _gravar(fato, "fato_anatel.csv"),
        "sha256": sha256(caminho),
        "fonte": MetadataValue.url(anatel.URL),
    })
