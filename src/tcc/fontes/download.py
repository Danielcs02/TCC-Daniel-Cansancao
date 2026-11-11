"""Download de arquivos das fontes oficiais para a camada bruta."""

from __future__ import annotations

import gzip
import time
import urllib.request
from pathlib import Path

AGENTE = "tcc-conectividade/0.1 (pesquisa academica)"


def baixar(url: str, destino: Path, refazer: bool = False, tentativas: int = 3,
           espera: float = 5.0, timeout: float = 300.0) -> Path:
    """Baixa ``url`` para ``destino`` e devolve o caminho do arquivo.

    O conteúdo é gravado exatamente como recebido. Se o arquivo já existe e
    ``refazer`` é False, o download é pulado, para que a camada bruta registre o
    que foi efetivamente usado e não mude a cada execução.
    """
    destino = Path(destino)
    if destino.exists() and not refazer:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    ultimo_erro: Exception | None = None
    for tentativa in range(1, tentativas + 1):
        try:
            with urllib.request.urlopen(pedido, timeout=timeout) as resposta:
                conteudo = resposta.read()
                # compressão de transporte (o IBGE envia gzip mesmo sem pedir)
                if resposta.headers.get("Content-Encoding", "").lower() == "gzip":
                    conteudo = gzip.decompress(conteudo)
            temporario = destino.with_suffix(destino.suffix + ".parcial")
            temporario.write_bytes(conteudo)
            temporario.replace(destino)
            return destino
        except OSError as erro:  # inclui URLError, HTTPError e timeout
            ultimo_erro = erro
            if tentativa < tentativas:
                time.sleep(espera * tentativa)
    raise RuntimeError(f"Falha ao baixar {url}: {ultimo_erro}") from ultimo_erro
