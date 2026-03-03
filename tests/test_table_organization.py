import pandas as pd

from amazon_sales_analysis.feature_engineering import build_features
from amazon_sales_analysis.table_organization import build_executive_tables


def _fixture_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": [1, 2, 3],
            "order_date": ["2024-01-15", "2024-02-10", "2024-02-18"],
            "product_id": [10, 11, 12],
            "product_category": ["Electronics", "Home", "Electronics"],
            "price": [100.0, 120.0, 80.0],
            "discount_percent": [10, 20, 5],
            "quantity_sold": [2, 1, 3],
            "customer_region": ["North", "South", "North"],
            "payment_method": ["Card", "Pix", "Card"],
            "rating": [4.8, 4.1, 4.6],
            "review_count": [50, 20, 15],
            "discounted_price": [90.0, 96.0, 76.0],
            "total_revenue": [180.0, 96.0, 228.0],
        }
    )


def test_build_executive_tables_returns_expected_tables() -> None:
    featured = build_features(_fixture_df())
    tables = build_executive_tables(featured)

    expected_keys = {
        "kpi_summary",
        "category_performance",
        "regional_performance",
        "payment_performance",
        "monthly_trend",
        "data_quality_audit",
    }

    assert set(tables.keys()) == expected_keys
    assert not tables["kpi_summary"].empty
    assert "month_end" in tables["monthly_trend"].columns
