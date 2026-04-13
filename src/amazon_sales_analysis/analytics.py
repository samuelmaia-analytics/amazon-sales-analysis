import pandas as pd

from .sales_analysis import compute_kpi_summary, prepare_sales_frame


def add_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    return prepare_sales_frame(df)


def summarize_kpis(df: pd.DataFrame) -> dict[str, float]:
    summary = compute_kpi_summary(prepare_sales_frame(df))
    lookup = dict(zip(summary["metric"], summary["value"], strict=False))
    return {
        "total_revenue": float(lookup.get("total_revenue", 0.0)),
        "total_orders": float(lookup.get("total_orders", 0.0)),
        "total_units": float(lookup.get("total_units", 0.0)),
        "avg_ticket": float(lookup.get("avg_order_value", 0.0)),
        "avg_rating": float(lookup.get("avg_rating", 0.0)),
        "net_revenue_retained": float(lookup.get("net_revenue_retained", 0.0)),
    }


def summarize_monthly_performance(df: pd.DataFrame) -> pd.DataFrame:
    prepared = prepare_sales_frame(df)
    monthly = (
        prepared.groupby("month_start", as_index=False)
        .agg(
            total_revenue=("total_revenue", "sum"),
            gross_revenue=("gross_revenue", "sum"),
            orders=("order_id", "nunique"),
            discount_value=("discount_value", "sum"),
        )
        .sort_values("month_start")
    )
    monthly["avg_order_value"] = monthly["total_revenue"] / monthly["orders"].replace(0, pd.NA)
    monthly["nrr"] = monthly["total_revenue"] / monthly["gross_revenue"].replace(0, pd.NA)
    return monthly.fillna(0.0)
