import pandas as pd


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    frame["order_date"] = pd.to_datetime(frame["order_date"], errors="coerce")

    frame["year"] = frame["order_date"].dt.year
    frame["month"] = frame["order_date"].dt.month
    frame["month_name"] = frame["order_date"].dt.strftime("%B")
    frame["quarter"] = frame["order_date"].dt.quarter
    frame["day_of_week"] = frame["order_date"].dt.strftime("%A")
    frame["is_weekend"] = frame["day_of_week"].isin(["Saturday", "Sunday"])

    frame["gross_revenue"] = frame["price"] * frame["quantity_sold"]
    frame["discount_value"] = frame["gross_revenue"] - frame["total_revenue"]
    frame["net_revenue_retained"] = frame["total_revenue"] / frame["gross_revenue"].replace(
        0, pd.NA
    )

    frame["revenue_per_unit"] = frame["total_revenue"] / frame["quantity_sold"].replace(0, pd.NA)
    frame["discount_impact_pct"] = (
        frame["discount_value"] / frame["gross_revenue"].replace(0, pd.NA)
    ) * 100

    return frame.fillna(
        {"revenue_per_unit": 0, "discount_impact_pct": 0, "net_revenue_retained": 0}
    )
