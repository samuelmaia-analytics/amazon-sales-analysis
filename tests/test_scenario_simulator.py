import pandas as pd

from amazon_sales_analysis.feature_engineering import build_features
from amazon_sales_analysis.scenario_simulator import simulate_leakage_recovery


def _fixture_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": [1, 2, 3],
            "order_date": ["2024-01-15", "2024-01-20", "2024-01-30"],
            "product_id": [10, 11, 12],
            "product_category": ["Electronics", "Beauty", "Electronics"],
            "price": [100.0, 200.0, 80.0],
            "discount_percent": [10, 20, 5],
            "quantity_sold": [2, 1, 3],
            "customer_region": ["North", "South", "North"],
            "payment_method": ["Card", "Pix", "Card"],
            "rating": [4.8, 4.4, 4.6],
            "review_count": [50, 20, 15],
            "discounted_price": [90.0, 160.0, 76.0],
            "total_revenue": [180.0, 160.0, 228.0],
        }
    )


def test_simulate_leakage_recovery_returns_expected_outputs() -> None:
    featured = build_features(_fixture_df())
    simulation = simulate_leakage_recovery(
        featured,
        recovery_rates={"Electronics": 0.2, "Beauty": 0.1},
    )

    assert simulation["baseline_revenue"] == 568.0
    assert simulation["gross_revenue"] == 640.0
    assert simulation["total_uplift"] == 10.4
    assert simulation["simulated_revenue"] == 578.4
    assert "category_breakdown" in simulation
