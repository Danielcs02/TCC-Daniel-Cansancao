"""Executa o pipeline do Dagster de ponta a ponta com arquivos sintéticos."""

import numpy as np
import pandas as pd
from dagster import AssetSelection, materialize

from tcc import definitions


def test_definicoes_carregam():
    nomes = {k.to_user_string() for a in definitions.ATIVOS for k in a.keys}
    assert {"fato_indicador_municipal", "iis", "sensibilidade", "quadrantes",
            "padronizado_dim_municipio", "padronizado_censo"} <= nomes


def test_pipeline_ponta_a_ponta(tmp_path, monkeypatch, largo):
    pad = tmp_path / "padronizado"
    pad.mkdir()
    rng = np.random.default_rng(0)
    pd.DataFrame({
        "codigo_municipio": largo.index,
        "nome": [f"Município {i}" for i in range(len(largo))],
        "uf": "RJ",
        "regiao": "Sudeste",
        "populacao": rng.integers(3_000, 2_000_000, len(largo)),
    }).to_csv(pad / "dim_municipio.csv", index=False)

    longo = largo.reset_index().melt(id_vars="codigo_municipio", var_name="codigo_indicador",
                                     value_name="valor")
    longo["ano_referencia"] = 2022
    # um arquivo por fonte, como o pipeline fará; o CNES chega com 6 dígitos
    cnes = longo["codigo_indicador"].isin(["H1", "H2"])
    longo.loc[cnes, "codigo_municipio"] = longo.loc[cnes, "codigo_municipio"].str[:6]
    longo[cnes].to_csv(pad / "fato_cnes.csv", index=False)
    longo[~cnes].to_csv(pad / "fato_demais.csv", index=False)

    monkeypatch.setenv("TCC_DATA_DIR", str(tmp_path))
    # só a camada analítica; os ativos de extração acessam a rede
    resultado = materialize(definitions.ATIVOS, selection=AssetSelection.groups("tcc"))
    assert resultado.success
    iis = resultado.output_for_node("iis")
    assert len(iis) == len(largo) and iis["iis"].between(0, 1).all()
    assert len(resultado.output_for_node("sensibilidade")) == 8
