# Amazon Sales Analytics Platform

Production-oriented analytics project for marketplace commercial performance. The repository combines batch processing, data quality controls, analytical marts, warehouse query serving, operational APIs, and execution history tracking in a single portfolio-ready codebase.

## Languages

- International: [README.md](README.md)
- PT-BR: [docs/README.pt-BR.md](docs/README.pt-BR.md)
- PT-PT: [docs/README.pt-PT.md](docs/README.pt-PT.md)

## Dataset Source

Primary source:

- Kaggle dataset: `aliiihussain/amazon-sales-dataset`
- Retrieval mechanism: `kagglehub`
- Raw landing path: `data/raw/amazon_sales/amazon_sales_dataset.csv`

The pipeline reuses the local raw dataset when it already exists and only downloads again when needed or explicitly forced.

## Why This Repository Exists

This project is designed to look and behave like a small real data platform rather than a notebook collection. It focuses on questions a revenue operations or category management team would actually ask:

- how much revenue was generated and how much was lost to discount leakage
- which categories concentrate revenue and promotional pressure
- whether the commercial trend is accelerating, stable, or declining
- where discount spikes require operational action
- how KPIs changed between the latest pipeline executions

## Platform Architecture Blueprint

```text
.
|-- .github/
|   |-- ISSUE_TEMPLATE/
|   |-- workflows/
|   `-- PULL_REQUEST_TEMPLATE.md
|-- alerts/
|   `-- discount_spike_alert.py
|-- app/
|   |-- __init__.py
|   |-- api.py
|   `-- streamlit_app.py
|-- assets/
|-- contracts/
|   |-- product_metrics.contract.json
|   `-- sales_dataset.contract.json
|-- data/
|   |-- processed/
|   `-- ... runtime layers created from config
|-- docs/
|   |-- README.en.md
|   |-- README.pt-BR.md
|   |-- README.pt-PT.md
|   `-- REPOSITORY_STRUCTURE.md
|-- notebooks/
|-- reports/
|-- scripts/
|   |-- bump_version.py
|   |-- run_alerts.py
|   |-- run_pipeline.py
|   `-- run_scenario_simulator.py
|-- sql/
|   |-- gold_commercial_mart.sql
|   `-- warehouse_validation.sql
|-- src/amazon_sales_analysis/
|   |-- cli/
|   |-- ingestion/
|   |-- observability/
|   |-- pipelines/
|   |-- serving/
|   |-- transformations/
|   |-- validation/
|   |-- config.py
|   |-- operations.py
|   |-- analytics.py
|   |-- anomaly_detection.py
|   |-- business_metrics.py
|   |-- decision_engine.py
|   |-- eda.py
|   |-- evaluation.py
|   |-- feature_engineering.py
|   |-- insights.py
|   |-- modeling.py
|   |-- sales_analysis.py
|   |-- scenario_simulator.py
|   |-- table_organization.py
|   |-- visualization.py
|   |-- contracts.py              # compatibility shim
|   |-- data_ingestion.py         # compatibility shim
|   |-- data_preprocessing.py     # compatibility shim
|   |-- logging_config.py         # compatibility shim
|   |-- metrics.py                # compatibility shim
|   |-- quality.py                # compatibility shim
|   |-- run_history.py            # compatibility shim
|   |-- warehouse.py              # compatibility shim
|   `-- warehouse_service.py      # compatibility shim
|-- tests/
|-- CHANGELOG.md
|-- CONTRIBUTING.md
|-- Dockerfile
|-- Makefile
|-- main.py
`-- pyproject.toml
```

Detailed structure and placement rules: [docs/REPOSITORY_STRUCTURE.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/REPOSITORY_STRUCTURE.md)

The package now follows a domain-oriented layout. New code should target the dedicated subpackages and use the top-level modules only when backward compatibility is required.

## Data Flow

1. Download or reuse the raw dataset in `data/raw/amazon_sales/`
2. Persist a bronze snapshot for the current run
3. Validate the raw contract and schema
4. Clean, normalize, deduplicate, and enforce quality gates
5. Persist the silver snapshot and the processed dataset
6. Build features and publish the gold mart snapshot
7. Materialize the warehouse layer in DuckDB when available
8. Export tables, alerts, metrics, and figures
9. Write `reports/runs/<run_id>/execution_manifest.json`
10. Expose metrics and warehouse queries through API and CLI surfaces

## Core Application Surfaces

API:

- `GET /health`
- `GET /health/ready`
- `GET /metrics/summary`
- `GET /metrics/opportunities`
- `GET /alerts/discount-spikes`
- `GET /warehouse/category-revenue`
- `GET /pipeline/runs`
- `GET /pipeline/runs/compare-latest`
- `GET /operations/latest`

CLI:

```bash
amazon-sales-pipeline
amazon-sales-pipeline --force-download
amazon-sales-pipeline --fail-on-kpi-regression
amazon-sales-alerts
amazon-sales-scenario
amazon-sales-warehouse --export-category-revenue
amazon-sales-warehouse --show-run-history
amazon-sales-warehouse --compare-latest-runs
amazon-sales-warehouse --show-operational-summary
```

## Runtime Layers

Configured through `src/amazon_sales_analysis/config.py`:

- `data/raw/`
- `data/bronze/`
- `data/silver/`
- `data/gold/`
- `data/warehouse/`
- `data/processed/`
- `reports/figures/`
- `reports/tables/`
- `reports/metrics/`
- `reports/runs/`

## Package Taxonomy

- `ingestion/`
  Raw dataset acquisition and landing logic.
- `transformations/`
  Dataset loading, cleaning, normalization, deduplication, and processed outputs.
- `validation/`
  Raw contracts, schema enforcement, and clean-data quality gates.
- `observability/`
  Logging, KPI packaging, and regression-baseline controls.
- `serving/`
  Warehouse materialization, query services, run history, and operational summaries.
- `pipelines/`
  Shared runtime utilities for artifacts and execution manifests.

Compatibility layer:

- Top-level modules such as `data_ingestion.py`, `metrics.py`, `warehouse.py`, and `quality.py` remain available as stable import shims for existing callers.

Shim policy:

- New code should import from the domain packages, not from the compatibility shims.
- Compatibility shims exist to preserve existing callers and test surfaces during package evolution.
- Any new public symbol added to a shim must be re-exported explicitly and covered by contract tests.

## Quality Workflow

```bash
make quality
make test
make build-check
```

Validation stack:

- `black`
- `isort`
- `ruff`
- `mypy`
- `pytest`
- `python -m build`
- GitHub Actions CI

## Repository Standards

- Keep business logic in `src/amazon_sales_analysis/`, not in notebooks or scripts
- Treat exported data artifacts as generated outputs, not source-controlled assets
- Prefer deterministic, testable transformations over ad hoc analysis code
- Keep API and CLI surfaces thin and reusable
- Document operational trade-offs explicitly

## Trade-offs

- No external scheduler or orchestrator
- No centralized telemetry or alerting backend
- DuckDB is local and optional, not a distributed warehouse
- Run history is derived from local manifests instead of a remote metadata store
- Operational summary is local-file based rather than backed by a metadata service

## Documentation

- Structure guide: [docs/REPOSITORY_STRUCTURE.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/REPOSITORY_STRUCTURE.md)
- International overview: [docs/README.en.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/README.en.md)
- PT-BR overview: [docs/README.pt-BR.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/README.pt-BR.md)
- PT-PT overview: [docs/README.pt-PT.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/README.pt-PT.md)

## Contact

- GitHub: https://github.com/samuelmaia-analytics
- LinkedIn: https://linkedin.com/in/samuelmaia-analytics
