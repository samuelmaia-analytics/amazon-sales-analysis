import pandas as pd
import pytest

from amazon_sales_analysis.data_preprocessing import (
    clean_sales_data,
    read_sales_dataset,
    validate_raw_sales_data,
)


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


def test_required_columns_are_validated() -> None:
    invalid_df = _base_df().drop(columns=["rating"])

    with pytest.raises(ValueError, match="Colunas obrigatorias ausentes"):
        clean_sales_data(invalid_df)


def test_discount_rating_and_revenue_are_normalized() -> None:
    frame = _base_df()
    frame.loc[0, "discount_percent"] = 120
    frame.loc[0, "rating"] = 7

    cleaned = clean_sales_data(frame)

    assert cleaned.loc[0, "discount_percent"] == 100
    assert cleaned.loc[0, "rating"] == 5
    assert cleaned.loc[0, "discounted_price"] == 0
    assert cleaned.loc[0, "total_revenue"] == 0


def test_clean_sales_data_deduplicates_business_key() -> None:
    frame = pd.concat([_base_df(), _base_df()], ignore_index=True)

    cleaned = clean_sales_data(frame)

    assert len(cleaned) == 1


def test_pandera_schema_validation_rejects_invalid_quantity() -> None:
    invalid_df = _base_df()
    invalid_df.loc[0, "quantity_sold"] = 0

    with pytest.raises(ValueError, match="pandera"):
        validate_raw_sales_data(invalid_df)


def test_read_sales_dataset_raises_clear_error_for_missing_file(tmp_path) -> None:
    missing_path = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError, match="Arquivo de vendas nao encontrado"):
        read_sales_dataset(missing_path)
