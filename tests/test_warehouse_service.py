from __future__ import annotations

import sys
from types import SimpleNamespace

import pandas as pd

from amazon_sales_analysis.config import PROJECT_ROOT, Settings
from amazon_sales_analysis.warehouse_service import query_category_revenue


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


def test_query_category_revenue_falls_back_to_gold_snapshot(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.gold_data_dir.mkdir(parents=True, exist_ok=True)
    snapshot = settings.gold_data_dir / "20260318T120000Z_commercial_mart.csv"
    pd.DataFrame(
        {
            "order_id": [1, 2],
            "order_date": ["2026-03-01", "2026-03-02"],
            "product_category": ["Beauty", "Beauty"],
            "discount_percent": [10.0, 20.0],
            "total_revenue": [90.0, 80.0],
        }
    ).to_csv(snapshot, index=False)
    monkeypatch.setattr("amazon_sales_analysis.warehouse_service.duckdb_available", lambda: False)

    result = query_category_revenue(settings)

    assert result.loc[0, "product_category"] == "Beauty"
    assert result.loc[0, "revenue"] == 170.0


def test_query_category_revenue_uses_duckdb_when_available(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.warehouse_dir.mkdir(parents=True, exist_ok=True)
    settings.warehouse_db_path.write_text("placeholder", encoding="utf-8")

    class FakeConnection:
        def execute(self, query: str) -> FakeConnection:
            assert "FROM gold_commercial_performance" in query
            return self

        def fetchdf(self) -> pd.DataFrame:
            return pd.DataFrame({"product_category": ["Books"], "revenue": [50.0]})

        def close(self) -> None:
            return None

    fake_duckdb = SimpleNamespace(connect=lambda *args, **kwargs: FakeConnection())
    monkeypatch.setattr("amazon_sales_analysis.warehouse_service.duckdb_available", lambda: True)
    monkeypatch.setitem(sys.modules, "duckdb", fake_duckdb)

    result = query_category_revenue(settings)

    assert result.loc[0, "product_category"] == "Books"
