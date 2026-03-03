# Amazon Sales Analytics | Business Impact Portfolio

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
|   `-- streamlit_app.py
|-- assets/
|   |-- amazon_logo.svg
|   `-- custom.css
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
|-- scripts/
|   `-- run_pipeline.py
|-- src/amazon_sales_analysis/
|   |-- analytics.py
|   |-- config.py
|   |-- data_ingestion.py
|   |-- data_preprocessing.py
|   |-- eda.py
|   |-- evaluation.py
|   |-- feature_engineering.py
|   |-- logging_config.py
|   |-- modeling.py
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

## Business Impact
- 5% recovery scenario: **+$252.3K** net revenue
- 10% recovery scenario: **+$504.7K** net revenue
- Decision impact: supports discount policy redesign by category and promotional channel

## Business Recommendations
- Cap discount depth for high-leakage categories and monitor weekly NRR.
- Shift campaign strategy from blanket discounts to category-specific thresholds.
- Track `discount_to_revenue_ratio` as a governance KPI in leadership reviews.
- Pilot policy in top 3 leakage categories before full rollout.

## Tech Stack
Python, Pandas, Plotly, Streamlit, Seaborn, Matplotlib, Pytest.

## How to Run
### Local
```bash
git clone https://github.com/samuelmaia-data-analyst/amazon-sales-analysis.git
cd amazon-sales-analysis
pip install -r requirements.txt
python main.py
streamlit run app/streamlit_app.py
```

### Docker
```bash
docker build -t amazon-sales-analytics .
docker run --rm -p 8501:8501 amazon-sales-analytics
```

## Future Improvements
- Add scenario simulator for category discount policy changes.
- Deploy CI pipeline (tests + lint + docs checks).
- Add anomaly detection on discount spikes.
- Expose metrics through a FastAPI endpoint for BI integration.

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
