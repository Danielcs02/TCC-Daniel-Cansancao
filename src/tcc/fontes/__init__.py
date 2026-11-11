"""Extração das fontes oficiais (camada bruta) e conversão para a camada padronizada.

Cada módulo cuida de uma fonte. A regra geral é:

1. baixar o arquivo da fonte e guardá-lo sem alteração em ``data/bruto/<fonte>/``;
2. converter o conteúdo em uma tabela no formato descrito em ``data/README.md``.

As funções de conversão recebem o conteúdo já baixado, para que possam ser
testadas sem acesso à rede.
"""
