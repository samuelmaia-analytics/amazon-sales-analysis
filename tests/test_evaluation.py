import pandas as pd

from amazon_sales_analysis.evaluation import build_executive_summary, calculate_business_impact


def _featured_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "price": [100.0, 50.0],
            "quantity_sold": [2, 1],
            "total_revenue": [180.0, 40.0],
            "gross_revenue": [200.0, 50.0],
        }
    )


def test_calculate_business_impact_uses_gross_revenue_when_available() -> None:
    impact = calculate_business_impact(_featured_df(), recovery_rate=0.1)

    assert impact["gross_revenue"] == 250.0
    assert impact["total_revenue"] == 220.0
    assert impact["discount_leakage"] == 30.0
    assert impact["expected_uplift"] == 3.0


def test_calculate_business_impact_fallbacks_to_price_times_quantity() -> None:
    frame = _featured_df().drop(columns=["gross_revenue"])
    impact = calculate_business_impact(frame)

    assert impact["gross_revenue"] == 250.0
    assert impact["retained_ratio"] == 220.0 / 250.0


def test_build_executive_summary_has_expected_metrics() -> None:
    summary = build_executive_summary(_featured_df())
    expected = {
        "north_star_net_revenue_retained",
        "total_revenue",
        "gross_revenue",
        "discount_leakage",
        "expected_uplift_5pct_recovery",
    }
    assert set(summary["metric"]) == expected
