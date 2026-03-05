from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from amazon_sales_analysis.analytics import add_derived_metrics, summarize_kpis
from amazon_sales_analysis.anomaly_detection import detect_discount_spikes
from amazon_sales_analysis.modeling import rank_discount_opportunities

DATASET_PATH = ROOT_DIR / "data" / "processed" / "amazon_sales_clean.csv"
ALERTS_PATH = ROOT_DIR / "reports" / "tables" / "discount_spike_alerts.csv"

app = FastAPI(
    title="Amazon Sales Analytics API",
    version="0.2.0",
    description="Executive metrics and operational alerts for sales performance.",
)


def _load_processed_data() -> pd.DataFrame:
    if not DATASET_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Processed dataset not found. Run: python scripts/run_pipeline.py",
        )
    frame = pd.read_csv(DATASET_PATH, parse_dates=["order_date"])
    return add_derived_metrics(frame)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics/summary")
def metrics_summary() -> dict[str, float]:
    frame = _load_processed_data()
    kpis = summarize_kpis(frame)
    gross_revenue = float(frame["gross_revenue"].sum()) if "gross_revenue" in frame else 0.0
    total_revenue = float(frame["total_revenue"].sum())

    return {
        "total_revenue": total_revenue,
        "gross_revenue": gross_revenue,
        "discount_leakage": gross_revenue - total_revenue,
        "north_star_nrr": kpis["net_revenue_retained"],
        "total_orders": kpis["total_orders"],
        "avg_ticket": kpis["avg_ticket"],
    }


@app.get("/metrics/opportunities")
def category_opportunities() -> list[dict[str, str | float]]:
    frame = _load_processed_data()
    opportunities = rank_discount_opportunities(frame)
    return opportunities.to_dict(orient="records")


@app.get("/alerts/discount-spikes")
def discount_spikes() -> list[dict[str, str | float]]:
    if ALERTS_PATH.exists():
        alerts = pd.read_csv(ALERTS_PATH, parse_dates=["order_date"])
    else:
        frame = _load_processed_data()
        alerts = detect_discount_spikes(frame)

    if alerts.empty:
        return []
    alerts["order_date"] = pd.to_datetime(alerts["order_date"]).dt.date.astype(str)
    return alerts.to_dict(orient="records")
