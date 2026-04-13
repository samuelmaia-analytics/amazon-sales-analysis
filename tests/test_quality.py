import pandas as pd
import pytest

from amazon_sales_analysis.config import Settings
from amazon_sales_analysis.quality import (
    enforce_clean_quality_gates,
    export_quality_gate_report,
    summarize_quality_gates,
)


def _base_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": [1, 2],
            "product_id": [10, 11],
            "order_date": ["2026-03-01", "2026-03-02"],
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


def test_quality_gate_rejects_stale_dataset(tmp_path) -> None:
    frame = _base_df()
    frame["order_date"] = ["2020-01-01", "2020-01-02"]
    settings = Settings(
        environment="test",
        project_root=tmp_path,
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
        max_data_staleness_days=30,
        kpi_regression_tolerance_pct=0.15,
        warehouse_materialization_mode="replace",
    )

    with pytest.raises(ValueError, match="data_freshness_days"):
        enforce_clean_quality_gates(frame, settings=settings)


def test_quality_summary_includes_thresholds() -> None:
    summary = summarize_quality_gates(_base_df())

    assert {"check", "status", "value", "threshold", "message"} <= set(summary.columns)


def test_quality_report_is_exported(tmp_path) -> None:
    settings = Settings(
        environment="test",
        project_root=tmp_path,
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

    output_path = export_quality_gate_report(
        _base_df(),
        settings=settings,
        output_path=tmp_path / "runs" / "run-1" / "metrics" / "quality_gates.json",
    )

    assert output_path.exists()
