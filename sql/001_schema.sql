-- Modelo dimensional do repositório analítico (seção 3.4 do artigo).
-- Executado automaticamente na primeira subida do contêiner (docker compose up).

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS analitico;

-- Dimensão conformada: ponto de encontro entre todas as fontes.
CREATE TABLE IF NOT EXISTS analitico.dim_municipio (
    codigo_municipio  CHAR(7) PRIMARY KEY CHECK (codigo_municipio ~ '^\d{7}$'),
    nome              TEXT        NOT NULL,
    uf                CHAR(2)     NOT NULL,
    regiao            TEXT        NOT NULL,
    populacao         INTEGER     NOT NULL CHECK (populacao > 0),
    porte             TEXT        NOT NULL,
    geometria         geometry(MultiPolygon, 4674)  -- SIRGAS 2000, padrão da malha do IBGE
);

CREATE TABLE IF NOT EXISTS analitico.dim_indicador (
    codigo      VARCHAR(4) PRIMARY KEY,
    nome        TEXT     NOT NULL,
    dimensao    TEXT     NOT NULL,
    fonte       TEXT     NOT NULL,
    referencia  TEXT     NOT NULL,
    unidade     TEXT     NOT NULL,
    sentido     SMALLINT NOT NULL CHECK (sentido IN (-1, 1)),
    no_iis      BOOLEAN  NOT NULL
);

-- Grão: município x indicador x ano de referência (formato longo).
CREATE TABLE IF NOT EXISTS analitico.fato_indicador_municipal (
    codigo_municipio  CHAR(7)    NOT NULL REFERENCES analitico.dim_municipio (codigo_municipio),
    codigo_indicador  VARCHAR(4) NOT NULL REFERENCES analitico.dim_indicador (codigo),
    ano_referencia    SMALLINT   NOT NULL,
    valor             DOUBLE PRECISION NOT NULL CHECK (valor >= 0),
    carregado_em      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (codigo_municipio, codigo_indicador, ano_referencia)
);

-- Visão analítica: uma coluna por indicador, base para o índice e o painel.
CREATE OR REPLACE VIEW analitico.vw_indicadores_largo AS
SELECT
    m.codigo_municipio, m.nome, m.uf, m.regiao, m.porte, m.populacao,
    MAX(f.valor) FILTER (WHERE f.codigo_indicador = 'C1') AS c1,
    MAX(f.valor) FILTER (WHERE f.codigo_indicador = 'C2') AS c2,
    MAX(f.valor) FILTER (WHERE f.codigo_indicador = 'S1') AS s1,
    MAX(f.valor) FILTER (WHERE f.codigo_indicador = 'S2') AS s2,
    MAX(f.valor) FILTER (WHERE f.codigo_indicador = 'H1') AS h1,
    MAX(f.valor) FILTER (WHERE f.codigo_indicador = 'H2') AS h2,
    MAX(f.valor) FILTER (WHERE f.codigo_indicador = 'E1') AS e1,
    MAX(f.valor) FILTER (WHERE f.codigo_indicador = 'E2') AS e2
FROM analitico.dim_municipio m
LEFT JOIN analitico.fato_indicador_municipal f
       ON f.codigo_municipio = m.codigo_municipio AND f.ano_referencia = 2022
GROUP BY m.codigo_municipio, m.nome, m.uf, m.regiao, m.porte, m.populacao;
