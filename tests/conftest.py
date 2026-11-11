import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def codigos_oficiais() -> list[str]:
    # Códigos reais de municípios do Estado do Rio de Janeiro.
    return ["3304557", "3303302", "3301702", "3300456", "3300704", "3304904"]


@pytest.fixture
def largo() -> pd.DataFrame:
    """Dados sintéticos no formato largo, só para testar a mecânica do índice."""
    rng = np.random.default_rng(42)
    n = 200
    # passo de 10 para que o prefixo de 6 dígitos seja único, como nos códigos reais
    idx = pd.Index([f"{3300000 + 10 * i:07d}" for i in range(n)], name="codigo_municipio")
    return pd.DataFrame({
        "C1": rng.uniform(10, 95, n),
        "C2": rng.uniform(40, 99, n),
        "S1": rng.uniform(20, 100, n),
        "S2": rng.uniform(5, 100, n),
        "H1": rng.gamma(2.0, 1.5, n),
        "H2": rng.gamma(1.5, 1.0, n),
        "E1": rng.uniform(2, 40, n),
        "E2": rng.uniform(30, 95, n),
    }, index=idx)
