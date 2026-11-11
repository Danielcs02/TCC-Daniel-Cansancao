"""Testes da extração do IBC com linhas reais do arquivo da Anatel (Rio de
Janeiro, Sumidouro e Armação dos Búzios, 2021 a 2025). Ver tests/dados/."""

import zipfile
from pathlib import Path

import pandas as pd
import pytest

from tcc.fontes import anatel

DADOS = Path(__file__).parent / "dados"


def _zip(tmp_path: Path, nome_csv: str = anatel.ARQUIVO_CSV) -> Path:
    caminho = tmp_path / anatel.ARQUIVO_ZIP
    with zipfile.ZipFile(caminho, "w") as z:
        z.writestr(nome_csv, (DADOS / "ibc_amostra.csv").read_bytes())
    return caminho


def test_le_csv_da_anatel(tmp_path):
    df = anatel.ler_zip(_zip(tmp_path))
    assert set(df["Ano"]) == {2021, 2022, 2023, 2024, 2025}
    assert df["Código Município"].str.fullmatch(r"\d{7}").all()


def test_c1_usa_o_ibc_de_2022(tmp_path):
    out = anatel.calcular_c1(anatel.ler_zip(_zip(tmp_path)))
    assert list(out.columns) == ["codigo_municipio", "codigo_indicador", "ano_referencia", "valor"]
    assert out["codigo_indicador"].eq("C1").all() and out["ano_referencia"].eq(2022).all()
    # Armação dos Búzios tem o maior IBC de 2022, como divulgado pela Anatel
    assert out.set_index("codigo_municipio")["valor"].to_dict() == {
        "3300233": 83.28, "3304557": 71.96, "3305703": 65.82}


def test_filtro_por_uf(tmp_path):
    df = anatel.ler_zip(_zip(tmp_path))
    assert len(anatel.calcular_c1(df, uf="rj")) == 3
    assert anatel.calcular_c1(df, uf="SP").empty


def test_csv_ausente_no_zip_falha(tmp_path):
    with pytest.raises(ValueError, match="não encontrado"):
        anatel.ler_zip(_zip(tmp_path, nome_csv="outro.csv"))


def test_sem_ano_de_referencia_falha(tmp_path):
    df = anatel.ler_zip(_zip(tmp_path))
    with pytest.raises(ValueError, match="2022"):
        anatel.calcular_c1(df[df["Ano"] != 2022])


def test_ibc_fora_da_escala_falha(tmp_path):
    df = anatel.ler_zip(_zip(tmp_path))
    df.loc[df["Ano"] == 2022, "IBC"] = 150.0
    with pytest.raises(ValueError, match="escala"):
        anatel.calcular_c1(df)


def test_municipio_repetido_falha(tmp_path):
    df = anatel.ler_zip(_zip(tmp_path))
    dup = pd.concat([df, df[(df["Ano"] == 2022)].head(1)])
    with pytest.raises(ValueError, match="repetido"):
        anatel.calcular_c1(dup)
