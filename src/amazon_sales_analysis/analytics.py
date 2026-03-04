import pandas as pd

from .feature_engineering import build_features


def add_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    return build_features(df)


def summarize_kpis(df: pd.DataFrame) -> dict[str, float]:
    orders = float(df["order_id"].nunique()) if not df.empty else 0.0
    revenue = float(df["total_revenue"].sum())
    units = float(df["quantity_sold"].sum())
    gross_revenue = (
        float(df["gross_revenue"].sum())
        if "gross_revenue" in df
        else float((df["price"] * df["quantity_sold"]).sum())
    )

    return {
        "total_revenue": revenue,
        "total_orders": orders,
        "total_units": units,
        "avg_ticket": revenue / orders if orders else 0.0,
        "avg_rating": float(df["rating"].mean()) if not df.empty else 0.0,
        "net_revenue_retained": (revenue / gross_revenue) if gross_revenue else 0.0,
    }
