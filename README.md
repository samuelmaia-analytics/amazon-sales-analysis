# Amazon Sales Analytics Pipeline

Pipeline analitico em Python para monitoramento de performance comercial de marketplace. O projeto foi estruturado como um sistema de dados pequeno, mas com preocupacoes reais de engenharia: camadas de ingestao e transformacao, quality gates, contratos de dados, artefatos versionados por execucao, testes e automacao de qualidade.

## Business value

O foco do repositório nao e apenas explorar um CSV. Ele responde perguntas operacionais que um time comercial ou de revenue operations realmente faria:

- quanto revenue foi gerado e quanto foi perdido por desconto
- quais categorias concentram receita e pressao promocional
- se a tendencia mensal esta acelerando, estavel ou em queda
- onde existem alertas de spike de desconto
- quais recomendacoes acionaveis podem entrar no rito semanal

## Arquitetura

```text
src/amazon_sales_analysis/
|-- cli/                    # pontos de entrada de pipeline, alertas e simulacao
|-- pipelines/runtime.py    # contexto de execucao e escrita atomica de artefatos
|-- config.py               # configuracao por ambiente via variaveis e .env
|-- data_ingestion.py       # obtencao/reuso da camada raw
|-- data_preprocessing.py   # leitura, limpeza e persistencia da camada clean
|-- contracts.py            # contrato do dataset bruto
|-- quality.py              # quality gates da camada tratada
|-- feature_engineering.py  # features derivadas
|-- sales_analysis.py       # metricas e tabelas de negocio
|-- anomaly_detection.py    # alertas operacionais
|-- decision_engine.py      # recomendacoes acionaveis
|-- metrics.py              # pacote consolidado de KPIs
`-- visualization.py        # artefatos visuais
```

## Fluxo de dados

1. `data/raw/amazon_sales/amazon_sales_dataset.csv`
2. snapshot bronze por execucao em `data/bronze/`
3. validacao de contrato e schema
4. limpeza, deduplicacao, normalizacao e quality gates
5. snapshot silver em `data/silver/`
6. enriquecimento analitico e publicacao do mart gold em `data/gold/`
7. materializacao opcional do mart consultavel em DuckDB em `data/warehouse/amazon_sales.duckdb`
8. exportacao de tabelas, metricas, alertas e visuais
9. geracao de `reports/runs/<run_id>/execution_manifest.json` com hashes, perfis e lineage do batch

## Confiabilidade implementada

- Reprocessamento: o pipeline reusa o dataset bruto local quando ele ja existe.
- Idempotencia de saida: os artefatos principais sao regravados de forma deterministica nos mesmos destinos.
- Escrita mais segura: CSVs/JSONs criticos usam escrita atomica para reduzir risco de artefato parcial.
- Observabilidade: logs incluem `environment` e `run_id`.
- Rastreabilidade: cada execucao gera um manifest com entradas, saidas, hashes SHA-256 e perfis de dataset.
- Governanca de qualidade: freshness, unicidade de chave de negocio e quality summary exportado.
- Camadas de dados: bronze, silver e gold ficam explicitas para facilitar reprocessamento e storytelling tecnico.
- Warehouse local: quando `duckdb` esta disponivel, o gold tambem vira uma tabela consultavel com SQL versionado.
- Serving analitico: a API expõe consultas do mart e a CLI `amazon-sales-warehouse` exporta resultados do warehouse para consumo externo.
- Observabilidade entre execuções: manifests e métricas permitem listar runs recentes e comparar drift de KPIs entre batches.
- Readiness operacional: a API expõe checks simples para dataset processado e camada de consulta analítica.

## Stack

- Python 3.12+
- pandas
- pandera
- duckdb
- FastAPI
- Streamlit
- pytest
- black, isort, ruff, mypy
- GitHub Actions

## Como executar

### 1. Instalar dependencias

```bash
python -m pip install -e .[dev]
```

### 2. Configurar ambiente

Use `.env.example` como base para um `.env` local.

Variaveis principais:

- `AMAZON_SALES_ENV`: ambiente logico (`dev`, `staging`, `prod`)
- `AMAZON_SALES_LOG_LEVEL`: nivel de log
- `AMAZON_SALES_ENABLE_DOWNLOAD`: habilita download do dataset
- `AMAZON_SALES_DATA_DIR`: diretório base de dados
- `AMAZON_SALES_REPORTS_DIR`: diretório base de artefatos
- `AMAZON_SALES_MAX_DATA_STALENESS_DAYS`: limite de obsolescencia aceito no quality gate

### 3. Rodar o pipeline

```bash
python main.py
```

Ou pelo entry point:

```bash
amazon-sales-pipeline
```

### 4. Rodar utilitarios operacionais

```bash
amazon-sales-alerts
amazon-sales-scenario
amazon-sales-warehouse
streamlit run app/streamlit_app.py
```

### Consultar o warehouse

```bash
amazon-sales-warehouse --export-category-revenue
```

Endpoint disponível:

- `GET /warehouse/category-revenue`
- `GET /pipeline/runs`
- `GET /pipeline/runs/compare-latest`
- `GET /health/ready`

Consultas operacionais pela CLI:

```bash
amazon-sales-warehouse --show-run-history
amazon-sales-warehouse --compare-latest-runs
```

O diff entre runs classifica drift por severidade (`stable`, `medium`, `high`, `critical`).

## Qualidade local

```bash
make quality
make test
```

## Testes

A suíte cobre:

- contrato do dado bruto
- limpeza e normalizacao
- quality gates
- metricas de negocio
- alertas
- runtime operacional do pipeline
- configuracao por ambiente

## CI/CD

O workflow em [`.github/workflows/ci.yml`](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/.github/workflows/ci.yml) executa:

- format checks com `black` e `isort`
- lint com `ruff`
- type check com `mypy`
- testes com cobertura

## Decisoes tecnicas

- O projeto manteve `pandas` em vez de migrar artificialmente para Spark. Para o volume e o objetivo de portfolio, isso preserva simplicidade sem sacrificar clareza.
- A configuracao foi centralizada em `config.py` com suporte a `.env`, evitando hardcodes de caminho e ambiente.
- O pipeline continua pequeno, mas ganhou camadas bronze/silver/gold, manifest de execucao rico e logging contextual para parecer e operar como um job real.
- O mart em DuckDB e opcional por design: o pipeline nao quebra em ambientes sem o engine, mas deixa os artefatos SQL e o status de materializacao registrados.
- O consumo do warehouse usa fallback para snapshot gold quando o DuckDB nao esta presente, preservando usabilidade local sem esconder a diferenca de capacidade.
- O historico de runs e baseado em manifests locais; ele e suficiente para portfolio e troubleshooting local, mas nao substitui telemetry centralizada.
- A estrutura nao foi quebrada em dezenas de subpacotes artificiais. Foram adicionadas apenas abstrações com efeito operacional mensuravel.

## Trade-offs

- Nao ha orquestrador externo, scheduler ou warehouse real.
- O download do Kaggle continua sendo dependente de credenciais locais quando necessario.
- A validacao ainda e centrada em `pandas` e `pandera`, nao em um motor de qualidade mais completo como Great Expectations.
- O warehouse local ainda e single-node e atende mais ao objetivo de portfolio e reproducibilidade do que a concorrencia de workloads reais.

## Roadmap

- persistencia em DuckDB ou warehouse local para analytics reproducivel
- testes de regressao de metricas
- particionamento de artefatos e manifests por data de processamento
- deploy do app e publicacao de releases com changelog automatizado
