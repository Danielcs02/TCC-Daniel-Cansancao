"""Construção do Índice de Infraestrutura Social (IIS) e análise de sensibilidade.

Implementa a seção 3.6 do artigo:

* winsorização dos indicadores por habitante (percentis 1 e 99);
* normalização mín-máx, com inversão dos indicadores de sentido negativo;
* subíndice de cada dimensão pela média aritmética dos seus indicadores;
* IIS pela média dos subíndices com pesos iguais (configuração de referência);
* cenários alternativos: agregação geométrica, pesos por componentes principais
  e exclusão de um indicador por vez, comparados à referência pela correlação de
  Spearman e pelo deslocamento médio de posições.

Todas as funções recebem um DataFrame "largo": uma linha por município (índice
igual ao código IBGE) e uma coluna por código de indicador.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from tcc import catalogo


# ----------------------------------------------------------------- tratamento

def winsorizar(s: pd.Series, inferior: float = 0.01, superior: float = 0.99) -> pd.Series:
    """Limita os valores aos percentis informados."""
    lo, hi = s.quantile([inferior, superior])
    return s.clip(lower=lo, upper=hi)


def normalizar_minmax(s: pd.Series, sentido: int = 1) -> pd.Series:
    """Leva os valores ao intervalo [0, 1]. Com sentido -1, 1 passa a ser o melhor valor."""
    lo, hi = s.min(), s.max()
    if pd.isna(lo) or hi == lo:
        raise ValueError(f"Indicador {s.name!r} sem variação: não é possível normalizar.")
    z = (s - lo) / (hi - lo)
    return z if sentido == 1 else 1 - z


def normalizar(df: pd.DataFrame, codigos: Sequence[str] | None = None,
               winsorizar_por_habitante: bool = True) -> pd.DataFrame:
    """Aplica winsorização (quando cabível) e normalização mín-máx às colunas indicadas."""
    codigos = list(codigos or [i.codigo for i in catalogo.indicadores_do_iis()])
    out = {}
    for c in codigos:
        s = df[c].astype(float)
        if winsorizar_por_habitante and c in catalogo.POR_HABITANTE:
            s = winsorizar(s)
        out[c] = normalizar_minmax(s, catalogo.POR_CODIGO[c].sentido)
    return pd.DataFrame(out, index=df.index)


# ----------------------------------------------------------------- agregação

def subindices(normalizado: pd.DataFrame,
               excluir: Sequence[str] = ()) -> pd.DataFrame:
    """Média aritmética dos indicadores normalizados de cada dimensão do IIS."""
    out = {}
    for dim in catalogo.DIMENSOES_IIS:
        cols = [i.codigo for i in catalogo.indicadores_do_iis()
                if i.dimensao == dim and i.codigo not in excluir]
        if not cols:
            raise ValueError(f"Dimensão {dim!r} ficou sem indicadores.")
        out[dim] = normalizado[cols].mean(axis=1)
    return pd.DataFrame(out, index=normalizado.index)


def agregar(sub: pd.DataFrame, pesos: Mapping[str, float] | None = None,
            metodo: str = "aritmetica", piso: float = 0.01) -> pd.Series:
    """Agrega os subíndices em um único valor por município.

    Args:
        sub: subíndices, uma coluna por dimensão.
        pesos: peso de cada dimensão; se None, pesos iguais.
        metodo: "aritmetica" (compensação total) ou "geometrica" (compensação parcial).
        piso: na agregação geométrica, os subíndices são reescalados para
            [piso, 1] para que um único zero não anule o índice do município.
    """
    w = pd.Series(pesos if pesos is not None else {c: 1.0 for c in sub.columns}, dtype=float)
    w = w.reindex(sub.columns)
    if w.isna().any() or (w < 0).any():
        raise ValueError("Pesos ausentes ou negativos.")
    w = w / w.sum()

    if metodo == "aritmetica":
        return (sub * w).sum(axis=1).rename("iis")
    if metodo == "geometrica":
        x = piso + (1 - piso) * sub
        return np.exp((np.log(x) * w).sum(axis=1)).rename("iis")
    raise ValueError(f"Método de agregação desconhecido: {metodo!r}")


def pesos_pca(sub: pd.DataFrame) -> dict[str, float]:
    """Pesos proporcionais às cargas do primeiro componente principal.

    Usa a matriz de correlação dos subíndices; as cargas são tomadas em valor
    absoluto e normalizadas para somar 1.
    """
    corr = np.corrcoef(sub.to_numpy(), rowvar=False)
    autovalores, autovetores = np.linalg.eigh(corr)
    carga = np.abs(autovetores[:, np.argmax(autovalores)])
    return dict(zip(sub.columns, carga / carga.sum()))


def calcular_iis(df: pd.DataFrame) -> pd.DataFrame:
    """Configuração de referência: subíndices e IIS com pesos iguais."""
    sub = subindices(normalizar(df))
    return sub.assign(iis=agregar(sub))


# ----------------------------------------------------------------- sensibilidade

def comparar_rankings(referencia: pd.Series, alternativo: pd.Series) -> dict[str, float]:
    """Correlação de Spearman e deslocamento médio de posições entre dois índices."""
    a, b = referencia.align(alternativo, join="inner")
    rho = spearmanr(a, b).statistic
    deslocamento = (a.rank(ascending=False) - b.rank(ascending=False)).abs().mean()
    return {"spearman": float(rho), "deslocamento_medio": float(deslocamento)}


def analise_sensibilidade(df: pd.DataFrame) -> pd.DataFrame:
    """Compara a configuração de referência com os cenários alternativos do artigo."""
    norm = normalizar(df)
    sub = subindices(norm)
    referencia = agregar(sub)

    cenarios = {
        "agregacao_geometrica": agregar(sub, metodo="geometrica"),
        "pesos_pca": agregar(sub, pesos=pesos_pca(sub)),
    }
    for ind in catalogo.indicadores_do_iis():
        cenarios[f"sem_{ind.codigo}"] = agregar(subindices(norm, excluir=[ind.codigo]))

    linhas = [{"cenario": nome, **comparar_rankings(referencia, alt)}
              for nome, alt in cenarios.items()]
    return pd.DataFrame(linhas).set_index("cenario")


# ----------------------------------------------------------------- quadrantes

QUADRANTES = {
    (True, True): "alta conectividade, alta infraestrutura social",
    (True, False): "alta conectividade, baixa infraestrutura social",
    (False, True): "baixa conectividade, alta infraestrutura social",
    (False, False): "baixa conectividade, baixa infraestrutura social",
}


def classificar_quadrantes(conectividade: pd.Series, iis: pd.Series) -> pd.Series:
    """Classifica cada município pelas medianas nacionais de conectividade e de IIS."""
    c, i = conectividade.align(iis, join="inner")
    alta_c = c > c.median()
    alta_i = i > i.median()
    return pd.Series([QUADRANTES[(bool(x), bool(y))] for x, y in zip(alta_c, alta_i)],
                     index=c.index, name="quadrante")
