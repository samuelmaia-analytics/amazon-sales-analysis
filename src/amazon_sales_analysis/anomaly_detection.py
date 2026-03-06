from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import TABLES_DIR


def detect_discount_spikes(
    df: pd.DataFrame,
    *,
    z_threshold: float = 2.5,
    min_observations: int = 5,
) -> pd.DataFrame:
    frame = df.copy()
    frame["order_date"] = pd.to_datetime(frame["order_date"], errors="coerce")
    frame = frame.dropna(subset=["order_date"])

    if "gross_revenue" not in frame.columns:
        frame["gross_revenue"] = frame["price"] * frame["quantity_sold"]

    daily = (
        frame.groupby(["product_category", "order_date"], as_index=False)
        .agg(
            avg_discount_percent=("discount_percent", "mean"),
            gross_revenue=("gross_revenue", "sum"),
        )
        .sort_values(["product_category", "order_date"])
    )

    grouped = daily.groupby("product_category")
    daily["baseline_mean"] = grouped["avg_discount_percent"].transform("mean")
    daily["baseline_std"] = grouped["avg_discount_percent"].transform("std").fillna(0.0)
    daily["obs_count"] = grouped["avg_discount_percent"].transform("count")

    safe_std = daily["baseline_std"].replace(0, pd.NA)
    daily["z_score"] = ((daily["avg_discount_percent"] - daily["baseline_mean"]) / safe_std).fillna(
        0.0
    )
    daily["discount_gap_pct"] = (daily["avg_discount_percent"] - daily["baseline_mean"]).clip(
        lower=0
    )
    daily["estimated_leakage_usd"] = daily["gross_revenue"] * (daily["discount_gap_pct"] / 100.0)

    alerts = daily[
        (daily["obs_count"] >= min_observations) & (daily["z_score"] >= z_threshold)
    ].copy()
    alerts["severity"] = pd.cut(
        alerts["z_score"],
        bins=[z_threshold, 3.5, 5.0, float("inf")],
        labels=["medium", "high", "critical"],
        include_lowest=True,
    ).astype(str)

    export_columns = [
        "order_date",
        "product_category",
        "avg_discount_percent",
        "baseline_mean",
        "baseline_std",
        "z_score",
        "gross_revenue",
        "estimated_leakage_usd",
        "severity",
    ]
    return alerts[export_columns].sort_values(
        ["severity", "estimated_leakage_usd"], ascending=[False, False]
    )


def export_discount_spike_alerts(alerts: pd.DataFrame, output_path: Path | None = None) -> Path:
    target = output_path or (TABLES_DIR / "discount_spike_alerts.csv")
    target.parent.mkdir(parents=True, exist_ok=True)
    alerts.to_csv(target, index=False)
    return target
