# Catálogo de fontes de dados

Todas as fontes são públicas e se referem a 2022, ano do Censo Demográfico. A coluna "Status" indica o que já foi conferido e o que será confirmado na prova de conceito.

| Código | Indicador | Fonte | Referência | Chave municipal | Status |
|---|---|---|---|---|---|
| C1 | Índice Brasileiro de Conectividade (IBC) | Anatel | dez. 2022 | 7 dígitos | confirmar disponibilidade da edição 2022 para download |
| C2 | Moradores em domicílios com acesso à Internet (%) | IBGE, Censo 2022 (amostra) | 2022 | 7 dígitos | a extrair |
| S1 | Moradores em domicílios abastecidos por rede geral de água (%) | IBGE, Censo 2022 (universo) | 2022 | 7 dígitos | a extrair (SIDRA) |
| S2 | Moradores em domicílios com esgotamento por rede geral, pluvial ou fossa séptica ligada à rede (%) | IBGE, Censo 2022 (universo) | 2022 | 7 dígitos | a extrair (SIDRA) |
| H1 | Unidades básicas de saúde por 10 mil habitantes | CNES (DATASUS) | competência dez. 2022 | 6 dígitos | a extrair |
| H2 | Médicos com vínculo ativo por mil habitantes | CNES (DATASUS) | competência dez. 2022 | 6 dígitos | a extrair |
| E1 | Taxa de distorção idade-série no ensino fundamental (%) | Inep, Indicadores Educacionais | 2022 | 7 dígitos | a extrair |
| E2 | Docentes do ensino fundamental com formação adequada (%) | Inep, Indicadores Educacionais | 2022 | 7 dígitos | a extrair |

Apoio: população do Censo 2022 (denominador de H1 e H2) e malha municipal digital do IBGE (mapas do painel).

## Onde encontrar

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
