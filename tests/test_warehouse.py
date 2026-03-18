from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import pandas as pd

from amazon_sales_analysis.config import PROJECT_ROOT, Settings
from amazon_sales_analysis.warehouse import materialize_gold_mart


def _settings(tmp_path) -> Settings:
    return Settings(
        environment="test",
        project_root=PROJECT_ROOT,
        data_dir=tmp_path / "data",
        raw_data_dir=tmp_path / "data" / "raw",
        bronze_data_dir=tmp_path / "data" / "bronze",
        silver_data_dir=tmp_path / "data" / "silver",
        gold_data_dir=tmp_path / "data" / "gold",
        warehouse_dir=tmp_path / "data" / "warehouse",
        warehouse_db_path=tmp_path / "data" / "warehouse" / "amazon_sales.duckdb",
        processed_data_dir=tmp_path / "data" / "processed",
        external_data_dir=tmp_path / "data" / "external",
        reports_dir=tmp_path / "reports",
        figures_dir=tmp_path / "reports" / "figures",
        tables_dir=tmp_path / "reports" / "tables",
        metrics_dir=tmp_path / "reports" / "metrics",
        contracts_dir=tmp_path / "contracts",
        pipeline_runs_dir=tmp_path / "reports" / "runs",
        kaggle_dataset="demo/dataset",
        log_level="INFO",
        enable_dataset_download=True,
        max_data_staleness_days=45,
        kpi_regression_tolerance_pct=0.15,
        warehouse_materialization_mode="replace",
    )


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": [1, 2],
            "order_date": ["2026-03-01", "2026-03-02"],
            "product_id": [10, 11],
            "product_category": ["Beauty", "Books"],
            "price": [100.0, 50.0],
            "discount_percent": [10.0, 20.0],
            "quantity_sold": [1, 2],
            "total_revenue": [90.0, 80.0],
        }
    )


def test_materialize_gold_mart_gracefully_skips_without_duckdb(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("amazon_sales_analysis.warehouse.duckdb_available", lambda: False)

    result = materialize_gold_mart(_frame(), settings=_settings(tmp_path))

    payload = json.loads(result.validation_output_path.read_text(encoding="utf-8"))
    assert result.status == "skipped"
    assert payload["reason"] == "duckdb_not_installed"
    assert result.materialization_mode == "replace"


def test_materialize_gold_mart_uses_duckdb_when_available(tmp_path, monkeypatch) -> None:
    executed_queries: list[str] = []

    class FakeConnection:
        def register(self, name: str, df: pd.DataFrame) -> None:
            assert name == "featured_df"
            assert not df.empty

        def execute(self, query: str) -> FakeConnection:
            executed_queries.append(query)
            return self

        def fetchdf(self) -> pd.DataFrame:
            return pd.DataFrame({"product_category": ["Beauty"], "revenue": [90.0]})

        def close(self) -> None:
            return None

    fake_duckdb = SimpleNamespace(connect=lambda _: FakeConnection())
    monkeypatch.setattr("amazon_sales_analysis.warehouse.duckdb_available", lambda: True)
    monkeypatch.setitem(sys.modules, "duckdb", fake_duckdb)

    result = materialize_gold_mart(_frame(), settings=_settings(tmp_path))

    payload = json.loads(result.validation_output_path.read_text(encoding="utf-8"))
    assert result.status == "materialized"
    assert any(
        "CREATE OR REPLACE TABLE gold_commercial_performance" in query for query in executed_queries
    )
    assert payload["status"] == "materialized"


def test_materialize_gold_mart_appends_history_when_configured(tmp_path, monkeypatch) -> None:
    executed_queries: list[str] = []

    class FakeConnection:
        def register(self, name: str, df: pd.DataFrame) -> None:
            assert name in {"featured_df", "history_df"}
            assert not df.empty

        def execute(self, query: str) -> FakeConnection:
            executed_queries.append(query)
            return self

        def fetchdf(self) -> pd.DataFrame:
            return pd.DataFrame({"product_category": ["Beauty"], "revenue": [90.0]})

        def close(self) -> None:
            return None

    fake_duckdb = SimpleNamespace(connect=lambda _: FakeConnection())
    monkeypatch.setattr("amazon_sales_analysis.warehouse.duckdb_available", lambda: True)
    monkeypatch.setitem(sys.modules, "duckdb", fake_duckdb)
    settings = _settings(tmp_path)
    settings = Settings(**{**settings.__dict__, "warehouse_materialization_mode": "append_history"})

    result = materialize_gold_mart(_frame(), settings=settings, run_id="run-123")

    assert result.materialization_mode == "append_history"
    assert any("gold_commercial_performance_history" in query for query in executed_queries)
