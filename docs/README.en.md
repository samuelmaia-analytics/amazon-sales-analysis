# Amazon Sales Analysis (EN)

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
```

## Docker
```bash
docker build -t amazon-sales-analytics .
docker run --rm -p 8501:8501 amazon-sales-analytics
```

## Contact
- GitHub: https://github.com/samuelmaia-data-analyst
- LinkedIn: https://linkedin.com/in/samuelmaia-data-analyst
- Email: smaia2@gmail.com
