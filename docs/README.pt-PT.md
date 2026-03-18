# Amazon Sales Analytics Platform (PT-PT)

## Selecao de Idioma

- International: [../README.md](../README.md)
- PT-BR: [README.pt-BR.md](README.pt-BR.md)
- PT-PT: [README.pt-PT.md](README.pt-PT.md)
- Contribuicao: [../CONTRIBUTING.md](../CONTRIBUTING.md)
- Guia de estrutura: [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md)

## Resumo

Este repositorio deixou de ser apenas uma analise exploratoria de vendas. Hoje funciona como um sistema analitico pequeno, mas orientado para producao, com:

- camadas `raw`, `bronze`, `silver` e `gold`
- contratos de schema e quality gates
- manifests de execucao com lineage, hashes e perfil de dataset
- materializacao opcional do mart em DuckDB
- endpoints FastAPI para metricas, alertas, consultas analiticas e comparacao entre execucoes
- checks de readiness para dataset processado e disponibilidade da camada analitica
- CLIs para pipeline, alertas, cenarios e operacoes de warehouse

## Fonte do Dataset

- Dataset Kaggle: `aliiihussain/amazon-sales-dataset`
- Download via `kagglehub`
- Caminho bruto local: `data/raw/amazon_sales/amazon_sales_dataset.csv`

## O Que o Projeto Resolve

O projeto foi estruturado para responder a perguntas recorrentes de operacao comercial, como:

- quanto revenue foi gerado e quanto foi perdido por leakage de desconto
- que categorias concentram receita e pressao promocional
- se a tendencia mensal esta a acelerar ou a cair
- onde existem spikes de desconto que exigem acao
- como os KPIs mudaram entre a ultima execucao e a anterior

## Visao da Arquitetura

```text
data/
|-- raw/
|-- bronze/
|-- silver/
|-- gold/
`-- warehouse/

reports/
|-- tables/
|-- metrics/
|-- figures/
`-- runs/<run_id>/execution_manifest.json
```

Pacotes de dominio:

- `ingestion/`: aquisicao do dataset bruto e reutilizacao da camada local
- `transformations/`: leitura, limpeza, normalizacao e outputs processados
- `validation/`: contratos, schema checks e quality gates
- `observability/`: logging, empacotamento de KPIs e controlo de regressao
- `serving/`: materializacao do warehouse, query services, historico de runs e operational summaries
- `pipelines/`: utilitarios de runtime para artefactos e manifests

Politica de shims:

- Modulos de topo como `data_ingestion.py`, `metrics.py` e `warehouse.py` sao shims explicitos de compatibilidade.
- O novo codigo deve importar a partir dos pacotes de dominio.
- Os exports dos shims sao mantidos de forma estavel e validados por testes de contrato de distribuicao.

## Como Executar

```bash
python -m pip install -e .[dev]
amazon-sales-pipeline
amazon-sales-pipeline --force-download
amazon-sales-pipeline --fail-on-kpi-regression
```

Entrypoints adicionais:

```bash
amazon-sales-alerts
amazon-sales-scenario
amazon-sales-warehouse
uvicorn app.api:app --reload
streamlit run app/streamlit_app.py
```

## Consultas de Warehouse

```bash
amazon-sales-warehouse --export-category-revenue
amazon-sales-warehouse --show-run-history
amazon-sales-warehouse --compare-latest-runs
amazon-sales-warehouse --show-operational-summary
```

Endpoints disponiveis:

- `GET /metrics/summary`
- `GET /alerts/discount-spikes`
- `GET /warehouse/category-revenue`
- `GET /pipeline/runs`
- `GET /pipeline/runs/compare-latest`
- `GET /operations/latest`
- `GET /health/ready`

## Caracteristicas de Engenharia

- Saidas idempotentes para os principais artefactos
- Escrita atomica para CSVs e JSONs criticos
- Reutilizacao do dataset bruto local para reprocessamento
- Validacoes de dominio, freshness e unicidade de chave de negocio
- Manifest por execucao com hashes, contagem de linhas e perfil dos datasets
- Warehouse local opcional com SQL versionado
- Comparacao de drift de KPIs entre execucoes recentes
- Classificacao de severidade de drift (`stable`, `medium`, `high`, `critical`)

## Comandos de Qualidade

```bash
make quality
make test
make build-check
```

## Estado de Validacao

O repositorio e validado com:

- `ruff check .`
- `mypy src tests app alerts scripts`
- `pytest`
- `python -m build --sdist --wheel`

## Trade-offs

- Nao existe orquestrador externo nem observabilidade centralizada
- O DuckDB e local e opcional, nao um warehouse distribuido
- O historico de runs e baseado em manifests locais, nao em telemetria remota

## Automacao

- Pull requests e pushes executam lint, type checks, testes e validacao de build
- Tags de release repetem a mesma quality gate antes da publicacao
- O CI pode ser agendado para validacao recorrente mesmo sem novos commits
