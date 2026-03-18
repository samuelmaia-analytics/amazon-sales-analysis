from __future__ import annotations

import json

from amazon_sales_analysis.config import PROJECT_ROOT, Settings
from amazon_sales_analysis.run_history import compare_latest_runs, summarize_run_history


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


def _write_run(settings: Settings, run_id: str, revenue: float, avg_ticket: float) -> None:
    run_dir = settings.pipeline_runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = settings.metrics_dir / f"{run_id}_metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(
            {
                "total_revenue": revenue,
                "gross_revenue": revenue + 10,
                "discount_leakage": 10.0,
                "north_star_nrr": 0.9,
                "total_orders": 2,
                "avg_ticket": avg_ticket,
                "clean_row_count": 2,
                "row_retention_rate": 1.0,
            }
        ),
        encoding="utf-8",
    )
    manifest = {
        "run_id": run_id,
        "started_at_utc": run_id,
        "completed_at_utc": run_id,
        "duration_seconds": 1.5,
        "status": "succeeded",
        "pipeline_version": "1.0.0",
        "row_counts": {"raw": 2, "clean": 2, "alerts": 0},
        "outputs": {"metrics": {"path": str(metrics_path)}},
    }
    (run_dir / "execution_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_summarize_run_history_returns_latest_runs(tmp_path) -> None:
    settings = _settings(tmp_path)
    _write_run(settings, "20260318T120000Z-a", 100.0, 50.0)
    _write_run(settings, "20260319T120000Z-b", 120.0, 60.0)

    runs = summarize_run_history(settings=settings)

    assert runs[0]["run_id"] == "20260319T120000Z-b"
    assert runs[0]["status"] == "succeeded"
    assert runs[0]["duration_seconds"] == 1.5
    assert runs[1]["run_id"] == "20260318T120000Z-a"


def test_compare_latest_runs_returns_kpi_deltas(tmp_path) -> None:
    settings = _settings(tmp_path)
    _write_run(settings, "20260318T120000Z-a", 100.0, 50.0)
    _write_run(settings, "20260319T120000Z-b", 120.0, 60.0)

    comparison = compare_latest_runs(settings=settings)

    assert comparison["latest_run_id"] == "20260319T120000Z-b"
    assert comparison["kpi_deltas"]["total_revenue"]["delta"] == 20.0
    assert comparison["kpi_deltas"]["total_revenue"]["severity"] == "critical"
    assert comparison["overall_severity"] == "critical"
