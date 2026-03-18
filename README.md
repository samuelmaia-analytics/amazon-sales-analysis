# Amazon Sales Analytics Platform

Production-oriented analytics platform for marketplace commercial performance. This repository is structured as a compact but credible data system: ingestion, layered transformations, contract enforcement, quality gates, KPI regression controls, analytical serving, run history, and operational visibility.

## Languages

- International: [README.md](README.md)
- PT-BR: [docs/README.pt-BR.md](docs/README.pt-BR.md)
- PT-PT: [docs/README.pt-PT.md](docs/README.pt-PT.md)

## Business Value

The platform is designed to answer recurring commercial questions that revenue, category, and operations teams actually care about:

- where revenue is concentrated and where discount leakage is growing
- which categories require action because of discount spikes
- whether the latest commercial KPIs are stable or drifting
- whether the current run produced trustworthy outputs
- how analytical data can be consumed consistently through API, CLI, and dashboard surfaces

## Dataset Source

- Source dataset: `aliiihussain/amazon-sales-dataset` on Kaggle
- Retrieval package: `kagglehub`
- Raw landing path: `data/raw/amazon_sales/amazon_sales_dataset.csv`

The ingestion layer reuses the local raw file when present and downloads again only when the file is missing or a forced refresh is requested.

## Why This Repository Exists

The goal is not to present a notebook collection with polished charts. The goal is to show the shape of a small real data platform:

- reproducible batch execution
- layered artifacts with operational traceability
- contract and quality enforcement
- analytical serving through multiple surfaces
- documentation and contribution standards that scale beyond a single author

## Architecture Blueprint

```text
.
|-- .github/
|   |-- ISSUE_TEMPLATE/
|   |-- workflows/
|   |-- CODEOWNERS
|   `-- PULL_REQUEST_TEMPLATE.md
|-- alerts/
|   `-- discount_spike_alert.py
|-- app/
|   |-- api.py
|   `-- streamlit_app.py
|-- assets/
|   |-- amazon_logo.svg
|   `-- custom.css
|-- contracts/
|   |-- product_metrics.contract.json
|   `-- sales_dataset.contract.json
|-- data/
|   |-- raw/
|   |-- bronze/
|   |-- silver/
|   |-- gold/
|   |-- warehouse/
|   `-- processed/
|-- docs/
|   |-- README.en.md
|   |-- README.pt-BR.md
|   |-- README.pt-PT.md
|   `-- REPOSITORY_STRUCTURE.md
|-- notebooks/
|-- reports/
|   |-- figures/
|   |-- metrics/
|   |-- runs/
|   `-- tables/
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
|   |-- analytics.py
|   |-- anomaly_detection.py
|   |-- business_metrics.py
|   |-- config.py
|   |-- decision_engine.py
|   |-- eda.py
|   |-- evaluation.py
|   |-- feature_engineering.py
|   |-- insights.py
|   |-- modeling.py
|   |-- operations.py
|   |-- sales_analysis.py
|   |-- scenario_simulator.py
|   |-- table_organization.py
|   |-- visualization.py
|   |-- contracts.py
|   |-- data_ingestion.py
|   |-- data_preprocessing.py
|   |-- logging_config.py
|   |-- metrics.py
|   |-- quality.py
|   |-- run_history.py
|   |-- warehouse.py
|   `-- warehouse_service.py
|-- tests/
|-- .env.example
|-- CHANGELOG.md
|-- CONTRIBUTING.md
|-- Dockerfile
|-- Makefile
|-- main.py
`-- pyproject.toml
```

Placement rules and ownership model: [docs/REPOSITORY_STRUCTURE.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/REPOSITORY_STRUCTURE.md)

## Data Flow

1. Reuse or download the raw Kaggle dataset into `data/raw/amazon_sales/`.
2. Register a new `run_id` and initialize runtime metadata.
3. Persist bronze snapshots for the execution.
4. Validate raw schema and contract expectations.
5. Clean, normalize, and deduplicate the dataset into silver outputs.
6. Publish the processed dataset and analytical gold outputs.
7. Evaluate quality gates and KPI regression against the stored baseline.
8. Materialize the local DuckDB warehouse when available.
9. Persist manifests, run status, metrics, and operational artifacts under `reports/runs/<run_id>/`.
10. Serve curated data through FastAPI, Streamlit, and CLI entry points.

## Package Taxonomy

- `ingestion/`
  Raw acquisition and landing.
- `transformations/`
  Cleaning, normalization, deduplication, and processed outputs.
- `validation/`
  Contracts, schema checks, and quality gates.
- `observability/`
  Logging, metrics packaging, and KPI regression controls.
- `serving/`
  Warehouse materialization, warehouse access, run history, and operational summaries.
- `pipelines/`
  Shared runtime helpers for artifacts, manifests, and status tracking.

## Execution Surfaces

### CLI

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

### API

- `GET /health`
- `GET /health/ready`
- `GET /metrics/summary`
- `GET /metrics/opportunities`
- `GET /alerts/discount-spikes`
- `GET /warehouse/category-revenue`
- `GET /pipeline/runs`
- `GET /pipeline/runs/compare-latest`
- `GET /operations/latest`

### Dashboard

The Streamlit app exposes both analytical and operational visibility, including commercial KPIs, category breakdowns, run status, quality gate summaries, and recent run comparisons.

## Runtime and Reliability

Configured through [`src/amazon_sales_analysis/config.py`](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/src/amazon_sales_analysis/config.py):

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

Operational guarantees already implemented:

- deterministic artifact layout by `run_id`
- explicit raw refresh control
- manifest and run-status persistence
- quality gates over the curated dataset
- KPI regression checks against a persisted baseline
- optional warehouse materialization with validation output

## Technology Stack

- Python
- pandas
- FastAPI
- Streamlit
- DuckDB
- pytest
- mypy
- ruff
- black
- isort
- pre-commit
- GitHub Actions

## Local Setup

```bash
python -m pip install -e .[dev]
pre-commit install
cp .env.example .env
```

Run the main workflow:

```bash
amazon-sales-pipeline
```

Run the service surfaces:

```bash
uvicorn app.api:app --reload
streamlit run app/streamlit_app.py
```

## Validation Workflow

```bash
make quality
make test
make build-check
```

Validation stack:

- `black --check .`
- `isort --check-only .`
- `ruff check .`
- `mypy src tests app alerts scripts`
- `pytest -q`
- `python -m build --sdist --wheel`

## Compatibility Policy

The root package still exposes compatibility modules such as `data_ingestion.py`, `quality.py`, `warehouse.py`, and `metrics.py`.

- New code should import from the domain packages.
- Compatibility modules exist to protect current callers during package evolution.
- Shim exports must remain explicit and covered by tests.
- If a shim is deprecated in the future, the deprecation must be documented before removal.

## Engineering Decisions

- The repository keeps orchestration local and explicit instead of pretending to be a full orchestration platform.
- DuckDB is optional because the project must remain runnable without external infrastructure.
- Operational history is stored in local artifacts because the objective is credible reproducibility, not artificial cloud complexity.
- API, CLI, and dashboard layers stay thin and rely on shared package logic to prevent divergent behavior.

## Trade-offs

- No external scheduler or orchestrator
- No centralized telemetry backend
- No cloud object storage or remote metadata store
- No fully incremental warehouse strategy yet
- No external alert dispatch beyond local operational artifacts

## Roadmap

- Introduce lightweight scheduled execution with retention rules.
- Expand regression coverage from KPIs to curated output snapshots.
- Strengthen warehouse materialization with incremental history semantics.
- Add external telemetry and alert routing only when infrastructure scope is justified.

## Repository Standards

- Keep reusable logic in `src/amazon_sales_analysis/`, not in notebooks or scripts.
- Treat `data/` and `reports/` as runtime artifact locations, not primary source code.
- Keep API, CLI, and dashboard surfaces thin.
- Document operational trade-offs explicitly.
- Update structure and contribution docs when repository topology changes.

## Documentation

- Contribution guide: [CONTRIBUTING.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/CONTRIBUTING.md)
- Structure guide: [docs/REPOSITORY_STRUCTURE.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/REPOSITORY_STRUCTURE.md)
- International overview: [docs/README.en.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/README.en.md)
- PT-BR overview: [docs/README.pt-BR.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/README.pt-BR.md)
- PT-PT overview: [docs/README.pt-PT.md](/C:/Users/samue/PycharmProjects/amazon-sales-analysis/docs/README.pt-PT.md)

## Contact

- GitHub: https://github.com/samuelmaia-analytics
- LinkedIn: https://linkedin.com/in/samuelmaia-analytics
