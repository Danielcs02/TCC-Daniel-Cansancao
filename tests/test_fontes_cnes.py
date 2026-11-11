"""Testes das regras de contagem do CNES com tabelas pequenas no formato dos
arquivos ST e PF do DATASUS (colunas e códigos reais, registros fictícios)."""

import pandas as pd
import pytest

from tcc.fontes import cnes

RIO, SUMIDOURO = "330455", "330570"


def _st(**alteracoes) -> pd.DataFrame:
    base = {
        "CNES": ["0000001", "0000002", "0000003", "0000004", "0000005"],
        "CODUFMUN": [RIO, RIO, RIO, SUMIDOURO, SUMIDOURO],
        # 01 posto de saúde, 02 centro de saúde/UBS, 05 hospital geral, 22 consultório
        "TP_UNID": ["01", "02", "05", "02", "22"],
        "COMPETEN": ["202212"] * 5,
    }
    base.update(alteracoes)
    return pd.DataFrame(base, dtype="string")


def _pf(**alteracoes) -> pd.DataFrame:
    base = {
        "CNES": ["0000001", "0000002", "0000003", "0000004", "0000004", "0000003"],
        "CODUFMUN": [RIO, RIO, RIO, SUMIDOURO, SUMIDOURO, RIO],
        # médico (CBO 2002), o mesmo médico em outro vínculo, código SUS antigo,
        # médico em Sumidouro, enfermeiro, médico sem CNS
        "CBO": ["225125", "225125", "2231F9", "225142", "223505", "225320"],
        "CNS_PROF": ["111", "111", "222", "111", "333", ""],
        "CPF_PROF": ["a", "a", "b", "a", "c", "d"],
        "COMPETEN": ["202212"] * 6,
    }
    base.update(alteracoes)
    return pd.DataFrame(base, dtype="string")


def _dim() -> pd.DataFrame:
    return pd.DataFrame({"codigo_municipio": ["3304557", "3305703", "3300100"],
                         "populacao": [6_211_223, 15_206, 167_434]})


def test_url_e_nome_do_arquivo():
    assert cnes.nome_arquivo("ST", "rj") == "STRJ2212.dbc"
    assert cnes.url_arquivo("PF", "RJ") == (
        "ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/PF/PFRJ2212.dbc")


def test_conta_so_postos_e_centros_de_saude():
    assert cnes.contar_ubs(_st()).to_dict() == {RIO: 2, SUMIDOURO: 1}


def test_medico_conta_uma_vez_por_municipio():
    # Rio: CNS 111 (dois vínculos), 222 e o sem CNS (pelo CPF) = 3; Sumidouro: 111 = 1
    assert cnes.contar_medicos(_pf()).to_dict() == {RIO: 3, SUMIDOURO: 1}


def test_competencia_diferente_falha():
    with pytest.raises(ValueError, match="competência"):
        cnes.contar_ubs(_st(COMPETEN=["202211"] * 5))


def test_estabelecimento_repetido_falha():
    with pytest.raises(ValueError, match="repetido"):
        cnes.contar_ubs(_st(CNES=["0000001"] * 5))


def test_indicadores_por_habitante():
    out = cnes.calcular_indicadores(cnes.contar_ubs(_st()), cnes.contar_medicos(_pf()), _dim())
    assert list(out.columns) == ["codigo_municipio", "codigo_indicador", "ano_referencia", "valor"]
    v = out.set_index(["codigo_indicador", "codigo_municipio"])["valor"]
    assert v["H1", "3304557"] == pytest.approx(2 / 6_211_223 * 10_000)
    assert v["H2", "3305703"] == pytest.approx(1 / 15_206 * 1_000)
    # município do escopo sem registro no CNES tem contagem zero
    assert v["H1", "3300100"] == 0 and v["H2", "3300100"] == 0
    assert len(out) == 6


def test_codigo_desconhecido_falha():
    st = _st(CODUFMUN=["999999"] * 5)
    with pytest.raises(ValueError):
        cnes.calcular_indicadores(cnes.contar_ubs(st), cnes.contar_medicos(_pf()), _dim())
