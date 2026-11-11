# Catálogo de fontes de dados

Todas as fontes são públicas e se referem a 2022, ano do Censo Demográfico. A coluna "Status" indica o que já foi conferido e o que será confirmado na prova de conceito.

| Código | Indicador | Fonte | Referência | Chave municipal | Status |
|---|---|---|---|---|---|
| C1 | Índice Brasileiro de Conectividade (IBC) | Anatel | 2022 | 7 dígitos | extraído (série 2021 a 2025, ano 2022) |
| C2 | Moradores em domicílios com acesso à Internet (%) | IBGE, Censo 2022 (amostra) | 2022 | 7 dígitos | extraído (SIDRA 9942) |
| S1 | Moradores em domicílios abastecidos por rede geral de água (%) | IBGE, Censo 2022 (universo) | 2022 | 7 dígitos | extraído (SIDRA 6894) |
| S2 | Moradores em domicílios com esgotamento por rede geral, pluvial ou fossa séptica ligada à rede (%) | IBGE, Censo 2022 (universo) | 2022 | 7 dígitos | extraído (SIDRA 7555) |
| H1 | Unidades básicas de saúde por 10 mil habitantes | CNES (DATASUS) | competência dez. 2022 | 6 dígitos | extraído (ST, conferido no TabNet) |
| H2 | Médicos com vínculo ativo por mil habitantes | CNES (DATASUS) | competência dez. 2022 | 6 dígitos | extraído (PF) |
| E1 | Taxa de distorção idade-série no ensino fundamental (%) | Inep, Indicadores Educacionais | 2022 | 7 dígitos | extraído (TDI 2022) |
| E2 | Docentes do ensino fundamental com formação adequada (%) | Inep, Indicadores Educacionais | 2022 | 7 dígitos | extraído (AFD 2022) |

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

## Arquivos do Inep usados

Planilhas municipais dos Indicadores Educacionais de 2022, baixadas manualmente da página do Inep (o servidor de download não respondeu ao acesso automatizado) e colocadas em `data/bruto/inep/`. Obtidas em 11/11/2026. O código está em `src/tcc/fontes/inep.py`.

| Uso | Arquivo | Coluna | Linha usada | SHA-256 do .zip |
|---|---|---|---|---|
| E1 | `TDI_2022_MUNICIPIOS.zip` (Taxa de Distorção Idade-Série) | `FUN_CAT_0` (ensino fundamental, total) | localização Total, dependência Total | `30ca963d8accdcd7a3715e996e00720e872731d1e08491253d48304c6f263f0b` |
| E2 | `AFD_2022_MUNICIPIOS.zip` (Adequação da Formação Docente) | `FUN_CAT_1` (ensino fundamental, total, grupo 1) | localização Total, dependência Total | `ef56287e590d9e7e9b5bf3762f0bf596422b62b9bd0d6f31a66518c880503032` |

Páginas: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/taxas-de-distorcao-idade-serie e https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/adequacao-da-formacao-docente. O link direto de cada arquivo ainda não foi registrado.

Observações:

- **Integridade.** Cada .zip traz o MD5 da planilha calculado pelo Inep; o pipeline confere antes de ler.
- **Cobertura.** As duas planilhas têm os 5.570 municípios, todos com valor na linha Total/Total do ensino fundamental.
- **E2 é percentual de docências.** Pela nota da planilha, o docente é contado uma vez em cada turma e disciplina que leciona, e o grupo 1 reúne docentes com licenciatura (ou bacharelado com complementação pedagógica) na mesma área da disciplina. O texto do artigo deve descrever o indicador assim. Nota técnica citada na planilha: https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2021/SEI_INEP_0644683_Nota_Tecnica.pdf

**Conferência.** Rio de Janeiro (3304557): E1 11,0%, E2 62,0%. Sumidouro (3305703): E1 23,0%, E2 36,8%.

## Arquivos do CNES usados

Arquivos mensais do FTP do DATASUS, competência dezembro de 2022, um por UF (exemplo do RJ: `STRJ2212.dbc` e `PFRJ2212.dbc`). Acesso em 11/11/2026. O código está em `src/tcc/fontes/cnes.py`.

- Estabelecimentos (ST): ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/ST/
- Profissionais (PF): ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/PF/
- Tabelas auxiliares do TabNet (`TAB_CNES.zip`, com `TP_ESTAB.CNV` e `medico02.CNV`): ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Auxiliar/

| Indicador | Arquivo | Regra |
|---|---|---|
| H1 | ST | estabelecimentos com `TP_UNID` 01 (posto de saúde) ou 02 (centro de saúde/unidade básica), segundo `TP_ESTAB.CNV`; por 10 mil habitantes |
| H2 | PF | profissionais distintos (pelo CNS; na falta, pelo CPF codificado) com CBO iniciado em 225 ou 2231, por município do estabelecimento; por mil habitantes |

Observações:

- **CBO de médico.** O subgrupo 225 da CBO 2002 reúne os médicos; os códigos 2231 são da versão anterior e continuam em uso no SUS (por exemplo, 2231F9, médico residente). O agrupamento "Médicos" do TabNet (`medico02.CNV`, 130 códigos) está inteiramente contido nessa regra. No RJ, a regra acrescenta dois códigos que a tabela do TabNet não lista: 225355 (médico radiologista intervencionista, 145 vínculos) e 225154 (1 vínculo), de um total de 109.929 vínculos de médicos.
- **Uma vez por município.** O arquivo PF tem um registro por vínculo. O médico com vários vínculos no mesmo município conta uma vez; quem atua em dois municípios conta nos dois. No RJ: 109.929 vínculos e 48.610 médicos distintos.
- **Contagem zero.** O CNES lista todos os estabelecimentos ativos; município sem registro recebe zero, e não valor ausente.
- **Leitura do .dbc.** Bibliotecas `pyreaddbc` (descompactação) e `dbfread` (leitura do DBF).

**Conferência.** H1 conferido contra o TabNet (CNES, Estabelecimentos por Tipo, Rio de Janeiro, Dez/2022, tipos "posto de saúde" e "centro de saúde/unidade básica", por município): as contagens coincidem nos 92 municípios (2.175 no estado; 307 no município do Rio de Janeiro; 9 em Sumidouro). H2 ainda não foi conferido contra o TabNet. Valores: Rio de Janeiro, H1 0,49 e H2 4,79; Sumidouro, H1 5,92 e H2 2,89.

## Arquivo do IBC usado

Arquivo .zip do conjunto "Meu Município: Índice Brasileiro de Conectividade" do Portal Brasileiro de Dados Abertos (https://dados.gov.br/dados/conjuntos-dados/meu-municipio---indice-brasileiro-de-conectividade), baixado manualmente (a página só funciona em navegador e a API do portal exige login) e gravado como `data/bruto/anatel/ibc.zip`. Obtido em 11/11/2026; arquivos internos datados de 23/04/2026 (edição IBC 2025). SHA-256 do .zip: `c7dfe5253357d1179a2f8ce907c8f0e7cd5c1bbcce59eeee6741326198ba1752`. O código está em `src/tcc/fontes/anatel.py`.

| Uso | Arquivo interno | Coluna | Filtro |
|---|---|---|---|
| C1 | `IBC_municipios_indicadores_normalizados.csv` | `IBC` (0 a 100) | `Ano` = 2022 |

O .zip traz também os indicadores originais (não normalizados) e as tabelas por UF. A série tem 5.570 municípios em cada ano de 2021 a 2025.

**Metodologia do IBC de 2022.** A série mistura duas versões do índice, o que foi verificado nos próprios dados:

- **2021 a 2023, metodologia original:** os componentes são normalizados pelo mínimo e pelo máximo do próprio ano (diferença máxima de 0,02 ponto ao refazer a conta a partir dos valores originais) e não há componente rural (coluna vazia). Os pesos recuperados por regressão dos componentes sobre o IBC (resíduo máximo de 0,06 ponto) são: fibra 0,20; densidade de banda larga fixa 0,19; densidade móvel 0,19; cobertura 4G/5G 0,17; adensamento de estações 0,13; competitividade móvel 0,06; competitividade fixa 0,06.
- **2024 e 2025, metodologia revisada:** limites teóricos fixos na normalização e componente de conectividade rural, com os pesos da página de metodologia da Anatel.

Consequência para o trabalho: o C1 de 2022 segue a metodologia original. Como a normalização é feita dentro do próprio ano, o IBC de 2022 ordena os municípios entre si em 2022, que é o uso feito aqui (correlação de Spearman e quadrantes pela mediana); ele não deve ser comparado em nível com edições de 2024 em diante. O texto do artigo deve registrar isso.

**Mês de referência.** O arquivo informa só o ano (2022). O artigo cita dados de dezembro de 2022; isso ainda precisa ser confirmado na documentação da Anatel.

**Conferência.** A Anatel divulgou que Armação dos Búzios (RJ) teve o maior IBC do país em 2022 e em 2023 (https://www.gov.br/anatel/pt-br/assuntos/noticias/regioes-norte-e-centro-oeste-tem-os-maiores-aumentos-de-conectividade-em-2023). No arquivo, Armação dos Búzios (3300233) é o primeiro em 2022 (83,28) e em 2023 (81,94). Rio de Janeiro (3304557): 71,96; Sumidouro (3305703): 65,82.

## Onde encontrar

- **SIDRA, Censo Demográfico 2022**: https://sidra.ibge.gov.br/pesquisa/censo-demografico/demografico-2022/inicial
- **Censo Demográfico 2022, características dos domicílios (universo)**: https://biblioteca.ibge.gov.br/visualizacao/periodicos/3106/cd_2022_domicilios.pdf. A publicação traz tabelas até UF; os dados municipais estão no SIDRA.
- **Censo Demográfico 2022 (página geral)**: https://www.ibge.gov.br/estatisticas/sociais/populacao/22827
- **CNES**: https://cnes.datasus.gov.br/
- **Inep, Indicadores Educacionais**: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais
- **Malha municipal do IBGE**: https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html
- **IBC (Anatel)**: dados em https://dados.gov.br/dados/conjuntos-dados/meu-municipio---indice-brasileiro-de-conectividade; metodologia em https://www.gov.br/anatel/pt-br/regulado/universalizacao/indice-brasileiro-conectiviadade-ibc; painel em https://informacoes.anatel.gov.br/paineis/meu-municipio/indice-brasileiro-de-conectividade.

## Fontes consideradas e não usadas

| Fonte | Motivo |
|---|---|
| TIC Domicílios (Cetic.br) | detalhamento geográfico só até UF |
| PNAD Contínua, módulo TIC (IBGE) | detalhamento geográfico só até UF |
| SNIS / SINISA | não resposta em parte dos municípios e troca de sistema em 2024; o Censo cobre todos os municípios |
| Leitos hospitalares (CNES) | concentrados em municípios-polo, penalizariam municípios pequenos atendidos por referência regional |
| Ideb (Inep) | divulgado só em anos ímpares, sem edição de 2022 |
