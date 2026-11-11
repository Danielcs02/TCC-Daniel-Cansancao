import pytest

from tcc import config
from tcc.fontes.download import baixar


def test_baixa_e_reaproveita_arquivo(tmp_path):
    origem = tmp_path / "origem.txt"
    origem.write_text("versão 1")
    destino = tmp_path / "bruto" / "x" / "arquivo.txt"

    baixar(origem.as_uri(), destino)
    assert destino.read_text() == "versão 1"

    origem.write_text("versão 2")
    baixar(origem.as_uri(), destino)  # já existe: não baixa de novo
    assert destino.read_text() == "versão 1"

    baixar(origem.as_uri(), destino, refazer=True)
    assert destino.read_text() == "versão 2"


def test_falha_depois_das_tentativas(tmp_path):
    with pytest.raises(RuntimeError, match="Falha ao baixar"):
        baixar((tmp_path / "nao_existe").as_uri(), tmp_path / "d.txt", tentativas=2, espera=0)
    assert not (tmp_path / "d.txt").exists()


@pytest.mark.parametrize("valor, esperado", [("rj", "RJ"), ("BR", None), ("", None)])
def test_escopo_uf(monkeypatch, valor, esperado):
    monkeypatch.setenv("TCC_UF", valor)
    assert config.escopo_uf() == esperado


def test_escopo_padrao_e_rj(monkeypatch):
    monkeypatch.delenv("TCC_UF", raising=False)
    assert config.escopo_uf() == "RJ"
