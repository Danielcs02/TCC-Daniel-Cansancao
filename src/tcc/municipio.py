"""Padronização da chave municipal.

O IBGE identifica municípios com sete dígitos (os seis primeiros mais um dígito
verificador). Os sistemas do DATASUS, como o CNES, usam apenas os seis primeiros.
Como o prefixo de seis dígitos é único entre os municípios, a conversão é feita
por correspondência com a lista oficial, sem recalcular o dígito verificador
(há municípios cujo código não segue a regra usual do dígito).
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

FAIXAS_PORTE = (
    (0, 20_000, "até 20 mil"),
    (20_000, 100_000, "20 mil a 100 mil"),
    (100_000, 500_000, "100 mil a 500 mil"),
    (500_000, float("inf"), "acima de 500 mil"),
)


class CodigoMunicipioInvalido(ValueError):
    """Há códigos que não correspondem a nenhum município da lista oficial."""

    def __init__(self, codigos: list[str]):
        self.codigos = codigos
        amostra = ", ".join(codigos[:10])
        super().__init__(f"{len(codigos)} código(s) sem correspondência: {amostra}")


def _limpar(codigos: pd.Series) -> pd.Series:
    s = codigos.astype("string").str.strip()
    s = s.str.replace(r"\.0$", "", regex=True)  # códigos lidos como float pelo pandas
    return s


def normalizar_codigo(codigos: pd.Series, codigos_oficiais: Iterable[str],
                      estrito: bool = True) -> pd.Series:
    """Converte códigos de 6 ou 7 dígitos para o código IBGE de 7 dígitos.

    Args:
        codigos: códigos como vieram da fonte (texto ou número).
        codigos_oficiais: códigos de 7 dígitos da dimensão de município.
        estrito: se True, levanta erro quando algum código não tem correspondência;
            se False, devolve <NA> para esses casos, para que sejam reportados.
    """
    oficiais = pd.Index(pd.Series(list(codigos_oficiais)).astype(str))
    if not oficiais.str.fullmatch(r"\d{7}").all():
        raise ValueError("A lista oficial deve conter apenas códigos de 7 dígitos.")
    prefixo = pd.Series(oficiais, index=oficiais.str[:6])
    if prefixo.index.has_duplicates:
        raise ValueError("Prefixos de 6 dígitos repetidos na lista oficial.")

    s = _limpar(codigos)
    resultado = pd.Series(pd.NA, index=s.index, dtype="string")

    sete = s.str.fullmatch(r"\d{7}").fillna(False)
    resultado[sete] = s[sete].where(s[sete].isin(oficiais))

    seis = s.str.fullmatch(r"\d{6}").fillna(False)
    resultado[seis] = s[seis].map(prefixo).astype("string")

    invalidos = s[resultado.isna() & s.notna()].unique().tolist()
    if invalidos and estrito:
        raise CodigoMunicipioInvalido(sorted(str(c) for c in invalidos))
    return resultado


def faixa_porte(populacao: pd.Series) -> pd.Series:
    """Classifica municípios nas quatro faixas de porte usadas no artigo."""
    rotulos = pd.Series(pd.NA, index=populacao.index, dtype="string")
    for inferior, superior, rotulo in FAIXAS_PORTE:
        rotulos[(populacao > inferior) & (populacao <= superior)] = rotulo
    return rotulos
