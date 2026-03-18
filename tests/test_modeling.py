import pandas as pd
import pytest

from amazon_sales_analysis.modeling import rank_discount_opportunities


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "product_category": ["Beauty", "Books"],
            "total_revenue": [90.0, 80.0],
            "discount_value": [10.0, 5.0],
        }
    )


def test_rank_discount_opportunities_returns_sorted_ratios() -> None:
    ranked = rank_discount_opportunities(_frame(), top_n=1)

    assert len(ranked) == 1
    assert ranked.iloc[0]["product_category"] == "Beauty"
    assert ranked.iloc[0]["discount_to_revenue_ratio"] == 10.0 / 90.0


def test_rank_discount_opportunities_rejects_missing_columns() -> None:
    with pytest.raises(ValueError, match="Missing required columns"):
        rank_discount_opportunities(pd.DataFrame({"product_category": ["Beauty"]}))


def test_rank_discount_opportunities_rejects_non_positive_top_n() -> None:
    with pytest.raises(ValueError, match="top_n"):
        rank_discount_opportunities(_frame(), top_n=0)
