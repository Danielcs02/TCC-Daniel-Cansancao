"""Acesso às tabelas do SIDRA pela API de agregados do IBGE (versão 3).

Documentação da API: https://servicodados.ibge.gov.br/api/docs/agregados?versao=3
"""

from __future__ import annotations

import json
import urllib.parse
from collections.abc import Mapping, Sequence
from pathlib import Path

import pandas as pd

URL_BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"

# Símbolos que o SIDRA usa no lugar de um número (dado inexistente, omitido
# para não identificar o informante, não aplicável etc.). Viram ausentes.
SIMBOLOS_SEM_VALOR = {"-", "..", "...", "X", "x", ""}


def localidades_municipios(codigo_uf: int | None = None) -> str:
    """Parâmetro de localidades: municípios de uma UF ou de todo o país."""
    return f"N6[N3[{codigo_uf}]]" if codigo_uf else "N6[all]"


def url_agregado(tabela: int, periodo: int, variaveis: Sequence[int], localidades: str,
                 classificacoes: Mapping[int, Sequence[int]] | None = None) -> str:
    """Monta a URL de consulta de valores de uma tabela do SIDRA."""
    caminho = (f"{URL_BASE}/{tabela}/periodos/{periodo}/variaveis/"
               + "|".join(str(v) for v in variaveis))
    params = {"localidades": localidades}
    if classificacoes:
        params["classificacao"] = "|".join(
            f"{c}[{','.join(str(x) for x in cats)}]" for c, cats in classificacoes.items())
    return (urllib.parse.quote(caminho, safe="/:")
            + "?" + urllib.parse.urlencode(params, safe="[],"))


def ler_resultado(conteudo: str | bytes | Path | list) -> pd.DataFrame:
    """Converte a resposta da API em uma tabela no formato longo.

    Colunas: ``variavel`` (código), ``codigo_localidade``, ``nome_localidade``,
    ``periodo``, uma coluna ``c<id>`` por classificação com o código da categoria,
    e ``valor`` (float; ausente quando o SIDRA publica um símbolo).
    """
    if isinstance(conteudo, Path):
        conteudo = conteudo.read_bytes()
    dados = json.loads(conteudo) if isinstance(conteudo, (str, bytes)) else conteudo

    linhas = []
    for variavel in dados:
        for resultado in variavel["resultados"]:
            categorias = {}
            for c in resultado["classificacoes"]:
                (codigo_categoria,) = c["categoria"].keys()
                categorias[f"c{c['id']}"] = codigo_categoria
            for serie in resultado["series"]:
                for periodo, valor in serie["serie"].items():
                    linhas.append({
                        "variavel": variavel["id"],
                        "codigo_localidade": serie["localidade"]["id"],
                        "nome_localidade": serie["localidade"]["nome"],
                        "periodo": int(periodo),
                        **categorias,
                        "valor": _numero(valor),
                    })
    return pd.DataFrame(linhas)


def _numero(valor: str | None) -> float:
    if valor is None or valor.strip() in SIMBOLOS_SEM_VALOR:
        return float("nan")
    return float(valor)
