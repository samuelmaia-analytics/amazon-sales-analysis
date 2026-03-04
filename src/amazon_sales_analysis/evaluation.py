import pandas as pd


def calculate_business_impact(df: pd.DataFrame, recovery_rate: float = 0.05) -> dict[str, float]:
    total_revenue = float(df["total_revenue"].sum())
    gross_revenue = (
        float(df["gross_revenue"].sum())
        if "gross_revenue" in df
        else float((df["price"] * df["quantity_sold"]).sum())
    )

    discount_leakage = gross_revenue - total_revenue
    expected_uplift = discount_leakage * recovery_rate
    retained_ratio = (total_revenue / gross_revenue) if gross_revenue else 0.0

    return {
        "total_revenue": total_revenue,
        "gross_revenue": gross_revenue,
        "discount_leakage": discount_leakage,
        "retained_ratio": retained_ratio,
        "expected_uplift": expected_uplift,
    }


def build_executive_summary(df: pd.DataFrame) -> pd.DataFrame:
    impact = calculate_business_impact(df)
    summary = pd.DataFrame(
        {
            "metric": [
                "north_star_net_revenue_retained",
                "total_revenue",
                "gross_revenue",
                "discount_leakage",
                "expected_uplift_5pct_recovery",
            ],
            "value": [
                impact["retained_ratio"],
                impact["total_revenue"],
                impact["gross_revenue"],
                impact["discount_leakage"],
                impact["expected_uplift"],
            ],
        }
    )
    return summary
