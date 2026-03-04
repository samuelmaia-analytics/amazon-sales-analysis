import pandas as pd
import pytest

from amazon_sales_analysis.contracts import RAW_REQUIRED_COLUMNS, enforce_raw_contract


def _base_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": [1],
            "order_date": ["2024-01-15"],
            "product_id": [10],
            "product_category": ["Electronics"],
            "price": [100.0],
            "discount_percent": [10],
            "quantity_sold": [2],
            "customer_region": ["North"],
            "payment_method": ["Card"],
            "rating": [4.8],
            "review_count": [50],
            "discounted_price": [90.0],
            "total_revenue": [180.0],
        }
    )


def test_raw_contract_accepts_valid_dataset() -> None:
    enforce_raw_contract(_base_df())


def test_raw_contract_rejects_missing_columns() -> None:
    frame = _base_df().drop(columns=["order_id"])
    with pytest.raises(ValueError, match="Colunas obrigatorias ausentes"):
        enforce_raw_contract(frame)


def test_required_columns_are_stable() -> None:
    assert len(RAW_REQUIRED_COLUMNS) == 13
