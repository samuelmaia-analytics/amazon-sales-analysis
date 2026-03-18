# Amazon Sales Analytics Pipeline (PT-BR)

## Troca de Idioma
- README principal: [../README.md](../README.md)
- International: [README.en.md](README.en.md)

## Resumo

Este repositório deixou de ser apenas uma análise exploratória de vendas. Hoje ele funciona como um sistema analítico pequeno, mas orientado a produção, com:

- camadas `raw`, `bronze`, `silver` e `gold`
- contratos de schema e quality gates
- manifests de execução com lineage, hashes e perfil de dataset
- materialização opcional do mart em DuckDB
- endpoints FastAPI para métricas, alertas, consultas analíticas e comparação entre execuções
- checks de readiness para dataset processado e disponibilidade da camada analítica
- CLIs para pipeline, alertas, cenários e operações de warehouse

## O Que o Projeto Resolve

O projeto foi estruturado para responder perguntas recorrentes de operação comercial, como:

- quanto revenue foi gerado e quanto foi perdido por leakage de desconto
- quais categorias concentram receita e pressão promocional
- se a tendência mensal está acelerando ou caindo
- onde existem spikes de desconto que exigem ação
- como os KPIs mudaram entre a última execução e a anterior

## Visão de Arquitetura

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

Módulos centrais:

- `config.py`: configuração por ambiente
- `data_ingestion.py`: obtenção/reuso da camada bruta
- `data_preprocessing.py`: limpeza, normalização e deduplicação
- `quality.py`: quality gates com freshness e unicidade de chave de negócio
- `warehouse.py`: materialização do mart em DuckDB
- `warehouse_service.py`: serving de consultas com fallback DuckDB-ou-CSV
- `run_history.py`: histórico de execuções e comparação de drift de KPIs

## Como Executar

```bash
python -m pip install -e .[dev]
amazon-sales-pipeline
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

Exportar receita por categoria:

```bash
amazon-sales-warehouse --export-category-revenue
```

Inspecionar histórico de runs:

```bash
amazon-sales-warehouse --show-run-history
amazon-sales-warehouse --compare-latest-runs
```

Endpoints disponíveis:

- `GET /metrics/summary`
- `GET /alerts/discount-spikes`
- `GET /warehouse/category-revenue`
- `GET /pipeline/runs`
- `GET /pipeline/runs/compare-latest`
- `GET /health/ready`

## Características de Engenharia

- Saídas idempotentes para os principais artefatos
- Escrita atômica para CSVs e JSONs críticos
- Reuso do dataset bruto local para reprocessamento
- Validações de domínio, freshness e unicidade de chave de negócio
- Manifest por execução com hashes, contagem de linhas e perfil dos datasets
- Warehouse local opcional com SQL versionado
- Comparação de drift de KPIs entre execuções recentes
- Classificação de severidade de drift (`stable`, `medium`, `high`, `critical`)

## Comandos de Qualidade

```bash
make quality
make test
```

## Status de Validação

O repositório é validado com:

- `ruff check .`
- `mypy src tests app alerts scripts`
- `pytest`

## Trade-offs

- Não há orquestrador externo nem observabilidade centralizada
- O DuckDB é local e opcional, não um warehouse distribuído
- O histórico de runs é baseado em manifests locais, não em telemetry remota

## Contato

- GitHub: https://github.com/samuelmaia-analytics
- LinkedIn: https://linkedin.com/in/samuelmaia-analytics
