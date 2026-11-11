# Modelo de dados

Modelagem dimensional (Kimball e Ross, 2013). O município é a dimensão conformada que liga todas as fontes. O DDL está em [`sql/001_schema.sql`](../sql/001_schema.sql).

```mermaid
erDiagram
    dim_municipio ||--o{ fato_indicador_municipal : "codigo_municipio"
    dim_indicador ||--o{ fato_indicador_municipal : "codigo_indicador"

    dim_municipio {
        char7 codigo_municipio PK
        text nome
        char2 uf
        text regiao
        int populacao
        text porte
        geometry geometria
    }
    dim_indicador {
        varchar codigo PK
        text nome
        text dimensao
        text fonte
        text referencia
        text unidade
        smallint sentido
        bool no_iis
    }
    fato_indicador_municipal {
        char7 codigo_municipio PK, FK
        varchar codigo_indicador PK, FK
        smallint ano_referencia PK
        float valor
        timestamptz carregado_em
    }
```

**Grão da tabela de fatos:** município x indicador x ano de referência. O formato longo permite incluir indicadores sem alterar o esquema. A visão `analitico.vw_indicadores_largo` organiza os indicadores em colunas para o cálculo do índice e para o painel.

## Camadas do pipeline

```mermaid
flowchart LR
    subgraph bruta[Camada bruta]
        A1[Censo 2022]
        A2[IBC Anatel]
        A3[CNES]
        A4[Inep]
    end
    subgraph padronizada[Camada padronizada]
        P[fato_fonte.csv<br/>chave de 7 dígitos]
    end
    subgraph analitica[Camada analítica]
        F[fato_indicador_municipal]
        I[IIS e subíndices]
        S[sensibilidade]
        Q[quadrantes]
    end
    A1 & A2 & A3 & A4 --> P --> F --> I --> Q
    F --> S
    Q --> D[Painel Streamlit]
```
