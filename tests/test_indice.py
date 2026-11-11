import numpy as np
import pandas as pd
import pytest

from tcc import catalogo, indice


def test_minmax_vai_de_0_a_1():
    s = pd.Series([10.0, 20.0, 30.0], name="S1")
    z = indice.normalizar_minmax(s)
    assert z.tolist() == [0.0, 0.5, 1.0]


def test_minmax_inverte_sentido_negativo():
    s = pd.Series([2.0, 10.0, 40.0], name="E1")
    z = indice.normalizar_minmax(s, sentido=-1)
    assert z.iloc[0] == 1.0 and z.iloc[-1] == 0.0


def test_minmax_sem_variacao_falha():
    with pytest.raises(ValueError):
        indice.normalizar_minmax(pd.Series([5.0, 5.0, 5.0], name="X"))


def test_winsorizacao_corta_extremos():
    s = pd.Series(np.r_[np.arange(1, 100), 10_000.0])
    w = indice.winsorizar(s)
    assert w.max() < 10_000 and w.max() == s.quantile(0.99)


def test_normalizar_usa_so_indicadores_do_iis(largo):
    norm = indice.normalizar(largo)
    esperados = {i.codigo for i in catalogo.indicadores_do_iis()}
    assert set(norm.columns) == esperados
    assert norm.min().min() >= 0 and norm.max().max() <= 1


def test_subindice_e_media_da_dimensao(largo):
    norm = indice.normalizar(largo)
    sub = indice.subindices(norm)
    assert list(sub.columns) == list(catalogo.DIMENSOES_IIS)
    pd.testing.assert_series_equal(sub["saneamento"], norm[["S1", "S2"]].mean(axis=1),
                                   check_names=False)


def test_geometrica_nao_supera_aritmetica(largo):
    sub = indice.subindices(indice.normalizar(largo))
    piso = 0.01
    x = piso + (1 - piso) * sub
    aritm = x.mean(axis=1)
    geom = indice.agregar(sub, metodo="geometrica", piso=piso)
    assert (geom <= aritm + 1e-12).all()  # desigualdade das médias


def test_geometrica_nao_zera_com_um_subindice_nulo():
    sub = pd.DataFrame({"saneamento": [0.0], "saude": [1.0], "educacao": [1.0]})
    assert indice.agregar(sub, metodo="geometrica").iloc[0] > 0


def test_pesos_iguais_por_padrao():
    sub = pd.DataFrame({"saneamento": [0.3], "saude": [0.6], "educacao": [0.9]})
    assert indice.agregar(sub).iloc[0] == pytest.approx(0.6)


def test_pesos_pca_somam_um(largo):
    sub = indice.subindices(indice.normalizar(largo))
    pesos = indice.pesos_pca(sub)
    assert sum(pesos.values()) == pytest.approx(1.0)
    assert all(p >= 0 for p in pesos.values())


def test_rankings_identicos():
    s = pd.Series([0.1, 0.5, 0.9])
    r = indice.comparar_rankings(s, s)
    assert r["spearman"] == pytest.approx(1.0) and r["deslocamento_medio"] == 0


def test_sensibilidade_tem_todos_os_cenarios(largo):
    resultado = indice.analise_sensibilidade(largo)
    esperados = {"agregacao_geometrica", "pesos_pca"} | {
        f"sem_{i.codigo}" for i in catalogo.indicadores_do_iis()}
    assert set(resultado.index) == esperados
    assert resultado["spearman"].between(-1, 1).all()


def test_quadrantes_pelas_medianas():
    conect = pd.Series([1, 2, 3, 4], index=list("abcd"), dtype=float)
    iis = pd.Series([4, 3, 2, 1], index=list("abcd"), dtype=float)
    q = indice.classificar_quadrantes(conect, iis)
    assert q["a"] == "baixa conectividade, alta infraestrutura social"
    assert q["d"] == "alta conectividade, baixa infraestrutura social"
