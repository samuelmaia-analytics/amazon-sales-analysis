from __future__ import annotations

import json

from amazon_sales_analysis.config import Settings, build_settings
from amazon_sales_analysis.pipelines.runtime import (
    PipelineRunContext,
    prune_pipeline_runs,
    publish_latest_artifact,
    write_json_artifact,
)


def test_build_settings_reads_environment_variables(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AMAZON_SALES_ENV", "prod")
    monkeypatch.setenv("AMAZON_SALES_DATA_DIR", str(tmp_path / "custom-data"))
    monkeypatch.setenv("AMAZON_SALES_REPORTS_DIR", str(tmp_path / "custom-reports"))
    monkeypatch.setenv("AMAZON_SALES_ENABLE_DOWNLOAD", "false")
    monkeypatch.setenv("AMAZON_SALES_LOG_LEVEL", "debug")

    settings = build_settings()

    assert settings.environment == "prod"
    assert settings.data_dir == (tmp_path / "custom-data").resolve()
    assert settings.reports_dir == (tmp_path / "custom-reports").resolve()
    assert settings.enable_dataset_download is False
    assert settings.log_level == "DEBUG"
    assert settings.bronze_data_dir == (tmp_path / "custom-data" / "bronze").resolve()
    assert settings.kpi_regression_tolerance_pct == 0.15
    assert settings.warehouse_materialization_mode == "replace"


def test_pipeline_run_context_writes_manifest(tmp_path) -> None:
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
    context = PipelineRunContext.create(settings)
    payload = context.manifest_payload(
        pipeline_version="1.0.0",
        dataset_path=tmp_path / "data" / "raw" / "amazon_sales_dataset.csv",
        processed_output_path=tmp_path / "data" / "processed" / "amazon_sales_clean.csv",
        contract_snapshot_path=tmp_path / "contracts" / "sales_dataset.contract.json",
        metrics_path=tmp_path / "reports" / "metrics" / "product_metrics.json",
        alerts_path=tmp_path / "reports" / "tables" / "discount_spike_alerts.csv",
        table_outputs={"kpi_summary": tmp_path / "reports" / "tables" / "kpi_summary.csv"},
        recommendations_path=tmp_path / "reports" / "tables" / "actionable_recommendations.csv",
        insights_path=tmp_path / "reports" / "tables" / "executive_insights.csv",
        row_counts={"raw": 10, "clean": 9, "featured": 9, "alerts": 1},
    )

    write_json_artifact(payload, context.manifest_path)

    stored = json.loads(context.manifest_path.read_text(encoding="utf-8"))
    assert stored["run_id"] == context.run_id
    assert stored["row_counts"]["clean"] == 9
    assert stored["status"] == "succeeded"
    assert stored["duration_seconds"] >= 0
    assert "sha256" in stored["outputs"]["metrics"]


def test_publish_latest_artifact_overwrites_target_atomically(tmp_path) -> None:
    source = tmp_path / "runs" / "run-1" / "metrics.json"
    target = tmp_path / "reports" / "metrics" / "product_metrics.json"
    source.parent.mkdir(parents=True, exist_ok=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    source.write_text('{"value": 10}', encoding="utf-8")
    target.write_text('{"value": 1}', encoding="utf-8")

    published_path = publish_latest_artifact(source, target)

    assert published_path == target
    assert target.read_text(encoding="utf-8") == '{"value": 10}'


def test_prune_pipeline_runs_removes_older_run_directories(tmp_path) -> None:
    runs_dir = tmp_path / "reports" / "runs"
    recent = runs_dir / "20260319T120000Z-bbbb"
    middle = runs_dir / "20260318T120000Z-aaaa"
    old = runs_dir / "20260317T120000Z-9999"
    for path in [recent, middle, old]:
        path.mkdir(parents=True, exist_ok=True)

    removed = prune_pipeline_runs(runs_dir, keep_last_runs=2)

    assert old in removed
    assert recent.exists()
    assert middle.exists()
    assert not old.exists()
