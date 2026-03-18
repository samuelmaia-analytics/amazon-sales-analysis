from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from amazon_sales_analysis.serving import warehouse_service as _impl
from amazon_sales_analysis.warehouse import duckdb_available


def query_category_revenue(settings: Any | None = None) -> pd.DataFrame:
    _impl.duckdb_available = duckdb_available
    return _impl.query_category_revenue(settings=settings)


def export_category_revenue_query(
    output_path: Path | None = None, *, settings: Any | None = None
) -> Path:
    _impl.duckdb_available = duckdb_available
    return _impl.export_category_revenue_query(output_path=output_path, settings=settings)


def warehouse_query_metadata(settings: Any | None = None) -> dict[str, Any]:
    _impl.duckdb_available = duckdb_available
    return _impl.warehouse_query_metadata(settings=settings)
