import pandas as pd
import pytest

from tcc import municipio


def test_seis_digitos_viram_sete(codigos_oficiais):
    s = pd.Series(["330455", "330330"])  # formato DATASUS
    assert municipio.normalizar_codigo(s, codigos_oficiais).tolist() == ["3304557", "3303302"]


def test_aceita_numero_e_float(codigos_oficiais):
    s = pd.Series([3304557, 330170.0])
    assert municipio.normalizar_codigo(s, codigos_oficiais).tolist() == ["3304557", "3301702"]


def test_codigo_inexistente_gera_erro(codigos_oficiais):
    with pytest.raises(municipio.CodigoMunicipioInvalido):
        municipio.normalizar_codigo(pd.Series(["9999999"]), codigos_oficiais)


def test_modo_nao_estrito_devolve_nulo(codigos_oficiais):
    out = municipio.normalizar_codigo(pd.Series(["3304557", "123"]), codigos_oficiais,
                                      estrito=False)
    assert out.iloc[0] == "3304557" and pd.isna(out.iloc[1])


def test_faixas_de_porte():
    pop = pd.Series([5_000, 20_000, 20_001, 150_000, 6_200_000])
    assert municipio.faixa_porte(pop).tolist() == [
        "até 20 mil", "até 20 mil", "20 mil a 100 mil", "100 mil a 500 mil", "acima de 500 mil"]
