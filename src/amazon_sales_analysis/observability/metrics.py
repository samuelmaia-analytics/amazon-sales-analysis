from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pandas as pd

from ..config import Settings, get_settings
from ..insights import generate_executive_insights
from ..pipelines.runtime import write_json_artifact
from ..sales_analysis import build_executive_report, prepare_sales_frame

PRODUCT_METRICS_VERSION = "2.0.0"
KPI_BASELINE_KEYS = (
    "total_revenue",
    "gross_revenue",
    "discount_leakage",
    "north_star_nrr",
    "total_orders",
    "avg_ticket",
    "clean_row_count",
    "row_retention_rate",
)


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
    metrics: Mapping[str, float | int | str | list[dict[str, str]]], output_path: Path | None = None
) -> Path:
    target = output_path or (get_settings().metrics_dir / "product_metrics.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    return write_json_artifact(dict(metrics), target)


def metrics_baseline_path(settings: Settings | None = None) -> Path:
    resolved_settings = settings or get_settings()
    return resolved_settings.metrics_dir / "product_metrics_baseline.json"


def metrics_regression_report_path(settings: Settings | None = None) -> Path:
    resolved_settings = settings or get_settings()
    return resolved_settings.metrics_dir / "product_metrics_regression.json"


def load_metrics_baseline(settings: Settings | None = None) -> dict[str, Any] | None:
    baseline_path = metrics_baseline_path(settings)
    if not baseline_path.exists():
        return None
    return cast(dict[str, Any], json.loads(baseline_path.read_text(encoding="utf-8")))


def save_metrics_baseline(
    metrics: Mapping[str, float | int | str | list[dict[str, str]]], settings: Settings | None = None
) -> Path:
    return write_json_artifact(dict(metrics), metrics_baseline_path(settings))


def build_metrics_regression_report(
    current_metrics: dict[str, Any],
    *,
    settings: Settings | None = None,
    baseline_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_settings = settings or get_settings()
    resolved_baseline = baseline_metrics if baseline_metrics is not None else load_metrics_baseline(
        resolved_settings
    )

    if resolved_baseline is None:
        return {
            "status": "baseline_initialized",
            "baseline_path": str(metrics_baseline_path(resolved_settings)),
            "tolerance_pct": resolved_settings.kpi_regression_tolerance_pct,
            "kpi_deltas": {},
            "failed_metrics": [],
        }

    kpi_deltas: dict[str, dict[str, float | str]] = {}
    failed_metrics: list[str] = []

    for metric_name in KPI_BASELINE_KEYS:
        current_value = float(current_metrics.get(metric_name, 0.0))
        baseline_value = float(resolved_baseline.get(metric_name, 0.0))
        delta = current_value - baseline_value
        delta_pct = 0.0 if baseline_value == 0 else delta / baseline_value
        status = (
            "fail"
            if abs(delta_pct) > resolved_settings.kpi_regression_tolerance_pct
            else "pass"
        )
        if status == "fail":
            failed_metrics.append(metric_name)
        kpi_deltas[metric_name] = {
            "baseline": baseline_value,
            "current": current_value,
            "delta": delta,
            "delta_pct": delta_pct,
            "status": status,
        }

    return {
        "status": "fail" if failed_metrics else "pass",
        "baseline_path": str(metrics_baseline_path(resolved_settings)),
        "tolerance_pct": resolved_settings.kpi_regression_tolerance_pct,
        "kpi_deltas": kpi_deltas,
        "failed_metrics": failed_metrics,
    }


def save_metrics_regression_report(
    report: dict[str, Any], settings: Settings | None = None
) -> Path:
    return write_json_artifact(report, metrics_regression_report_path(settings))
