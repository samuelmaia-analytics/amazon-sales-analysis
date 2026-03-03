import pandas as pd


def build_executive_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    frame = df.copy()

    total_revenue = float(frame["total_revenue"].sum())
    total_orders = int(frame["order_id"].nunique())
    total_units = int(frame["quantity_sold"].sum())
    avg_ticket = total_revenue / total_orders if total_orders else 0.0
    avg_rating = float(frame["rating"].mean()) if not frame.empty else 0.0
    gross_revenue = float(frame["gross_revenue"].sum()) if "gross_revenue" in frame else 0.0
    nrr = (total_revenue / gross_revenue) if gross_revenue else 0.0

    kpi_summary = pd.DataFrame(
        {
            "metric": [
                "total_revenue",
                "total_orders",
                "total_units",
                "avg_ticket",
                "avg_rating",
                "north_star_nrr",
            ],
            "value": [total_revenue, total_orders, total_units, avg_ticket, avg_rating, nrr],
        }
    )

    category_performance = (
        frame.groupby("product_category", as_index=False)
        .agg(
            total_revenue=("total_revenue", "sum"),
            total_units=("quantity_sold", "sum"),
            total_orders=("order_id", "nunique"),
            avg_rating=("rating", "mean"),
            discount_value=("discount_value", "sum"),
        )
        .sort_values("total_revenue", ascending=False)
    )

    regional_performance = (
        frame.groupby("customer_region", as_index=False)
        .agg(
            total_revenue=("total_revenue", "sum"),
            total_orders=("order_id", "nunique"),
            avg_ticket=("total_revenue", "mean"),
        )
        .sort_values("total_revenue", ascending=False)
    )

    payment_performance = (
        frame.groupby("payment_method", as_index=False)
        .agg(
            total_revenue=("total_revenue", "sum"),
            total_orders=("order_id", "nunique"),
            avg_ticket=("total_revenue", "mean"),
        )
        .sort_values("total_revenue", ascending=False)
    )

    monthly_trend = (
        frame.set_index("order_date")["total_revenue"]
        .resample("ME")
        .sum()
        .reset_index()
        .rename(columns={"order_date": "month_end"})
        .sort_values("month_end")
    )

    data_quality_audit = pd.DataFrame(
        {
            "check": [
                "row_count",
                "null_values",
                "duplicated_order_id",
                "discount_out_of_range",
                "rating_out_of_range",
            ],
            "value": [
                len(frame),
                int(frame.isna().sum().sum()),
                int(frame["order_id"].duplicated().sum()),
                int(((frame["discount_percent"] < 0) | (frame["discount_percent"] > 100)).sum()),
                int(((frame["rating"] < 0) | (frame["rating"] > 5)).sum()),
            ],
        }
    )

    return {
        "kpi_summary": kpi_summary,
        "category_performance": category_performance,
        "regional_performance": regional_performance,
        "payment_performance": payment_performance,
        "monthly_trend": monthly_trend,
        "data_quality_audit": data_quality_audit,
    }
