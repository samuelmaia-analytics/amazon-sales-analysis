from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from .config import METRICS_DIR

PRODUCT_METRICS_VERSION = "1.0.0"


def collect_product_metrics(
    df_raw: pd.DataFrame,
    df_clean: pd.DataFrame,
    df_featured: pd.DataFrame,
    *,
    contract_version: str,
    pipeline_version: str = "unknown",
) -> dict[str, float | int | str]:
    gross_revenue = float(df_featured["gross_revenue"].sum()) if not df_featured.empty else 0.0
    total_revenue = float(df_featured["total_revenue"].sum()) if not df_featured.empty else 0.0
    discount_leakage = gross_revenue - total_revenue
    nrr = (total_revenue / gross_revenue) if gross_revenue else 0.0

    min_date = df_featured["order_date"].min()
    max_date = df_featured["order_date"].max()
    date_start = min_date.date().isoformat() if pd.notna(min_date) else ""
    date_end = max_date.date().isoformat() if pd.notna(max_date) else ""

    metrics: dict[str, float | int | str] = {
        "metrics_version": PRODUCT_METRICS_VERSION,
        "contract_version": contract_version,
        "pipeline_version": pipeline_version,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "raw_row_count": int(len(df_raw)),
        "clean_row_count": int(len(df_clean)),
        "rows_dropped": int(len(df_raw) - len(df_clean)),
        "row_retention_rate": (float(len(df_clean)) / float(len(df_raw))) if len(df_raw) else 0.0,
        "total_revenue": total_revenue,
        "gross_revenue": gross_revenue,
        "discount_leakage": discount_leakage,
        "north_star_nrr": nrr,
        "unique_orders": int(df_featured["order_id"].nunique()) if "order_id" in df_featured else 0,
        "unique_categories": (
            int(df_featured["product_category"].nunique())
            if "product_category" in df_featured
            else 0
        ),
        "period_start": date_start,
        "period_end": date_end,
    }
    return metrics


def save_product_metrics(
    metrics: dict[str, float | int | str], output_path: Path | None = None
) -> Path:
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    target = output_path or (METRICS_DIR / "product_metrics.json")
    target.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return target
