from __future__ import annotations

from typing import Any

import pandas as pd

from amazon_sales_analysis.serving import warehouse as _impl

WAREHOUSE_TABLE_NAME = _impl.WAREHOUSE_TABLE_NAME
WAREHOUSE_VIEW_NAME = _impl.WAREHOUSE_VIEW_NAME
WAREHOUSE_HISTORY_TABLE_NAME = _impl.WAREHOUSE_HISTORY_TABLE_NAME
WarehouseMaterializationResult = _impl.WarehouseMaterializationResult
warehouse_validation_query = _impl.warehouse_validation_query
warehouse_bootstrap_queries = _impl.warehouse_bootstrap_queries


def duckdb_available() -> bool:
    return _impl.duckdb_available()


def materialize_gold_mart(
    df: pd.DataFrame, *, settings: Any | None = None, run_id: str | None = None
) -> WarehouseMaterializationResult:
    _impl.duckdb_available = duckdb_available
    return _impl.materialize_gold_mart(df, settings=settings, run_id=run_id)
