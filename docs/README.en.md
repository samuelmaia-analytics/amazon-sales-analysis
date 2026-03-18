# Amazon Sales Analytics Platform (International)

## Language Switch

- International: [../README.md](../README.md)
- PT-BR: [README.pt-BR.md](README.pt-BR.md)
- PT-PT: [README.pt-PT.md](README.pt-PT.md)
- Contributing: [../CONTRIBUTING.md](../CONTRIBUTING.md)
- Structure guide: [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md)

## Summary

This repository is no longer just a notebook-style sales analysis. It is a small but production-oriented analytics system with:

- raw-to-bronze/silver/gold data layers
- schema contracts and quality gates
- run manifests with lineage, hashes, and dataset profiles
- optional DuckDB materialization for the gold mart
- FastAPI endpoints for metrics, alerts, warehouse queries, and run-history comparison
- readiness checks for processed data and analytical query availability
- CLI entry points for pipeline, alerts, scenarios, and warehouse operations

## Dataset Source

- Kaggle dataset: `aliiihussain/amazon-sales-dataset`
- Downloaded through `kagglehub`
- Raw landing path: `data/raw/amazon_sales/amazon_sales_dataset.csv`

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

Domain packages:

- `ingestion/`: raw dataset acquisition and local landing reuse
- `transformations/`: loading, cleaning, normalization, and processed outputs
- `validation/`: contracts, schema checks, and quality gates
- `observability/`: logging, KPI packaging, and regression controls
- `serving/`: warehouse materialization, query services, run history, and operational summaries
- `pipelines/`: artifact and manifest runtime helpers

Compatibility policy:

- Top-level modules such as `data_ingestion.py`, `metrics.py`, and `warehouse.py` are explicit compatibility shims.
- New code should import from the domain packages.
- Shim exports are kept stable and validated by distribution contract tests.

## Run

```bash
python -m pip install -e .[dev]
amazon-sales-pipeline
amazon-sales-pipeline --force-download
amazon-sales-pipeline --fail-on-kpi-regression
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

```bash
amazon-sales-warehouse --export-category-revenue
amazon-sales-warehouse --show-run-history
amazon-sales-warehouse --compare-latest-runs
amazon-sales-warehouse --show-operational-summary
```

API endpoints:

- `GET /metrics/summary`
- `GET /alerts/discount-spikes`
- `GET /warehouse/category-revenue`
- `GET /pipeline/runs`
- `GET /pipeline/runs/compare-latest`
- `GET /operations/latest`
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
make build-check
```

## Validation Status

Current repository validation includes:

- `ruff check .`
- `mypy src tests app alerts scripts`
- `pytest`
- `python -m build --sdist --wheel`

## Trade-offs

- No external orchestrator or centralized observability stack
- DuckDB is local and optional, not a distributed warehouse
- Run history is based on local manifests rather than remote telemetry

## Automation

- Pull requests and pushes run lint, type checks, tests, and package build validation
- Release tags re-run the same quality gate before publishing
- CI can be scheduled to provide recurring validation even without new commits
