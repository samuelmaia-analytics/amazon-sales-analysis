# Amazon Sales Analytics Pipeline (International)

## Language Switch
- Main README: [../README.md](../README.md)
- PT-BR: [README.pt-BR.md](README.pt-BR.md)

## Summary

This repository is no longer just a notebook-style sales analysis. It is a small but production-oriented analytics system with:

- raw-to-bronze/silver/gold data layers
- schema contracts and quality gates
- run manifests with lineage, hashes, and dataset profiles
- optional DuckDB materialization for the gold mart
- FastAPI endpoints for metrics, alerts, warehouse queries, and run-history comparison
- readiness checks for processed data and analytical query availability
- CLI entry points for pipeline, alerts, scenarios, and warehouse operations

## What It Solves

The project is designed to answer recurring commercial questions such as:

- how much revenue was generated and how much was lost to discount leakage
- which categories concentrate revenue and promotional pressure
- whether monthly momentum is accelerating or declining
- where discount spikes require operational follow-up
- how KPIs changed between the latest pipeline runs

## Architecture Snapshot

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

Core modules:

- `config.py`: environment-aware settings
- `data_ingestion.py`: raw dataset retrieval/reuse
- `data_preprocessing.py`: cleaning, normalization, deduplication
- `quality.py`: quality gates including freshness and business-key uniqueness
- `warehouse.py`: DuckDB mart materialization
- `warehouse_service.py`: query-serving with DuckDB-or-CSV fallback
- `run_history.py`: run summary and KPI drift comparison

## Run

```bash
python -m pip install -e .[dev]
amazon-sales-pipeline
```

Additional entry points:

```bash
amazon-sales-alerts
amazon-sales-scenario
amazon-sales-warehouse
uvicorn app.api:app --reload
streamlit run app/streamlit_app.py
```

## Warehouse Queries

Export category revenue:

```bash
amazon-sales-warehouse --export-category-revenue
```

Inspect run history:

```bash
amazon-sales-warehouse --show-run-history
amazon-sales-warehouse --compare-latest-runs
```

API endpoints:

- `GET /metrics/summary`
- `GET /alerts/discount-spikes`
- `GET /warehouse/category-revenue`
- `GET /pipeline/runs`
- `GET /pipeline/runs/compare-latest`
- `GET /health/ready`

## Engineering Characteristics

- Idempotent outputs for main artifacts
- Atomic writes for critical CSV/JSON artifacts
- Local raw dataset reuse for reprocessing
- Quality checks for domains, freshness, and business-key uniqueness
- Per-run manifests with hashes, row counts, and dataset profiles
- Optional local warehouse with versioned SQL assets
- KPI drift comparison across recent runs
- Drift severity classification (`stable`, `medium`, `high`, `critical`)

## Quality Commands

```bash
make quality
make test
```

## Validation Status

Current repository validation includes:

- `ruff check .`
- `mypy src tests app alerts scripts`
- `pytest`

## Trade-offs

- No external orchestrator or centralized observability stack
- DuckDB is local and optional, not a distributed warehouse
- Run history is based on local manifests rather than remote telemetry

## Contact

- GitHub: https://github.com/samuelmaia-analytics
- LinkedIn: https://linkedin.com/in/samuelmaia-analytics
