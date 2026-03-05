# Amazon Sales Analysis (EN)

## Language Switch
- Main README: [../README.md](../README.md)
- Portugues (BR): [README.pt-BR.md](README.pt-BR.md)

## Summary
- Business problem: discount leakage impacting net revenue.
- Audience: revenue leaders and category managers.
- North Star Metric: Net Revenue Retained (NRR).
- Value case: +$252.3K at 5% leakage recovery.

## Business Metrics Snapshot
- Net Revenue: **$32.87M**
- Discount Leakage: **$5.05M**
- North Star (NRR): **86.69%**
- Upside at 5% leakage recovery: **+$252.3K**

## Table of Contents
- [Executive Summary](#executive-summary)
- [Problem](#problem)
- [Approach](#approach)
- [Key Insights](#key-insights)
- [Expected Impact](#expected-impact)
- [Methodology](#methodology)
- [Dataset Source](#dataset-source)
- [Architecture](#architecture)
- [How to Run](#how-to-run)
- [Docker](#docker)
- [Quality and Contracts](#quality-and-contracts)
- [CI and Product Metrics](#ci-and-product-metrics)
- [Release Process](#release-process)
- [Decision Cadence](#decision-cadence)
- [Contact](#contact)

## Executive Summary
This project solves a strategic pricing problem: discount practices are increasing volume but leaking significant net revenue.

Audience: Revenue leaders, category managers, and operations teams who need to maximize commercial performance without adding acquisition cost.

North Star Metric: **Net Revenue Retained (NRR)** = `total_revenue / gross_revenue`.

From the current dataset baseline:
- Net revenue: **$32.87M**
- Discount leakage: **$5.05M**
- NRR: **86.69%**
- 5% leakage recovery upside: **$252.3K**

## Problem
How can we reduce discount leakage while preserving sales velocity?

## Approach
- Build a reproducible end-to-end pipeline.
- Enforce data quality constraints.
- Engineer business-ready features.
- Rank category-level leakage opportunities.
- Deliver executive dashboard views for action.
- Simulate category-level leakage recovery scenarios in Streamlit.
- Detect discount spikes and export operational alerts.
- Expose summary metrics and alerts through FastAPI endpoints.

## Key Insights
- Leakage is materially relevant versus current net revenue.
- Opportunity concentration exists by category.
- A small recovery rate already creates meaningful upside.

## Expected Impact
Recovering 5% of current discount leakage can add about **$252K** in net revenue.

## Methodology
Ingestion -> Cleaning -> Feature Engineering -> Evaluation -> Visualization

## Dataset Source
- Kaggle dataset: `aliiihussain/amazon-sales-dataset`
- Link: https://www.kaggle.com/datasets/aliiihussain/amazon-sales-dataset

## Architecture
See root `README.md` for complete project tree and runbook.

## How to Run
```bash
pip install -r requirements.txt
python main.py
streamlit run app/streamlit_app.py
uvicorn app.api:app --reload
```

## Docker
```bash
docker build -t amazon-sales-analytics .
docker run --rm -p 8501:8501 amazon-sales-analytics
```

## Quality and Contracts
- Raw contract: `contracts/sales_dataset.contract.json`
- Product metrics contract: `contracts/product_metrics.contract.json`
- Pipeline gates:
  - raw schema contract enforcement
  - clean-data quality checks
  - metrics generation in `reports/metrics/product_metrics.json`
  - discount spike alert export in `reports/tables/discount_spike_alerts.csv`

### Local Quality Commands
```bash
pip install -r requirements-dev.txt
black --check .
isort --check-only .
ruff check .
mypy src scripts
pytest
```

## CI and Product Metrics
- CI workflow: `.github/workflows/ci.yml`
- Gates: format, lint, typing, tests, coverage (`>=70%`)
- Exported CI artifacts:
  - `reports/metrics/coverage.xml`
  - `reports/metrics/pytest-results.xml`

## Release Process
1. Add release entry in `CHANGELOG.md`.
2. Bump version:
   ```bash
   python scripts/bump_version.py 0.2.0
   ```
3. Tag and push:
   ```bash
   git tag v0.2.0
   git push origin main --tags
   ```
4. Release workflow (`.github/workflows/release.yml`) validates tag/version/changelog consistency.

## Decision Cadence
- Weekly: review `north_star_nrr` and `discount_leakage`, then inspect `reports/tables/discount_spike_alerts.csv`.
- Monthly: recalibrate category discount thresholds using the Scenario Simulator.

## Contact
- GitHub: https://github.com/samuelmaia-data-analyst
- LinkedIn: https://linkedin.com/in/samuelmaia-data-analyst
- Email: smaia2@gmail.com



