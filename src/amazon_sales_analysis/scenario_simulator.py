from __future__ import annotations

from collections.abc import Mapping

import pandas as pd


def _normalize_recovery_rate(value: float) -> float:
    if value < 0:
        return 0.0
    if value > 1:
        return 1.0
    return value


def simulate_leakage_recovery(
    df: pd.DataFrame,
    recovery_rates: Mapping[str, float],
) -> dict[str, float | pd.DataFrame]:
    frame = df.copy()
    if "gross_revenue" not in frame.columns:
        frame["gross_revenue"] = frame["price"] * frame["quantity_sold"]
    if "discount_value" not in frame.columns:
        frame["discount_value"] = frame["gross_revenue"] - frame["total_revenue"]

    category_summary = (
        frame.groupby("product_category", as_index=False)
        .agg(
            gross_revenue=("gross_revenue", "sum"),
            total_revenue=("total_revenue", "sum"),
            discount_leakage=("discount_value", "sum"),
        )
        .sort_values("discount_leakage", ascending=False)
    )

    category_summary["recovery_rate"] = category_summary["product_category"].map(
        lambda category: _normalize_recovery_rate(float(recovery_rates.get(str(category), 0.0)))
    )
    category_summary["expected_uplift"] = (
        category_summary["discount_leakage"] * category_summary["recovery_rate"]
    )
    category_summary["simulated_revenue"] = (
        category_summary["total_revenue"] + category_summary["expected_uplift"]
    )

    baseline_revenue = float(category_summary["total_revenue"].sum())
    gross_revenue = float(category_summary["gross_revenue"].sum())
    total_uplift = float(category_summary["expected_uplift"].sum())
    simulated_revenue = baseline_revenue + total_uplift

    return {
        "baseline_revenue": baseline_revenue,
        "gross_revenue": gross_revenue,
        "baseline_nrr": (baseline_revenue / gross_revenue) if gross_revenue else 0.0,
        "simulated_revenue": simulated_revenue,
        "simulated_nrr": (simulated_revenue / gross_revenue) if gross_revenue else 0.0,
        "total_uplift": total_uplift,
        "category_breakdown": category_summary.reset_index(drop=True),
    }
