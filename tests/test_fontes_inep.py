"""Testes da extração do Inep com as planilhas reais de 2022, reduzidas a dois
municípios (Rio de Janeiro, 3304557, e Sumidouro, 3305703). Ver tests/dados/."""

import hashlib
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from tcc.fontes import inep

DADOS = Path(__file__).parent / "dados"
TDI, AFD = inep.INDICADORES_INEP


def _zip(tmp_path: Path, sigla: str, md5: str | None = None) -> Path:
    """Monta um .zip com a mesma estrutura do publicado pelo Inep."""
    conteudo = (DADOS / f"{sigla}_2022_amostra.xlsx").read_bytes()
    md5 = md5 or hashlib.md5(conteudo).hexdigest()
    pasta = f"{sigla}_2022_MUNICIPIOS"
    caminho = tmp_path / f"{pasta}.zip"
    with zipfile.ZipFile(caminho, "w") as z:
        z.writestr(f"{pasta}/{sigla}_MUNICIPIOS_2022.xlsx", conteudo)
        z.writestr(f"{pasta}/MD5_{sigla}_MUNICIPIOS_2022.txt",
                   f"{md5} *{sigla}_MUNICIPIOS_2022.xlsx\n")
    return caminho


def _planilha(sigla: str) -> pd.DataFrame:
    return inep.ler_planilha((DADOS / f"{sigla}_2022_amostra.xlsx").read_bytes())


def test_ler_planilha_descarta_titulos_e_notas():
    df = _planilha("AFD")
    assert {"NU_ANO_CENSO", "SG_UF", "CO_MUNICIPIO", "NO_CATEGORIA", "NO_DEPENDENCIA",
            "FUN_CAT_1"} <= set(df.columns)
    assert set(df["CO_MUNICIPIO"]) == {"3304557", "3305703"}


@pytest.mark.parametrize("ind, sigla, esperado", [
    # valores da linha Total/Total das planilhas do Inep de 2022
    (TDI, "TDI", {"3304557": 11.0, "3305703": 23.0}),
    (AFD, "AFD", {"3304557": 62.0, "3305703": 36.8}),
])
def test_indicadores_do_inep(tmp_path, ind, sigla, esperado):
    out = inep.calcular_indicador(ind, inep.ler_zip(_zip(tmp_path, sigla)))
    assert list(out.columns) == ["codigo_municipio", "codigo_indicador", "ano_referencia", "valor"]
    assert out["codigo_indicador"].eq(ind.codigo).all() and out["ano_referencia"].eq(2022).all()
    assert out.set_index("codigo_municipio")["valor"].to_dict() == esperado


def test_codigos_e_colunas_do_catalogo():
    assert (TDI.codigo, TDI.coluna) == ("E1", "FUN_CAT_0")
    assert (AFD.codigo, AFD.coluna) == ("E2", "FUN_CAT_1")


def test_md5_divergente_falha(tmp_path):
    with pytest.raises(inep.ArquivoCorrompido):
        inep.ler_zip(_zip(tmp_path, "TDI", md5="0" * 32))


def test_filtro_por_uf():
    assert inep.calcular_indicador(TDI, _planilha("TDI"), uf="SP").empty
    assert len(inep.calcular_indicador(TDI, _planilha("TDI"), uf="rj")) == 2


def test_valor_nao_publicado_fica_de_fora():
    df = _planilha("TDI")
    rio = (df["CO_MUNICIPIO"] == "3304557")
    df.loc[rio, "FUN_CAT_0"] = "--"
    assert inep.calcular_indicador(TDI, df)["codigo_municipio"].tolist() == ["3305703"]


def test_ano_diferente_de_2022_falha():
    df = _planilha("TDI")
    df["NU_ANO_CENSO"] = "2021"
    with pytest.raises(ValueError, match="ano"):
        inep.calcular_indicador(TDI, df)
