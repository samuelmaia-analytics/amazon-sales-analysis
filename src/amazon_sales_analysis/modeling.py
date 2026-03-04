import pandas as pd


def rank_discount_opportunities(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    grouped = (
        df.groupby("product_category", as_index=False)
        .agg(total_revenue=("total_revenue", "sum"), discount_value=("discount_value", "sum"))
        .sort_values("discount_value", ascending=False)
        .head(top_n)
    )
    grouped["discount_to_revenue_ratio"] = grouped["discount_value"] / grouped[
        "total_revenue"
    ].replace(0, pd.NA)
    return grouped.fillna({"discount_to_revenue_ratio": 0})
