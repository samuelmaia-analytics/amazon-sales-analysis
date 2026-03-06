# Amazon Sales Analytics | Business Impact Portfolio

[![Latest Release](https://img.shields.io/github/v/release/samuelmaia-data-analyst/amazon-sales-analysis?display_name=release)](https://github.com/samuelmaia-data-analyst/amazon-sales-analysis/releases)
[![Release Notes](https://img.shields.io/badge/Release%20Notes-CHANGELOG-blue)](CHANGELOG.md)

## Language
- English: [docs/README.en.md](docs/README.en.md)
- Português (BR): [docs/README.pt-BR.md](docs/README.pt-BR.md)

## Summary
- Business problem: revenue leakage from discount strategy.
- Audience: Revenue Ops, Sales Leadership, Category Managers.
- North Star Metric: Net Revenue Retained (NRR).
- Financial upside: +$252.3K with 5% leakage recovery scenario.

## Business Metrics Snapshot
- Net Revenue: **$32.87M**
- Discount Leakage: **$5.05M**
- North Star (NRR): **86.69%**
- Upside at 5% leakage recovery: **+$252.3K**

## Table of Contents
- [Public Releases](#public-releases)
- [Executive Summary](#executive-summary)
- [Business Problem](#business-problem)
- [Dataset](#dataset)
- [Methodology](#methodology)
- [Architecture](#architecture)
- [Results](#results)
- [Business Impact](#business-impact)
- [Business Recommendations](#business-recommendations)
- [Action Playbook (Executive)](#action-playbook-executive)
- [Scenario Simulation Snapshot](#scenario-simulation-snapshot)
- [Tech Stack](#tech-stack)
- [How to Run](#how-to-run)
- [API Examples](#api-examples)
- [Visual Snapshots](#visual-snapshots)
- [Quality and Contracts](#quality-and-contracts)
- [CI and Metrics](#ci-and-metrics)
- [Release Process](#release-process)
- [Decision Cadence](#decision-cadence)
- [Future Improvements](#future-improvements)
- [Versioning Convention](#versioning-convention)
- [Author](#author)

## Public Releases
The project release channel is published at:
- GitHub Releases: https://github.com/samuelmaia-data-analyst/amazon-sales-analysis/releases
- Changelog: `CHANGELOG.md`

Quick value from latest release line:
- Versioned pipeline with contracts + quality gates.
- Scenario simulation artifact (`scenario_simulation_summary.json`) for executive decisions.
- Operational alerts for discount spikes (`discount_spike_alerts.csv`).

## Executive Summary
The project addresses a strategic revenue efficiency problem: high discount leakage reduces net sales performance even when order volume is strong.

For commercial leadership (Head of Sales, Revenue Operations, Category Managers), this solution delivers a reproducible analytics pipeline and an executive dashboard to prioritize margin-preserving growth.

North Star Metric: **Net Revenue Retained (NRR)** = `net revenue / gross revenue before discounts`.

Current baseline from the processed dataset:
- Total net revenue: **$32.87M**
- Discount leakage: **$5.05M**
- Net Revenue Retained: **86.69%**
- Expected uplift with 5% leakage recovery: **$252.3K**

Business framing example: **Recovering only 5% of discount leakage can add ~$252K without increasing acquisition spend.**

## Business Problem
Amazon marketplace-style operations often optimize for volume but lose value through uncontrolled discounting.

This project answers:
- Where are discounts eroding revenue most?
- Which categories create the largest recoverable value?
- What is the financial upside of tighter discount governance?

## Dataset
- Source: Kaggle (`aliiihussain/amazon-sales-dataset`)
- Link: https://www.kaggle.com/datasets/aliiihussain/amazon-sales-dataset
- Scope: 50,000 transactions
- Main entities: order, product category, price, discount, region, payment method, rating

## Methodology
1. Data ingestion with fallback logic for local execution.
2. Data quality enforcement (schema checks, domain clipping, invalid-row removal).
3. Feature engineering for business metrics (`gross_revenue`, `discount_value`, `NRR`).
4. Opportunity ranking by category-level discount leakage.
5. Executive dashboards and artifacts for decision support.

## Architecture
```text
amazon-sales-analysis/
|-- app/
|   |-- api.py
|   `-- streamlit_app.py
|-- assets/
|   |-- amazon_logo.svg
|   `-- custom.css
|-- alerts/
|   `-- discount_spike_alert.py
|-- data/
|   |-- raw/
|   `-- processed/
|-- docs/
|   |-- README.en.md
|   `-- README.pt-BR.md
|-- notebooks/
|-- reports/
|   |-- figures/
|   `-- tables/
|-- Makefile
|-- scenario_simulation.py
|-- scripts/
|   |-- run_alerts.py
|   |-- run_pipeline.py
|   `-- run_scenario_simulator.py
|-- src/amazon_sales_analysis/
|   |-- analytics.py
|   |-- anomaly_detection.py
|   |-- config.py
|   |-- data_ingestion.py
|   |-- data_preprocessing.py
|   |-- eda.py
|   |-- evaluation.py
|   |-- feature_engineering.py
|   |-- logging_config.py
|   |-- modeling.py
|   |-- scenario_simulator.py
|   `-- visualization.py
|-- tests/
|-- main.py
|-- pyproject.toml
|-- requirements.txt
`-- Dockerfile
```

## Results
- Net revenue retained: **86.69%** (baseline)
- Discount leakage identified: **$5.05M**
- Highest-revenue category: **Beauty ($5.55M)**
- Prioritized category opportunities exported to `reports/tables/discount_opportunities.csv`
- Discount spike anomalies exported to `reports/tables/discount_spike_alerts.csv`

## Business Impact
- 5% recovery scenario: **+$252.3K** net revenue
- 10% recovery scenario: **+$504.7K** net revenue
- Decision impact: supports discount policy redesign by category and promotional channel

## Business Recommendations
- Cap discount depth for high-leakage categories and monitor weekly NRR.
- Shift campaign strategy from blanket discounts to category-specific thresholds.
- Track `discount_to_revenue_ratio` as a governance KPI in leadership reviews.
- Pilot policy in top 3 leakage categories before full rollout.

## Action Playbook (Executive)
| Priority | Action | Owner | Cadence | Trigger | Target |
|---|---|---|---|---|---|
| P1 | Apply discount caps in top leakage categories (Beauty, Books, Sports) | Revenue Ops + Category Managers | Weekly | `discount_to_revenue_ratio > 15%` | Recover 5% leakage |
| P2 | Review anomaly alerts and freeze outlier campaigns | Sales Leadership | Weekly | `severity in {medium, high}` in spike alerts | Reduce avoidable leakage |
| P3 | Recalibrate discount thresholds by category using simulation outputs | Head of Sales + FP&A | Monthly | `north_star_nrr < 87%` | Lift NRR trend |
| P4 | Scale pilot policy from top 3 categories to full portfolio | Revenue Ops | Quarterly | Pilot reaches recovery target | Institutionalize governance |

Execution artifacts:
- `reports/tables/discount_opportunities.csv`
- `reports/tables/discount_spike_alerts.csv`
- `reports/tables/scenario_simulation_summary.json`

## Scenario Simulation Snapshot
Based on `reports/tables/scenario_simulation_summary.json` (5% default leakage recovery):

| Metric | Baseline | Simulated | Delta |
|---|---:|---:|---:|
| Net Revenue | $32.87M | $33.12M | **+$252.3K** |
| NRR | 86.69% | 87.35% | **+0.66 p.p.** |
| Gross Revenue | $37.91M | $37.91M | - |

Top category uplifts from `reports/tables/scenario_simulation_breakdown.csv`:

| Category | Expected Uplift |
|---|---:|
| Beauty | $42.7K |
| Books | $42.5K |
| Sports | $42.3K |

Visual view (5% scenario):
```text
Net Revenue (USD M)
Baseline  | ################################ 32.87
Simulated | ################################# 33.12
Gain      | +0.25M
```

## Tech Stack
Python, Pandas, Plotly, Streamlit, FastAPI, Seaborn, Matplotlib, Pytest.

## How to Run
### Local
```bash
git clone https://github.com/samuelmaia-data-analyst/amazon-sales-analysis.git
cd amazon-sales-analysis
pip install -r requirements.txt
python main.py
streamlit run app/streamlit_app.py
uvicorn app.api:app --reload
make pipeline
make alerts
make scenario
```

### Cron Example (Operational Alerts)
```bash
0 8 * * 1-5 cd /path/to/amazon-sales-analysis && make alerts
```

### Docker
```bash
docker build -t amazon-sales-analytics .
docker run --rm -p 8501:8501 amazon-sales-analytics
```

## API Examples
Base URL (local): `http://127.0.0.1:8000`

```bash
uvicorn app.api:app --reload
```

`GET /api/v1/revenue_metrics`
```json
{
  "total_revenue": 32866579.536,
  "gross_revenue": 37913104.54000001,
  "discount_leakage": 5046525.004000008,
  "north_star_nrr": 0.866892330099855,
  "total_orders": 50000.0,
  "avg_ticket": 657.33159072
}
```

`GET /metrics/opportunities` (sample)
```json
[
  {
    "product_category": "Beauty",
    "total_revenue": 5550626.229,
    "discount_value": 854360.231,
    "discount_to_revenue_ratio": 0.15392141278335028
  }
]
```

`GET /alerts/discount-spikes` (sample)
```json
[
  {
    "order_date": "2022-10-31",
    "product_category": "Fashion",
    "avg_discount_percent": 21.363636363636363,
    "z_score": 2.696544107570046,
    "estimated_leakage_usd": 933.6917756183568,
    "severity": "medium"
  }
]
```

## Visual Snapshots
![Sales Trend](reports/figures/sales_trend_over_time.png)
![Top Categories](reports/figures/top_categories_by_sales.png)

## Quality and Contracts
- Raw data contract is versioned at `contracts/sales_dataset.contract.json`.
- Product metrics contract is versioned at `contracts/product_metrics.contract.json`.
- Pipeline enforces:
  - required schema on raw data
  - clean-data quality gates (domain and invalid-value checks)
  - product metrics generation in `reports/metrics/product_metrics.json`
  - pipeline provenance with `pipeline_version` in metrics artifacts

### Local Quality Commands
```bash
pip install -r requirements-dev.txt
black --check .
isort --check-only .
ruff check .
mypy src scripts
pytest
```

## CI and Metrics
- CI workflow: `.github/workflows/ci.yml`
- Gates: formatting, lint, type checking, tests and coverage threshold (`>=70%`).
- CI artifacts exported in `reports/metrics/`:
  - `pytest-results.xml`
  - `coverage.xml`

## Release Process
1. Update changelog with a new section in `CHANGELOG.md` (format `## [x.y.z] - YYYY-MM-DD`).
2. Bump package version:
   ```bash
   python scripts/bump_version.py 1.0.0
   ```
3. Commit, tag and push:
   ```bash
   git add .
   git commit -m "chore(release): v1.0.0"
   git tag v1.0.0
   git push origin main --tags
   ```
4. The release workflow validates version/changelog consistency and publishes GitHub release.

## Decision Cadence
- Weekly: monitor `north_star_nrr` + `discount_leakage` and review anomaly alerts in `reports/tables/discount_spike_alerts.csv`.
- Monthly: review and recalibrate discount thresholds by category using scenario simulation outputs.

## Future Improvements
- Add model-based threshold recommendations per category (beyond static policy ranges).
- Add API authentication and rate limiting for production BI integration.

## Versioning Convention
Use semantic commit messages:
- `feat: add feature engineering pipeline`
- `fix: correct discount leakage calculation`
- `docs: improve executive summary for international recruiters`

## Author
Samuel Maia
- GitHub: https://github.com/samuelmaia-data-analyst
- LinkedIn: https://linkedin.com/in/samuelmaia-data-analyst
- Email: smaia2@gmail.com



