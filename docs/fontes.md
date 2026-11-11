# Catálogo de fontes de dados

Todas as fontes são públicas e se referem a 2022, ano do Censo Demográfico. A coluna "Status" indica o que já foi conferido e o que será confirmado na prova de conceito.

| Código | Indicador | Fonte | Referência | Chave municipal | Status |
|---|---|---|---|---|---|
| C1 | Índice Brasileiro de Conectividade (IBC) | Anatel | dez. 2022 | 7 dígitos | confirmar disponibilidade da edição 2022 para download |
| C2 | Moradores em domicílios com acesso à Internet (%) | IBGE, Censo 2022 (amostra) | 2022 | 7 dígitos | extraído (SIDRA 9942) |
| S1 | Moradores em domicílios abastecidos por rede geral de água (%) | IBGE, Censo 2022 (universo) | 2022 | 7 dígitos | extraído (SIDRA 6894) |
| S2 | Moradores em domicílios com esgotamento por rede geral, pluvial ou fossa séptica ligada à rede (%) | IBGE, Censo 2022 (universo) | 2022 | 7 dígitos | extraído (SIDRA 7555) |
| H1 | Unidades básicas de saúde por 10 mil habitantes | CNES (DATASUS) | competência dez. 2022 | 6 dígitos | a extrair |
| H2 | Médicos com vínculo ativo por mil habitantes | CNES (DATASUS) | competência dez. 2022 | 6 dígitos | a extrair |
| E1 | Taxa de distorção idade-série no ensino fundamental (%) | Inep, Indicadores Educacionais | 2022 | 7 dígitos | a extrair |
| E2 | Docentes do ensino fundamental com formação adequada (%) | Inep, Indicadores Educacionais | 2022 | 7 dígitos | a extrair |

Apoio: população do Censo 2022 (denominador de H1 e H2; SIDRA 4714, extraída) e malha municipal digital do IBGE (mapas do painel).

## Tabelas do SIDRA usadas

Consultadas pela API de agregados do IBGE (https://servicodados.ibge.gov.br/api/docs/agregados?versao=3). Acesso em 11/11/2026. O código está em `src/tcc/fontes/ibge.py`.

| Uso | Tabela | Variável | Categorias | Link |
|---|---|---|---|---|
| População (dim_municipio) | 4714: População residente, área territorial e densidade demográfica | 93 (população residente) | não há | https://sidra.ibge.gov.br/tabela/4714 |
| S1 | 6894: Moradores em domicílios particulares permanentes ocupados, por existência de ligação à rede geral de distribuição de água e principal forma de abastecimento de água | 382 (moradores) | classificação 1821: numerador 72144 ("possui ligação à rede geral e a utiliza como forma principal"), total 72129 | https://sidra.ibge.gov.br/tabela/6894 |
| S2 | 7555: Moradores em domicílios particulares permanentes ocupados, por tipo de esgotamento sanitário | 382 | classificação 11558: numerador 46290 ("rede geral, rede pluvial ou fossa ligada à rede"), total 46292 | https://sidra.ibge.gov.br/tabela/7555 |
| C2 | 9942: Moradores em domicílios particulares permanentes ocupados, por existência de conexão domiciliar à Internet | 382 | classificação 2072: numerador 77585 ("sim"), total 77584 | https://sidra.ibge.gov.br/tabela/9942 |

Nas tabelas 6894, 7555 e 9942 são usadas as categorias "Total" de grupo de idade (58: 95253) e de cor ou raça (86: 95251).

Observações:

- **Moradores, não domicílios.** As tabelas 6803, 6805 e 9936 trazem os mesmos temas contados em domicílios; foram preteridas porque os indicadores do Quadro 1 são definidos em moradores.
- **S1, rede geral como forma principal.** O Censo 2022 separa quem tem ligação à rede geral e a usa como forma principal (72144) de quem tem ligação mas usa principalmente outra forma (72145). O indicador usa só a primeira, que é o recorte destacado pelo IBGE na divulgação. Para o Brasil: 82,89% (72144) contra 86,60% somando as duas.
- **C2 vem da amostra.** O total de moradores da tabela 9942 no Brasil (202.122.010) difere do total do universo nas tabelas 6894 e 7555 (202.083.020), o que é esperado para resultados expandidos da amostra.
- **Lista de municípios.** A base do `dim_municipio` é a tabela 4714 (5.570 municípios em 2022). Nome, UF e região vêm da API de localidades (https://servicodados.ibge.gov.br/api/v1/localidades/municipios?view=nivelado), que já lista 5.571 municípios por incluir Boa Esperança do Norte (MT), instalado depois do Censo; esse município fica de fora.

**Conferência.** Os percentuais são calculados a partir das contagens de moradores e comparados, município a município, com o percentual publicado pelo próprio IBGE na mesma tabela (variável 1000382); diferenças acima de 0,01 ponto percentual interrompem o pipeline. Valores conferidos (Brasil): S1 82,89%, S2 62,51%, C2 89,36%. Rio de Janeiro (3304557): S1 98,25%, S2 94,55%, C2 92,29%; população 6.211.223. População do estado do RJ: 16.055.174.

## Onde encontrar

- **SIDRA, Censo Demográfico 2022**: https://sidra.ibge.gov.br/pesquisa/censo-demografico/demografico-2022/inicial
- **Censo Demográfico 2022, características dos domicílios (universo)**: https://biblioteca.ibge.gov.br/visualizacao/periodicos/3106/cd_2022_domicilios.pdf. A publicação traz tabelas até UF; os dados municipais estão no SIDRA.
- **Censo Demográfico 2022 (página geral)**: https://www.ibge.gov.br/estatisticas/sociais/populacao/22827
- **CNES**: https://cnes.datasus.gov.br/
- **Inep, Indicadores Educacionais**: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais
- **Malha municipal do IBGE**: https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html
- **IBC (Anatel)**: link a registrar quando a base for baixada.

## Fontes consideradas e não usadas

| Fonte | Motivo |
|---|---|
| TIC Domicílios (Cetic.br) | detalhamento geográfico só até UF |
| PNAD Contínua, módulo TIC (IBGE) | detalhamento geográfico só até UF |
| SNIS / SINISA | não resposta em parte dos municípios e troca de sistema em 2024; o Censo cobre todos os municípios |
| Leitos hospitalares (CNES) | concentrados em municípios-polo, penalizariam municípios pequenos atendidos por referência regional |
| Ideb (Inep) | divulgado só em anos ímpares, sem edição de 2022 |
