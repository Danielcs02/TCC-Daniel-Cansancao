# Pasta de dados

Os arquivos de dados não são versionados (ver `.gitignore`). A estrutura esperada é:

```
data/
  bruto/         arquivos como baixados das fontes oficiais, sem alteração
  padronizado/   arquivos já convertidos para o formato comum, lidos pelo pipeline
```

## Formato da camada padronizada

**`padronizado/dim_municipio.csv`**: uma linha por município.

| coluna | tipo | exemplo |
|---|---|---|
| codigo_municipio | texto, 7 dígitos | 3304557 |
| nome | texto | Rio de Janeiro |
| uf | texto | RJ |
| regiao | texto | Sudeste |
| populacao | inteiro | população do Censo 2022 |

**`padronizado/fato_<fonte>.csv`**: um arquivo por fonte, no formato longo.

| coluna | tipo | observação |
|---|---|---|
| codigo_municipio | texto | 7 dígitos (IBGE) ou 6 dígitos (DATASUS); o pipeline converte |
| codigo_indicador | texto | um dos códigos de `docs/fontes.md` (C1, C2, S1, S2, H1, H2, E1, E2) |
| ano_referencia | inteiro | 2022 |
| valor | número | percentuais entre 0 e 100 |

Os ativos que baixam e geram esses arquivos a partir das fontes oficiais fazem parte da prova de conceito (ver roteiro no `README.md` da raiz).
