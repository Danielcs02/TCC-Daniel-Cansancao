"""Testes da extração do IBGE com respostas reais do SIDRA, reduzidas a dois
municípios (Rio de Janeiro, 3304557, e Sumidouro, 3305703). Ver tests/dados/."""

import json
from pathlib import Path

import pandas as pd
import pytest

from tcc.fontes import ibge, sidra

DADOS = Path(__file__).parent / "dados"


def _sidra(tabela: int) -> pd.DataFrame:
    return sidra.ler_resultado(DADOS / f"sidra_{tabela}_amostra.json")


def _por_municipio(df: pd.DataFrame) -> dict[str, float]:
    return df.set_index("codigo_municipio")["valor"].round(2).to_dict()


# ----------------------------------------------------------------- SIDRA

def test_url_agregado_com_classificacoes():
    url = sidra.url_agregado(6894, 2022, [382, 1000382], "N6[N3[33]]",
                             {1821: [72129, 72144], 58: [95253]})
    assert url == ("https://servicodados.ibge.gov.br/api/v3/agregados/6894/periodos/2022/"
                   "variaveis/382%7C1000382?localidades=N6[N3[33]]"
                   "&classificacao=1821[72129,72144]%7C58[95253]")


def test_localidades_por_uf_e_pais():
    assert sidra.localidades_municipios(33) == "N6[N3[33]]"
    assert sidra.localidades_municipios(None) == "N6[all]"


def test_ler_resultado_formato_longo():
    df = _sidra(7555)
    assert {"variavel", "codigo_localidade", "periodo", "c11558", "c58", "c86", "valor"} <= set(df)
    assert set(df["codigo_localidade"]) == {"3304557", "3305703"}
    assert df["periodo"].eq(2022).all()


def test_simbolos_do_sidra_viram_ausente():
    resposta = [{"id": "93", "resultados": [{"classificacoes": [], "series": [
        {"localidade": {"id": "3304557", "nome": "Rio"}, "serie": {"2022": "-"}},
        {"localidade": {"id": "3305703", "nome": "Sumidouro"}, "serie": {"2022": "X"}},
        {"localidade": {"id": "3300100", "nome": "Angra"}, "serie": {"2022": "167434"}},
    ]}]}]
    df = sidra.ler_resultado(json.dumps(resposta))
    assert df["valor"].isna().sum() == 2 and df["valor"].iloc[2] == 167434


# ----------------------------------------------------------------- IBGE

def test_dim_municipio():
    loc = ibge.ler_localidades(DADOS / "localidades_amostra.json")
    dim = ibge.montar_dim_municipio(_sidra(4714), loc)
    assert dim.to_dict("records") == [
        {"codigo_municipio": "3304557", "nome": "Rio de Janeiro", "uf": "RJ",
         "regiao": "Sudeste", "populacao": 6211223},
        {"codigo_municipio": "3305703", "nome": "Sumidouro", "uf": "RJ",
         "regiao": "Sudeste", "populacao": 15206},
    ]


def test_dim_municipio_ignora_municipio_criado_apos_o_censo():
    # a amostra de localidades tem um município de RO que não está na tabela do Censo
    loc = ibge.ler_localidades(DADOS / "localidades_amostra.json")
    assert len(loc) == 3
    assert len(ibge.montar_dim_municipio(_sidra(4714), loc)) == 2


def test_dim_municipio_sem_cadastro_falha():
    loc = ibge.ler_localidades(DADOS / "localidades_amostra.json")
    with pytest.raises(ValueError, match="sem cadastro"):
        ibge.montar_dim_municipio(_sidra(4714), loc[loc["codigo_municipio"] != "3305703"])


def test_codigo_da_uf():
    loc = ibge.ler_localidades(DADOS / "localidades_amostra.json")
    assert ibge.codigo_da_uf(loc, "rj") == 33
    with pytest.raises(ValueError):
        ibge.codigo_da_uf(loc, "XX")


@pytest.mark.parametrize("codigo, tabela, esperado", [
    # valores publicados no SIDRA (variável 1000382), conferidos em 11/11/2026
    ("S1", 6894, {"3304557": 98.25, "3305703": 25.72}),
    ("S2", 7555, {"3304557": 94.55, "3305703": 24.82}),
    ("C2", 9942, {"3304557": 92.29, "3305703": 90.87}),
])
def test_indicadores_do_censo(codigo, tabela, esperado):
    ind = next(i for i in ibge.INDICADORES_CENSO if i.codigo == codigo)
    assert ind.tabela == tabela
    out = ibge.calcular_indicador(ind, _sidra(tabela))
    assert list(out.columns) == ["codigo_municipio", "codigo_indicador", "ano_referencia", "valor"]
    assert out["codigo_indicador"].eq(codigo).all() and out["ano_referencia"].eq(2022).all()
    assert _por_municipio(out) == esperado


def test_divergencia_com_publicado_falha():
    ind = ibge.INDICADORES_CENSO[0]
    df = _sidra(ind.tabela)
    alterar = (df["variavel"] == "382") & (df["c1821"] == "72144") & (df["c58"] == "95253") \
        & (df["c86"] == "95251") & (df["codigo_localidade"] == "3305703")
    df.loc[alterar, "valor"] += 1000
    with pytest.raises(ibge.DivergenciaPublicacao):
        ibge.calcular_indicador(ind, df)


def test_municipio_sem_contagem_fica_de_fora():
    ind = ibge.INDICADORES_CENSO[1]
    df = _sidra(ind.tabela)
    df.loc[df["codigo_localidade"] == "3305703", "valor"] = float("nan")
    out = ibge.calcular_indicador(ind, df)
    assert out["codigo_municipio"].tolist() == ["3304557"]
