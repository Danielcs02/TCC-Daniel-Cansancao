# Conectividade e infraestrutura social nos municípios brasileiros

Repositório do Trabalho de Conclusão de Curso de **Daniel Cansanção da Silva**, Engenharia de Computação, Universidade Veiga de Almeida (UVA). Orientador: Prof. Vitor Amadeu Souza.

**Título:** Integração de dados abertos para análise comparativa entre conectividade e infraestrutura social nos municípios brasileiros.

**Área de pesquisa:** Banco de Dados e Sistemas de Informação.

## Pergunta de pesquisa

Em que medida o nível de conectividade dos municípios brasileiros acompanha a disponibilidade de infraestrutura social básica (saneamento, saúde e educação), no ano de referência de 2022?

## O que o projeto faz

1. **Integra** bases públicas do IBGE, da Anatel, do Ministério da Saúde e do Inep em um modelo dimensional com o município como grão e o código IBGE como chave.
2. **Valida** os dados com regras automatizadas de qualidade: esquema, chave, unicidade, domínio, período e completude.
3. **Constrói** o Índice de Infraestrutura Social (IIS), com normalização, pesos e análise de sensibilidade documentados.
4. **Compara** o IIS com duas medidas de conectividade, por correlação de Spearman e por uma classificação dos municípios em quadrantes.
5. **Apresenta** os resultados em um painel com mapas.

## Indicadores

| Código | Indicador | Fonte | Papel |
|---|---|---|---|
| C1 | Índice Brasileiro de Conectividade (IBC) | Anatel, dez. 2022 | conectividade (oferta) |
| C2 | Moradores em domicílios com Internet (%) | IBGE, Censo 2022 | conectividade (acesso) |
| S1 | Abastecimento por rede geral de água (%) | IBGE, Censo 2022 | IIS, saneamento |
| S2 | Esgotamento por rede ou fossa ligada à rede (%) | IBGE, Censo 2022 | IIS, saneamento |
| H1 | Unidades básicas de saúde por 10 mil hab. | CNES, dez. 2022 | IIS, saúde |
| H2 | Médicos por mil hab. | CNES, dez. 2022 | IIS, saúde |
| E1 | Distorção idade-série no ensino fundamental (%) | Inep, 2022 | IIS, educação (sentido negativo) |
| E2 | Docentes com formação adequada (%) | Inep, 2022 | IIS, educação |

Detalhes e links: [`docs/fontes.md`](docs/fontes.md). Justificativas: [`docs/decisoes.md`](docs/decisoes.md).

## Arquitetura

- **Orquestração:** Dagster, com cada etapa modelada como um ativo de dados.
- **Armazenamento:** PostgreSQL 16 com PostGIS, em Docker.
- **Transformação e qualidade:** pandas e Pandera.
- **Painel:** Streamlit e Plotly.

O modelo de dados e o fluxo entre as camadas bruta, padronizada e analítica estão em [`docs/modelo-de-dados.md`](docs/modelo-de-dados.md).

## Estrutura

```
src/tcc/
  catalogo.py     catálogo dos indicadores (fonte única de definições)
  municipio.py    padronização do código IBGE (6 para 7 dígitos) e faixas de porte
  qualidade.py    regras de qualidade da tabela de fatos (Pandera)
  indice.py       normalização, IIS, análise de sensibilidade e quadrantes
  config.py       pasta de dados e UF a extrair (variáveis de ambiente)
  extracao.py     ativos da camada bruta (baixam as fontes e geram a camada padronizada)
  fontes/         um módulo por fonte oficial (SIDRA/IBGE, Inep, CNES, Anatel)
  definitions.py  ativos e dependências do Dagster
sql/              esquema do banco (modelo dimensional)
docs/             fontes, decisões metodológicas e modelo de dados
tests/            testes automatizados, incluindo o pipeline de ponta a ponta
data/             dados locais (não versionados), ver data/README.md
```

## Como executar

Pré-requisitos: Python 3.12+ e Docker.

```bash
# ambiente
python -m venv .venv
source .venv/bin/activate          # no Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# banco (cria o esquema na primeira subida)
cp .env.example .env
docker compose up -d

# testes
pytest

# interface do Dagster em http://localhost:3000
dagster dev
```

## Roteiro

- [x] Pré-projeto aprovado com ajustes
- [x] Entrega parcial (AVA2): introdução, referencial teórico e metodologia
- [x] Catálogo de indicadores, esquema do banco e decisões metodológicas
- [x] Módulo do índice (normalização, agregação, sensibilidade, quadrantes) com testes
- [x] Regras de qualidade e padronização da chave municipal com testes
- [x] Prova de conceito: extração das quatro fontes para os 92 municípios do RJ
- [ ] Carga no PostgreSQL
- [ ] Execução nacional (5.570 municípios)
- [ ] Painel em Streamlit
- [ ] Análise dos resultados e versão final do artigo

## Licença

A definir.
