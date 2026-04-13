from __future__ import annotations

import json

from amazon_sales_analysis.config import PROJECT_ROOT, Settings
from amazon_sales_analysis.serving.operations import latest_operational_summary


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


def test_latest_operational_summary_reads_latest_run_artifacts(tmp_path) -> None:
    settings = _settings(tmp_path)
    run_dir = settings.pipeline_runs_dir / "20260318T120000Z-run"
    run_dir.mkdir(parents=True, exist_ok=True)
    quality_path = run_dir / "quality_gates.json"
    regression_path = run_dir / "metrics_regression.json"
    warehouse_path = run_dir / "warehouse_validation.json"
    metrics_path = settings.metrics_dir / "run_metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps({"total_revenue": 100.0}), encoding="utf-8")
    quality_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    regression_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    warehouse_path.write_text(json.dumps({"status": "materialized"}), encoding="utf-8")
    (run_dir / "execution_manifest.json").write_text(
        json.dumps(
            {
                "run_id": "20260318T120000Z-run",
                "started_at_utc": "2026-03-18T12:00:00+00:00",
                "pipeline_version": "1.0.0",
                "row_counts": {"raw": 10, "clean": 9, "alerts": 1},
                "outputs": {
                    "metrics": {"path": str(metrics_path)},
                    "layers": {
                        "quality_gates": {"path": str(quality_path)},
                        "metrics_regression": {"path": str(regression_path)},
                        "warehouse_validation": {"path": str(warehouse_path)},
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    summary = latest_operational_summary(settings=settings)

    assert summary["run_id"] == "20260318T120000Z-run"
    assert summary["overall_status"] == "healthy"
    assert summary["quality_gates"]["status"] == "pass"
    assert summary["run_status"]["status"] == "missing"


def test_latest_operational_summary_uses_run_status_when_manifest_is_missing(tmp_path) -> None:
    settings = _settings(tmp_path)
    failed_run_dir = settings.pipeline_runs_dir / "20260320T120000Z-failed"
    failed_run_dir.mkdir(parents=True, exist_ok=True)
    (failed_run_dir / "run_status.json").write_text(
        json.dumps(
            {
                "run_id": "20260320T120000Z-failed",
                "started_at_utc": "2026-03-20T12:00:00+00:00",
                "status": "failed",
                "error_message": "quality gate failed",
            }
        ),
        encoding="utf-8",
    )

    summary = latest_operational_summary(settings=settings)

    assert summary["run_id"] == "20260320T120000Z-failed"
    assert summary["overall_status"] == "attention"
    assert summary["run_status"]["status"] == "failed"
    assert summary["quality_gates"]["status"] == "missing"


def test_latest_operational_summary_prioritizes_newer_failed_status_over_older_manifest(
    tmp_path,
) -> None:
    settings = _settings(tmp_path)
    successful_run_dir = settings.pipeline_runs_dir / "20260319T120000Z-success"
    successful_run_dir.mkdir(parents=True, exist_ok=True)
    quality_path = successful_run_dir / "quality_gates.json"
    regression_path = successful_run_dir / "metrics_regression.json"
    warehouse_path = successful_run_dir / "warehouse_validation.json"
    metrics_path = settings.metrics_dir / "run_metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps({"total_revenue": 100.0}), encoding="utf-8")
    quality_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    regression_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    warehouse_path.write_text(json.dumps({"status": "materialized"}), encoding="utf-8")
    (successful_run_dir / "execution_manifest.json").write_text(
        json.dumps(
            {
                "run_id": "20260319T120000Z-success",
                "started_at_utc": "2026-03-19T12:00:00+00:00",
                "pipeline_version": "1.0.0",
                "row_counts": {"raw": 10, "clean": 9, "alerts": 1},
                "outputs": {
                    "metrics": {"path": str(metrics_path)},
                    "layers": {
                        "quality_gates": {"path": str(quality_path)},
                        "metrics_regression": {"path": str(regression_path)},
                        "warehouse_validation": {"path": str(warehouse_path)},
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    failed_run_dir = settings.pipeline_runs_dir / "20260320T120000Z-failed"
    failed_run_dir.mkdir(parents=True, exist_ok=True)
    (failed_run_dir / "run_status.json").write_text(
        json.dumps(
            {
                "run_id": "20260320T120000Z-failed",
                "started_at_utc": "2026-03-20T12:00:00+00:00",
                "status": "failed",
            }
        ),
        encoding="utf-8",
    )

    summary = latest_operational_summary(settings=settings)

    assert summary["run_id"] == "20260320T120000Z-failed"
    assert summary["run_status"]["status"] == "failed"
    assert summary["overall_status"] == "attention"
