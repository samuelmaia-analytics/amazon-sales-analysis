from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

try:
    import pandera.pandas as pa
except ModuleNotFoundError:  # pragma: no cover - exercised in environments without pandera
    pa = None


if pa is not None:
    sales_schema = pa.DataFrameSchema(
        {
            "order_id": pa.Column(float, nullable=False, coerce=True),
            "order_date": pa.Column(str, nullable=False, coerce=True),
            "product_id": pa.Column(float, nullable=False, coerce=True),
            "product_category": pa.Column(str, nullable=False, coerce=True),
            "price": pa.Column(float, nullable=False, coerce=True, checks=pa.Check.ge(0)),
            "discount_percent": pa.Column(
                float, nullable=False, coerce=True, checks=[pa.Check.ge(0), pa.Check.le(100)]
            ),
            "quantity_sold": pa.Column(float, nullable=False, coerce=True, checks=pa.Check.gt(0)),
            "customer_region": pa.Column(str, nullable=True, coerce=True),
            "payment_method": pa.Column(str, nullable=True, coerce=True),
            "rating": pa.Column(
                float, nullable=True, coerce=True, checks=[pa.Check.ge(0), pa.Check.le(5)]
            ),
            "review_count": pa.Column(float, nullable=True, coerce=True, checks=pa.Check.ge(0)),
            "discounted_price": pa.Column(float, nullable=True, coerce=True, checks=pa.Check.ge(0)),
            "total_revenue": pa.Column(float, nullable=True, coerce=True, checks=pa.Check.ge(0)),
        },
        strict=False,
        coerce=True,
    )
else:

    @dataclass
    class _FallbackSchema:
        def validate(self, df: pd.DataFrame, lazy: bool = True) -> pd.DataFrame:
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
