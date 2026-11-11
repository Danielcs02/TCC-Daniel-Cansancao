# Decisões metodológicas

Registro das escolhas que afetam o desenho do trabalho e o motivo de cada uma. O professor orientador indicou que essas escolhas devem ser justificadas no texto; aqui ficam registradas também para quem ler o código.

## 1. Município como unidade de análise

As pesquisas de referência sobre uso da Internet (TIC Domicílios e PNAD Contínua TIC) só descem até UF, o que daria 27 observações. As bases de infraestrutura social são municipais. Optou-se pelo município, usando Anatel e Censo 2022 como fontes de conectividade, porque a resolução municipal sustenta a análise de correlação, a estratificação por porte e o mapa.

## 2. Conectividade fora do índice

A Anatel já publica um índice municipal de conectividade (IBC). Em vez de construir outro, o trabalho usa duas medidas complementares e as mantém separadas do índice de infraestrutura social, para poder compará-las a ele:

- **C1 (IBC):** oferta de infraestrutura de telecomunicações;
- **C2 (Censo):** acesso efetivo das famílias à Internet no domicílio.

## 3. Ano de referência único: 2022

Todas as fontes representam 2022, para que diferenças de ano de referência não produzam conclusões equivocadas. O Censo Demográfico 2022 é a âncora.

## 4. Saneamento pelo Censo, e não pelo SNIS

O SNIS depende de informação declarada por prestadores e municípios, tem não resposta em parte deles (sobretudo em esgoto) e foi sucedido pelo SINISA em 2024, com mudança metodológica. O Censo cobre todos os municípios na mesma data de referência da população usada como denominador.

## 5. Saúde por atenção primária

Unidades básicas de saúde e médicos por habitante, do CNES. Leitos foram descartados porque se concentram em municípios-polo.

## 6. Educação pelos Indicadores Educacionais do Inep

O Ideb não tem edição de 2022 (é bienal, anos ímpares).

## 7. Construção do Índice de Infraestrutura Social (IIS)

| Etapa | Escolha | Justificativa |
|---|---|---|
| Valores ausentes | não imputar; município fica fora do índice e é reportado | imputação criaria valores sem lastro nas fontes |
| Valores extremos | winsorização nos percentis 1 e 99, só em H1 e H2 | taxas por habitante explodem em municípios muito pequenos |
| Normalização | mín-máx; E1 invertido | preserva a distribuição; mesmo princípio do IDHM |
| Subíndice | média aritmética dos indicadores da dimensão | dois indicadores por dimensão |
| Agregação | média aritmética, pesos iguais | sem base teórica para priorizar uma dimensão (OECD, 2008) |

**Análise de sensibilidade** (`tcc.indice.analise_sensibilidade`): o ordenamento da referência é comparado com três cenários, pela correlação de Spearman e pelo deslocamento médio de posições:

1. agregação geométrica (reduz a compensação entre dimensões);
2. pesos pelo primeiro componente principal;
3. exclusão de um indicador por vez.

## 8. Escopo reduzido

Por orientação do professor, o agrupamento por k-means saiu do escopo. A pergunta de pesquisa é respondida pela classificação em quadrantes (medianas de conectividade e de IIS).

## 9. Tecnologias

| Função | Escolha | Por quê |
|---|---|---|
| Orquestração | Dagster | dependências explícitas entre ativos e rastreio da origem de cada valor |
| Banco | PostgreSQL 16 com PostGIS, em Docker | reprodutível localmente, sem serviço pago |
| Qualidade | Pandera | regras declarativas, todos os erros reportados de uma vez |
| Painel | Streamlit e Plotly | código versionado no mesmo repositório |
