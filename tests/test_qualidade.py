import pandas as pd
import pandera.pandas as pa
import pytest

from tcc import qualidade


def _fato(**alteracoes):
    base = {
        "codigo_municipio": ["3304557", "3303302", "3304557"],
        "codigo_indicador": ["S1", "S1", "H1"],
        "ano_referencia": [2022, 2022, 2022],
        "valor": [98.5, 92.1, 1.7],
    }
    base.update(alteracoes)
    return pd.DataFrame(base)


def test_fato_valido_passa(codigos_oficiais):
    assert len(qualidade.validar_fato(_fato(), codigos_oficiais)) == 3


def test_percentual_acima_de_100_falha(codigos_oficiais):
    with pytest.raises(pa.errors.SchemaErrors):
        qualidade.validar_fato(_fato(valor=[101.0, 92.1, 1.7]), codigos_oficiais)


def test_duplicidade_falha(codigos_oficiais):
    dup = _fato(codigo_indicador=["S1", "S1", "S1"], codigo_municipio=["3304557"] * 3)
    with pytest.raises(pa.errors.SchemaErrors):
        qualidade.validar_fato(dup, codigos_oficiais)


def test_ano_diferente_de_2022_falha(codigos_oficiais):
    with pytest.raises(pa.errors.SchemaErrors):
        qualidade.validar_fato(_fato(ano_referencia=[2022, 2021, 2022]), codigos_oficiais)


def test_municipio_fora_da_dimensao_falha(codigos_oficiais):
    with pytest.raises(pa.errors.SchemaErrors):
        qualidade.validar_fato(_fato(codigo_municipio=["3304557", "3550308", "3304557"]),
                               codigos_oficiais)


def test_relatorio_de_completude(codigos_oficiais):
    rel = qualidade.relatorio_completude(_fato(), codigos_oficiais)
    assert rel.loc["S1", "municipios_com_valor"] == 2
    assert rel.loc["E1", "municipios_ausentes"] == len(codigos_oficiais)


def test_municipio_incompleto_fica_fora(largo):
    largo.iloc[0, largo.columns.get_loc("H2")] = None
    completos, excluidos = qualidade.municipios_completos(largo, ["S1", "H2"])
    assert len(excluidos) == 1 and excluidos[0] == largo.index[0]
    assert len(completos) == len(largo) - 1
