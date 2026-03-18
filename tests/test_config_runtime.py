from __future__ import annotations

import json

from amazon_sales_analysis.config import Settings, build_settings
from amazon_sales_analysis.pipelines.runtime import PipelineRunContext, write_json_artifact


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
    assert "sha256" in stored["outputs"]["metrics"]
