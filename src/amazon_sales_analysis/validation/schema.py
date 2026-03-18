from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

try:
    import pandera.pandas as pandera
except ModuleNotFoundError:  # pragma: no cover - exercised in environments without pandera
    pandera = None


if pandera is not None:
    sales_schema = pandera.DataFrameSchema(
        {
            "order_id": pandera.Column(float, nullable=False, coerce=True),
            "order_date": pandera.Column(str, nullable=False, coerce=True),
            "product_id": pandera.Column(float, nullable=False, coerce=True),
            "product_category": pandera.Column(str, nullable=False, coerce=True),
            "price": pandera.Column(float, nullable=False, coerce=True, checks=pandera.Check.ge(0)),
            "discount_percent": pandera.Column(
                float,
                nullable=False,
                coerce=True,
                checks=[pandera.Check.ge(0), pandera.Check.le(100)],
            ),
            "quantity_sold": pandera.Column(
                float, nullable=False, coerce=True, checks=pandera.Check.gt(0)
            ),
            "customer_region": pandera.Column(str, nullable=True, coerce=True),
            "payment_method": pandera.Column(str, nullable=True, coerce=True),
            "rating": pandera.Column(
                float, nullable=True, coerce=True, checks=[pandera.Check.ge(0), pandera.Check.le(5)]
            ),
            "review_count": pandera.Column(
                float, nullable=True, coerce=True, checks=pandera.Check.ge(0)
            ),
            "discounted_price": pandera.Column(
                float, nullable=True, coerce=True, checks=pandera.Check.ge(0)
            ),
            "total_revenue": pandera.Column(
                float, nullable=True, coerce=True, checks=pandera.Check.ge(0)
            ),
        },
        strict=False,
        coerce=True,
    )
else:

    @dataclass
    class _FallbackSchema:
        def validate(self, df: pd.DataFrame, lazy: bool = True) -> pd.DataFrame:
            del lazy
            required_columns = {
                "order_id",
                "order_date",
                "product_id",
                "product_category",
                "price",
                "discount_percent",
                "quantity_sold",
            }
            missing_columns = required_columns - set(df.columns)
            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise ValueError(f"Missing required columns for validation: {missing}")
            if (pd.to_numeric(df["quantity_sold"], errors="coerce") <= 0).any():
                raise ValueError("quantity_sold must be > 0")
            return df

    sales_schema = _FallbackSchema()
