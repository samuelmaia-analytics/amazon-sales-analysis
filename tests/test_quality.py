import pandas as pd
import pytest

from amazon_sales_analysis.quality import enforce_clean_quality_gates


def _base_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "discount_percent": [10.0, 20.0],
            "rating": [4.5, 3.8],
            "quantity_sold": [2, 1],
            "price": [100.0, 50.0],
        }
    )


def test_quality_gate_accepts_valid_dataset() -> None:
    enforce_clean_quality_gates(_base_df())


@pytest.mark.parametrize(
    ("column", "value", "error_match"),
    [
        ("discount_percent", 120.0, "discount_percent"),
        ("rating", 7.0, "rating"),
        ("quantity_sold", 0, "quantity_sold"),
        ("price", -1.0, "price"),
    ],
)
def test_quality_gate_rejects_invalid_domain(column: str, value: float, error_match: str) -> None:
    frame = _base_df()
    frame.loc[0, column] = value

    with pytest.raises(ValueError, match=error_match):
        enforce_clean_quality_gates(frame)
