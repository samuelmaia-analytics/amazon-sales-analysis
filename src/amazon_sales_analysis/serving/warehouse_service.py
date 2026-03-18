from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pandas as pd

from ..config import Settings, get_settings
from ..pipelines.runtime import write_dataframe_artifact
from ..transformations.data_preprocessing import read_sales_dataset
from .warehouse import WAREHOUSE_TABLE_NAME, duckdb_available, warehouse_validation_query


def _latest_gold_snapshot(settings: Settings) -> Path:
    candidates = sorted(settings.gold_data_dir.glob("*_commercial_mart.csv"), reverse=True)
    if not candidates:
        raise FileNotFoundError("Gold mart snapshot not found. Run the pipeline first.")
    return candidates[0]


def query_category_revenue(settings: Settings | None = None) -> pd.DataFrame:
    resolved_settings = settings or get_settings()

    if duckdb_available() and resolved_settings.warehouse_db_path.exists():
        import duckdb

        connection = duckdb.connect(str(resolved_settings.warehouse_db_path), read_only=True)
        try:
            return cast(pd.DataFrame, connection.execute(warehouse_validation_query()).fetchdf())
        finally:
            connection.close()

    gold_snapshot = _latest_gold_snapshot(resolved_settings)
    frame = read_sales_dataset(gold_snapshot)
    frame["order_date"] = pd.to_datetime(frame["order_date"], errors="coerce")
    result = (
        frame.groupby("product_category", as_index=False)
        .agg(
            revenue=("total_revenue", "sum"),
            orders=("order_id", "nunique"),
            avg_discount_percent=("discount_percent", "mean"),
        )
        .sort_values("revenue", ascending=False)
        .reset_index(drop=True)
    )
    result["revenue"] = result["revenue"].round(2)
    result["avg_discount_percent"] = result["avg_discount_percent"].round(2)
    return result


def export_category_revenue_query(
    output_path: Path | None = None, *, settings: Settings | None = None
) -> Path:
    resolved_settings = settings or get_settings()
    target = output_path or (resolved_settings.tables_dir / "warehouse_category_revenue.csv")
    result = query_category_revenue(resolved_settings)
    return write_dataframe_artifact(result, target)


def warehouse_query_metadata(settings: Settings | None = None) -> dict[str, Any]:
    resolved_settings = settings or get_settings()
    return {
        "warehouse_db_path": str(resolved_settings.warehouse_db_path),
        "warehouse_table": WAREHOUSE_TABLE_NAME,
        "duckdb_available": duckdb_available(),
    }
