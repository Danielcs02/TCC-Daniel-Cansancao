"""Configuração lida do ambiente (ver ``.env.example``)."""

from __future__ import annotations

import os
from pathlib import Path


def dir_dados() -> Path:
    return Path(os.getenv("TCC_DATA_DIR", "data"))


def dir_bruto(fonte: str) -> Path:
    return dir_dados() / "bruto" / fonte


def dir_padronizado() -> Path:
    return dir_dados() / "padronizado"


def escopo_uf() -> str | None:
    """Sigla da UF a extrair (prova de conceito: RJ) ou None para o país inteiro.

    Definida por ``TCC_UF``; o valor ``BR`` indica execução nacional.
    """
    sigla = os.getenv("TCC_UF", "RJ").strip().upper()
    return None if sigla in ("", "BR") else sigla
