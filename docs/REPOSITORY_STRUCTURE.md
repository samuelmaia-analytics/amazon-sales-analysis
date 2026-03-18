# Repository Structure

This document describes the current repository topology and where production-oriented logic should live.

## Top-Level Layout

```text
.
|-- .github/
|-- alerts/
|-- app/
|-- assets/
|-- contracts/
|-- data/
|-- docs/
|-- notebooks/
|-- reports/
|-- scripts/
|-- sql/
|-- src/
|-- tests/
|-- CHANGELOG.md
|-- CONTRIBUTING.md
|-- Dockerfile
|-- Makefile
|-- README.md
|-- main.py
|-- pyproject.toml
|-- scenario_simulation.py
`-- streamlit_app.py
```

## `.github/`

Repository automation and contribution workflow:

- `workflows/ci.yml`
- `workflows/release.yml`
- `ISSUE_TEMPLATE/`
- `PULL_REQUEST_TEMPLATE.md`
- `CODEOWNERS`

## `alerts/`

Thin alert-related script surface:

- `discount_spike_alert.py`

## `app/`

Application-facing entry points:

- `api.py`
  FastAPI surface for health, metrics, alerts, warehouse queries, and run history.
- `streamlit_app.py`
  Streamlit dashboard surface.
- `__init__.py`
  Path bootstrap for local execution.

## `assets/`

Static assets used by the app and presentation layer:

- `amazon_logo.svg`
- `custom.css`

## `contracts/`

Generated or versioned contract artifacts:

- `sales_dataset.contract.json`
- `product_metrics.contract.json`

## `data/`

Local runtime storage. Not all layers need to exist ahead of execution; some are created from configuration.

- `raw/`
  Raw landed dataset from Kaggle.
- `bronze/`
  Snapshot of raw inputs by run.
- `silver/`
  Cleaned and validated snapshots.
- `gold/`
  Analytics-ready mart snapshots.
- `warehouse/`
  DuckDB file and warehouse query artifacts.
- `processed/`
  Stable processed dataset used by API and downstream flows.
- `external/`
  Reserved for externally managed inputs when needed.

## `docs/`

Repository documentation:

- `README.en.md`
- `README.pt-BR.md`
- `README.pt-PT.md`
- `REPOSITORY_STRUCTURE.md`

## `notebooks/`

Exploratory and supporting analysis only:

- `01_exploratory_analysis.ipynb`
- `02_feature_engineering.ipynb`
- `03_modeling.ipynb`

Notebook code should not be treated as the source of truth for production logic.

## `reports/`

Generated outputs and execution artifacts:

- `figures/`
- `tables/`
- `metrics/`
- `runs/`

## `scripts/`

Wrapper scripts around package entry points:

- `run_pipeline.py`
- `run_alerts.py`
- `run_scenario_simulator.py`
- `bump_version.py`

## `sql/`

Warehouse-facing SQL assets:

- `gold_commercial_mart.sql`
- `warehouse_validation.sql`

## `src/amazon_sales_analysis/`

The main Python package. This is where reusable production logic belongs.

### Core runtime and configuration

- `__init__.py`
- `config.py`
- `logging_config.py`
- `operations.py`
- `pipelines/runtime.py`

### Compatibility shims

- `data_ingestion.py`
- `data_preprocessing.py`
- `contracts.py`
- `logging_config.py`
- `metrics.py`
- `quality.py`
- `run_history.py`
- `warehouse.py`
- `warehouse_service.py`

These preserve backward-compatible import paths while the real implementation lives in domain packages below.

### Domain packages

- `ingestion/data_ingestion.py`
- `transformations/data_preprocessing.py`
- `validation/contracts.py`
- `validation/schema.py`
- `validation/quality.py`
- `observability/logging_config.py`
- `observability/metrics.py`
- `serving/warehouse.py`
- `serving/warehouse_service.py`
- `serving/run_history.py`
- `serving/operations.py`

### Analytical logic

- `feature_engineering.py`
- `business_metrics.py`
- `sales_analysis.py`
- `analytics.py`
- `eda.py`
- `evaluation.py`
- `insights.py`
- `decision_engine.py`
- `modeling.py`
- `table_organization.py`
- `visualization.py`
- `scenario_simulator.py`
- `anomaly_detection.py`

### CLI surfaces

- `cli/pipeline.py`
- `cli/alerts.py`
- `cli/scenario.py`
- `cli/warehouse.py`

## `tests/`

Automated coverage for:

- contracts and preprocessing
- quality gates
- metrics and modeling
- runtime orchestration
- API behavior
- warehouse behavior
- execution history

## Dataset Source

Configured in `src/amazon_sales_analysis/config.py`:

- Kaggle dataset: `aliiihussain/amazon-sales-dataset`
- Retrieval package: `kagglehub`

Local landing path:

- `data/raw/amazon_sales/amazon_sales_dataset.csv`

## Placement Rules

- Put reusable logic in `src/`, not in notebooks or scripts
- Put generated outputs in `reports/` or `data/`, not in `src/`
- Put warehouse SQL in `sql/`
- Keep GitHub workflow and contribution metadata in `.github/`
- Keep exploratory work isolated in `notebooks/`
