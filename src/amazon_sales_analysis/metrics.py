from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .config import get_settings
from .insights import generate_executive_insights
from .pipelines.runtime import write_json_artifact
from .sales_analysis import build_executive_report, prepare_sales_frame

PRODUCT_METRICS_VERSION = "2.0.0"


def collect_product_metrics(
    df_raw: pd.DataFrame,
    df_clean: pd.DataFrame,
    df_featured: pd.DataFrame,
    *,
    contract_version: str,
    pipeline_version: str = "unknown",
) -> dict[str, float | int | str | list[dict[str, str]]]:
    prepared = prepare_sales_frame(df_featured)
    insights = generate_executive_insights(prepared)
    report = build_executive_report(prepared, insights)
    kpi_lookup = dict(zip(report.kpi_summary["metric"], report.kpi_summary["value"], strict=False))

    min_date = prepared["order_date"].min()
    max_date = prepared["order_date"].max()
    date_start = min_date.date().isoformat() if pd.notna(min_date) else ""
    date_end = max_date.date().isoformat() if pd.notna(max_date) else ""

    headline_insights = [
        {str(key): str(value) for key, value in record.items()}
        for record in insights.to_dict(orient="records")
    ]

    metrics: dict[str, Any] = {
        "metrics_version": PRODUCT_METRICS_VERSION,
        "contract_version": contract_version,
        "pipeline_version": pipeline_version,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "raw_row_count": int(len(df_raw)),
        "clean_row_count": int(len(df_clean)),
        "rows_dropped": int(len(df_raw) - len(df_clean)),
        "row_retention_rate": (float(len(df_clean)) / float(len(df_raw))) if len(df_raw) else 0.0,
        "total_revenue": float(kpi_lookup.get("total_revenue", 0.0)),
        "gross_revenue": float(prepared["gross_revenue"].sum()) if not prepared.empty else 0.0,
        "discount_leakage": float(kpi_lookup.get("discount_leakage", 0.0)),
        "north_star_nrr": float(kpi_lookup.get("net_revenue_retained", 0.0)),
        "total_orders": int(kpi_lookup.get("total_orders", 0.0)),
        "avg_ticket": float(kpi_lookup.get("avg_order_value", 0.0)),
        "unique_categories": (
            int(prepared["product_category"].nunique()) if "product_category" in prepared else 0
        ),
        "period_start": date_start,
        "period_end": date_end,
        "headline_insights": headline_insights,
    }
    return metrics


def save_product_metrics(
    metrics: dict[str, float | int | str | list[dict[str, str]]], output_path: Path | None = None
) -> Path:
    target = output_path or (get_settings().metrics_dir / "product_metrics.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    return write_json_artifact(metrics, target)
