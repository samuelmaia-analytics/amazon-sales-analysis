import builtins
import json
import logging
import sys
import types
from pathlib import Path
from typing import Any, cast

import pandas as pd
import pytest

from amazon_sales_analysis.cli import alerts as alerts_cli
from amazon_sales_analysis.cli import pipeline as pipeline_cli
from amazon_sales_analysis.cli import scenario as scenario_cli
from amazon_sales_analysis.config import Settings
from amazon_sales_analysis.data_ingestion import download_amazon_sales_dataset
from amazon_sales_analysis.logging_config import configure_logging
from amazon_sales_analysis.pipelines.runtime import PipelineRunContext


def test_download_dataset_copies_files_from_kagglehub(tmp_path, monkeypatch) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source_file = source_dir / "amazon_sales_dataset.csv"
    source_file.write_text("order_id\n1\n", encoding="utf-8")

    fake_module = types.SimpleNamespace(dataset_download=lambda _: str(source_dir))
    monkeypatch.setitem(sys.modules, "kagglehub", fake_module)
    settings = Settings(
        environment="test",
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        raw_data_dir=tmp_path / "raw",
        bronze_data_dir=tmp_path / "bronze",
        silver_data_dir=tmp_path / "silver",
        gold_data_dir=tmp_path / "gold",
        warehouse_dir=tmp_path / "warehouse",
        warehouse_db_path=tmp_path / "warehouse" / "amazon_sales.duckdb",
        processed_data_dir=tmp_path / "processed",
        external_data_dir=tmp_path / "external",
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

    target_dir = download_amazon_sales_dataset(settings=settings)

    copied_file = target_dir / "amazon_sales_dataset.csv"
    assert copied_file.exists()
    assert copied_file.read_text(encoding="utf-8") == source_file.read_text(encoding="utf-8")


def test_download_dataset_uses_existing_local_copy_when_kagglehub_is_missing(
    tmp_path, monkeypatch
) -> None:
    raw_dir = tmp_path / "raw"
    target_dir = raw_dir / "amazon_sales"
    target_dir.mkdir(parents=True)
    existing_file = target_dir / "amazon_sales_dataset.csv"
    existing_file.write_text("order_id\n1\n", encoding="utf-8")

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "kagglehub":
            raise ModuleNotFoundError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, "kagglehub", raising=False)
    monkeypatch.setattr(builtins, "__import__", fake_import)
    settings = Settings(
        environment="test",
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        raw_data_dir=raw_dir,
        bronze_data_dir=tmp_path / "bronze",
        silver_data_dir=tmp_path / "silver",
        gold_data_dir=tmp_path / "gold",
        warehouse_dir=tmp_path / "warehouse",
        warehouse_db_path=tmp_path / "warehouse" / "amazon_sales.duckdb",
        processed_data_dir=tmp_path / "processed",
        external_data_dir=tmp_path / "external",
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

    target = download_amazon_sales_dataset(settings=settings)

    assert target == target_dir


def test_configure_logging_delegates_to_basic_config(monkeypatch) -> None:
    monkeypatch.setattr(
        "amazon_sales_analysis.logging_config.get_settings",
        lambda: types.SimpleNamespace(environment="test", log_level="INFO"),
    )
    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)

    configure_logging(logging.DEBUG, run_id="run-123")

    assert root_logger.level == logging.DEBUG
    assert root_logger.handlers
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "message", (), None)
    for handler in root_logger.handlers:
        for log_filter in handler.filters:
            if callable(log_filter):
                log_filter(record)
            else:
                log_filter.filter(record)
    enriched_record = cast(Any, record)
    assert enriched_record.environment == "test"
    assert enriched_record.run_id == "run-123"

    root_logger.handlers.clear()
    root_logger.handlers.extend(original_handlers)


def test_scenario_cli_helpers_parse_and_merge_category_rates() -> None:
    overrides = scenario_cli.parse_category_rates("Beauty=0.1,Fashion=0.2")
    recovery_rates = scenario_cli.build_recovery_rates(["Beauty", "Books"], 0.05, overrides)

    assert overrides == {"Beauty": 0.1, "Fashion": 0.2}
    assert recovery_rates == {"Beauty": 0.1, "Books": 0.05, "Fashion": 0.2}


def test_scenario_cli_rejects_invalid_override_format() -> None:
    with pytest.raises(ValueError):
        scenario_cli.parse_category_rates("Beauty:0.1")


def test_scenario_cli_run_generates_artifacts(tmp_path) -> None:
    input_path = tmp_path / "clean.csv"
    output_dir = tmp_path / "reports"
    frame = pd.DataFrame(
        {
            "order_id": [1, 2],
            "order_date": ["2024-01-01", "2024-01-02"],
            "product_id": [10, 11],
            "product_category": ["Beauty", "Books"],
            "price": [100.0, 200.0],
            "discount_percent": [10.0, 20.0],
            "quantity_sold": [1, 1],
            "customer_region": ["North", "South"],
            "payment_method": ["Card", "Pix"],
            "rating": [4.8, 4.7],
            "review_count": [10, 20],
            "discounted_price": [90.0, 160.0],
            "total_revenue": [90.0, 160.0],
        }
    )
    frame.to_csv(input_path, index=False)

    scenario_cli.run(
        input_path=input_path,
        output_dir=output_dir,
        recovery_rate=0.05,
        category_rates="Beauty=0.1",
    )

    assert (output_dir / "scenario_simulation_breakdown.csv").exists()
    assert (output_dir / "scenario_simulation_summary.json").exists()


def test_alerts_cli_run_rejects_invalid_parameters(tmp_path) -> None:
    with pytest.raises(SystemExit):
        alerts_cli.run(
            input_path=tmp_path / "missing.csv",
            z_threshold=2.5,
            min_observations=5,
            summary_output=tmp_path / "summary.json",
        )


def test_alerts_cli_run_generates_csv_and_summary(tmp_path, monkeypatch) -> None:
    input_path = tmp_path / "clean.csv"
    summary_output = tmp_path / "metrics" / "alerts_summary.json"
    exported_csv = tmp_path / "tables" / "discount_spike_alerts.csv"
    frame = pd.DataFrame(
        {
            "order_date": ["2024-01-05"],
            "product_category": ["Beauty"],
            "discount_percent": [30.0],
            "price": [100.0],
            "quantity_sold": [1],
        }
    )
    alerts = pd.DataFrame(
        {
            "order_date": ["2024-01-05"],
            "product_category": ["Beauty"],
            "avg_discount_percent": [30.0],
            "baseline_mean": [10.0],
            "baseline_std": [5.0],
            "z_score": [4.0],
            "gross_revenue": [100.0],
            "estimated_leakage_usd": [20.0],
            "severity": ["high"],
        }
    )
    frame.to_csv(input_path, index=False)

    def fake_export_discount_spike_alerts(detected: pd.DataFrame):
        exported_csv.parent.mkdir(parents=True, exist_ok=True)
        detected.to_csv(exported_csv, index=False)
        return exported_csv

    monkeypatch.setattr(alerts_cli, "detect_discount_spikes", lambda *args, **kwargs: alerts)
    monkeypatch.setattr(
        alerts_cli, "export_discount_spike_alerts", fake_export_discount_spike_alerts
    )

    alerts_cli.run(
        input_path=input_path,
        z_threshold=2.5,
        min_observations=5,
        summary_output=summary_output,
    )

    payload = json.loads(summary_output.read_text(encoding="utf-8"))
    assert exported_csv.exists()
    assert payload["status"] == "attention"
    assert payload["alerts_count"] == 1
    assert payload["severity_counts"] == {"high": 1}


def test_pipeline_cli_main_orchestrates_pipeline_outputs(tmp_path, monkeypatch) -> None:
    raw_df = pd.DataFrame({"order_id": [1], "price": [100.0]})
    clean_df = pd.DataFrame({"order_id": [1], "price": [100.0]})
    featured_df = pd.DataFrame({"order_id": [1], "total_revenue": [90.0]})
    alerts_df = pd.DataFrame({"product_category": ["Beauty"], "severity": ["high"]})
    recommendations = pd.DataFrame({"owner": ["Revenue Ops"], "action": ["Cap discounts"]})
    organized_tables = {
        "category_performance": pd.DataFrame({"product_category": ["Beauty"], "revenue": [90.0]}),
        "product_contribution": pd.DataFrame({"product_id": [1], "revenue": [90.0]}),
    }
    insights = pd.DataFrame({"headline": ["Revenue baseline"], "insight": ["..."]})

    contract_path = tmp_path / "contracts" / "snapshot.json"
    metrics_path = tmp_path / "metrics" / "product_metrics.json"
    processed_path = tmp_path / "processed" / "amazon_sales_clean.csv"
    alerts_path = tmp_path / "tables" / "discount_spike_alerts.csv"
    tables_dir = tmp_path / "tables"
    settings = types.SimpleNamespace(
        environment="test",
        raw_data_dir=tmp_path / "raw",
        bronze_data_dir=tmp_path / "bronze",
        silver_data_dir=tmp_path / "silver",
        gold_data_dir=tmp_path / "gold",
        warehouse_dir=tmp_path / "warehouse",
        warehouse_db_path=tmp_path / "warehouse" / "amazon_sales.duckdb",
        processed_data_dir=tmp_path / "processed",
        external_data_dir=tmp_path / "external",
        figures_dir=tmp_path / "figures",
        tables_dir=tables_dir,
        metrics_dir=tmp_path / "metrics",
        contracts_dir=tmp_path / "contracts",
        pipeline_runs_dir=tmp_path / "runs",
        max_data_staleness_days=45,
    )
    logged_messages: list[str] = []

    def _write_text_artifact(path: Path, content: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    class FakeLogger:
        def info(self, message: str, *args) -> None:
            logged_messages.append(message % args if args else message)

        def warning(self, message: str, *args) -> None:
            logged_messages.append(message % args if args else message)

        def exception(self, message: str, *args) -> None:
            logged_messages.append(message % args if args else message)

    monkeypatch.setattr(pipeline_cli, "get_settings", lambda: settings)
    monkeypatch.setattr(
        pipeline_cli,
        "PipelineRunContext",
        types.SimpleNamespace(
            create=lambda _settings: PipelineRunContext(
                run_id="run-123",
                environment="test",
                started_at_utc="2026-03-18T00:00:00+00:00",
                artifact_dir=tmp_path / "runs" / "run-123",
                manifest_path=tmp_path / "runs" / "run-123" / "execution_manifest.json",
            )
        ),
    )
    monkeypatch.setattr(pipeline_cli, "configure_logging", lambda **kwargs: None)
    monkeypatch.setattr(pipeline_cli, "ensure_directories", lambda _settings: None)
    monkeypatch.setattr(
        pipeline_cli, "logging", types.SimpleNamespace(getLogger=lambda name=None: FakeLogger())
    )
    monkeypatch.setattr(
        pipeline_cli,
        "download_amazon_sales_dataset",
        lambda settings, force_download=False: tmp_path / "raw",
    )
    monkeypatch.setattr(pipeline_cli, "load_raw_sales_data", lambda: raw_df)
    monkeypatch.setattr(pipeline_cli, "enforce_raw_contract", lambda frame: None)
    monkeypatch.setattr(pipeline_cli, "validate_raw_sales_data", lambda frame: frame)
    monkeypatch.setattr(
        pipeline_cli,
        "export_contract_snapshot",
        lambda contract_version, output_path=None: _write_text_artifact(contract_path, "{}"),
    )
    monkeypatch.setattr(pipeline_cli, "clean_sales_data", lambda frame: clean_df)
    monkeypatch.setattr(pipeline_cli, "enforce_clean_quality_gates", lambda frame: None)
    monkeypatch.setattr(pipeline_cli, "save_processed_data", lambda frame: processed_path)
    monkeypatch.setattr(
        pipeline_cli,
        "export_quality_gate_report",
        lambda frame, settings, output_path=None: _write_text_artifact(
            metrics_path.parent / "quality_gates.json", '{"status":"pass"}'
        ),
    )
    monkeypatch.setattr(pipeline_cli, "prepare_sales_frame", lambda frame: featured_df)
    monkeypatch.setattr(pipeline_cli, "generate_executive_insights", lambda frame: insights)
    monkeypatch.setattr(
        pipeline_cli,
        "build_executive_report",
        lambda frame, report_insights: types.SimpleNamespace(insights=report_insights),
    )
    monkeypatch.setattr(pipeline_cli, "build_storytelling_visuals", lambda frame: None)
    monkeypatch.setattr(
        pipeline_cli, "build_actionable_recommendations", lambda frame: recommendations
    )
    monkeypatch.setattr(pipeline_cli, "build_executive_tables", lambda frame: organized_tables)
    monkeypatch.setattr(
        pipeline_cli,
        "materialize_gold_mart",
        lambda frame, settings, run_id=None: types.SimpleNamespace(
            status="materialized",
            validation_output_path=settings.warehouse_dir / "warehouse_validation.json",
        ),
    )
    monkeypatch.setattr(
        pipeline_cli,
        "collect_product_metrics",
        lambda raw_df, clean_df, featured_df, contract_version, pipeline_version: {
            "contract_version": contract_version,
            "pipeline_version": pipeline_version,
        },
    )
    monkeypatch.setattr(
        pipeline_cli,
        "save_product_metrics",
        lambda payload, output_path=None: _write_text_artifact(metrics_path, '{"status":"ok"}'),
    )
    monkeypatch.setattr(pipeline_cli, "load_metrics_baseline", lambda settings: None)
    monkeypatch.setattr(
        pipeline_cli,
        "build_metrics_regression_report",
        lambda payload, settings, baseline_metrics: {
            "status": "baseline_initialized",
            "failed_metrics": [],
        },
    )
    monkeypatch.setattr(
        pipeline_cli,
        "save_metrics_regression_report",
        lambda report, settings, output_path=None: _write_text_artifact(
            metrics_path.parent / "product_metrics_regression.json",
            '{"status":"baseline_initialized","failed_metrics":[]}',
        ),
    )
    monkeypatch.setattr(
        pipeline_cli,
        "save_metrics_baseline",
        lambda payload, settings: _write_text_artifact(
            metrics_path.parent / "product_metrics_baseline.json", '{"status":"initialized"}'
        ),
    )
    monkeypatch.setattr(
        pipeline_cli,
        "write_operational_summary",
        lambda payload, output_path, settings: output_path,
    )
    monkeypatch.setattr(pipeline_cli, "detect_discount_spikes", lambda frame: alerts_df)
    monkeypatch.setattr(
        pipeline_cli,
        "export_discount_spike_alerts",
        lambda frame, output_path=None: _write_text_artifact(
            alerts_path, "product_category\nBeauty\n"
        ),
    )

    def fake_write_json_artifact(payload: dict[str, object], target: Path) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload), encoding="utf-8")
        return target

    monkeypatch.setattr(pipeline_cli, "write_json_artifact", fake_write_json_artifact)

    pipeline_cli.run()

    assert (tables_dir / "actionable_recommendations.csv").exists()
    assert (tables_dir / "executive_insights.csv").exists()
    assert (tables_dir / "category_performance.csv").exists()
    assert (tables_dir / "product_contribution.csv").exists()
    assert any(
        path.name.endswith("_amazon_sales_raw.csv") for path in settings.bronze_data_dir.iterdir()
    )
    assert any(
        path.name.endswith("_amazon_sales_clean.csv") for path in settings.silver_data_dir.iterdir()
    )
    assert any(
        path.name.endswith("_commercial_mart.csv") for path in settings.gold_data_dir.iterdir()
    )
    assert (tmp_path / "runs" / "run-123" / "execution_manifest.json").exists()
    assert (tmp_path / "runs" / "run-123" / "run_status.json").exists()
    assert any("Pipeline completed successfully" in message for message in logged_messages)


def test_pipeline_cli_can_fail_on_kpi_regression(tmp_path, monkeypatch) -> None:
    settings = types.SimpleNamespace(
        environment="test",
        raw_data_dir=tmp_path / "raw",
        bronze_data_dir=tmp_path / "bronze",
        silver_data_dir=tmp_path / "silver",
        gold_data_dir=tmp_path / "gold",
        warehouse_dir=tmp_path / "warehouse",
        warehouse_db_path=tmp_path / "warehouse" / "amazon_sales.duckdb",
        processed_data_dir=tmp_path / "processed",
        external_data_dir=tmp_path / "external",
        figures_dir=tmp_path / "figures",
        tables_dir=tmp_path / "tables",
        metrics_dir=tmp_path / "metrics",
        contracts_dir=tmp_path / "contracts",
        pipeline_runs_dir=tmp_path / "runs",
        max_data_staleness_days=45,
    )

    class FakeLogger:
        def __init__(self) -> None:
            self.exception_messages: list[str] = []
            self.error_messages: list[str] = []

        def info(self, message: str, *args) -> None:
            return None

        def warning(self, message: str, *args) -> None:
            return None

        def error(self, message: str, *args) -> None:
            self.error_messages.append(message % args if args else message)

        def exception(self, message: str, *args) -> None:
            self.exception_messages.append(message % args if args else message)

    fake_logger = FakeLogger()

    def _write_text_artifact(path: Path, content: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    monkeypatch.setattr(pipeline_cli, "get_settings", lambda: settings)
    monkeypatch.setattr(
        pipeline_cli,
        "PipelineRunContext",
        types.SimpleNamespace(
            create=lambda _settings: PipelineRunContext(
                run_id="run-123",
                environment="test",
                started_at_utc="2026-03-18T00:00:00+00:00",
                artifact_dir=tmp_path / "runs" / "run-123",
                manifest_path=tmp_path / "runs" / "run-123" / "execution_manifest.json",
            )
        ),
    )
    monkeypatch.setattr(pipeline_cli, "configure_logging", lambda **kwargs: None)
    monkeypatch.setattr(pipeline_cli, "ensure_directories", lambda _settings: None)
    monkeypatch.setattr(
        pipeline_cli, "logging", types.SimpleNamespace(getLogger=lambda name=None: fake_logger)
    )
    monkeypatch.setattr(
        pipeline_cli,
        "download_amazon_sales_dataset",
        lambda settings, force_download=False: tmp_path / "raw",
    )
    monkeypatch.setattr(
        pipeline_cli, "load_raw_sales_data", lambda: pd.DataFrame({"order_id": [1]})
    )
    monkeypatch.setattr(pipeline_cli, "enforce_raw_contract", lambda frame: None)
    monkeypatch.setattr(pipeline_cli, "validate_raw_sales_data", lambda frame: frame)
    monkeypatch.setattr(
        pipeline_cli,
        "export_contract_snapshot",
        lambda contract_version, output_path=None: _write_text_artifact(
            tmp_path / "contracts" / "snapshot.json", "{}"
        ),
    )
    monkeypatch.setattr(
        pipeline_cli, "clean_sales_data", lambda frame: pd.DataFrame({"order_id": [1]})
    )
    monkeypatch.setattr(pipeline_cli, "enforce_clean_quality_gates", lambda frame: None)
    monkeypatch.setattr(
        pipeline_cli,
        "save_processed_data",
        lambda frame: tmp_path / "processed" / "amazon_sales_clean.csv",
    )
    monkeypatch.setattr(
        pipeline_cli,
        "export_quality_gate_report",
        lambda frame, settings, output_path=None: _write_text_artifact(
            tmp_path / "metrics" / "quality_gates.json", '{"status":"pass"}'
        ),
    )
    monkeypatch.setattr(
        pipeline_cli, "prepare_sales_frame", lambda frame: pd.DataFrame({"order_id": [1]})
    )
    monkeypatch.setattr(
        pipeline_cli,
        "generate_executive_insights",
        lambda frame: pd.DataFrame({"headline": ["x"], "insight": ["y"]}),
    )
    monkeypatch.setattr(
        pipeline_cli,
        "build_executive_report",
        lambda frame, report_insights: types.SimpleNamespace(insights=report_insights),
    )
    monkeypatch.setattr(pipeline_cli, "build_storytelling_visuals", lambda frame: None)
    monkeypatch.setattr(
        pipeline_cli,
        "build_actionable_recommendations",
        lambda frame: pd.DataFrame({"owner": ["x"]}),
    )
    monkeypatch.setattr(
        pipeline_cli,
        "build_executive_tables",
        lambda frame: {"category_performance": pd.DataFrame({"x": [1]})},
    )
    monkeypatch.setattr(
        pipeline_cli,
        "materialize_gold_mart",
        lambda frame, settings, run_id=None: types.SimpleNamespace(
            status="materialized",
            validation_output_path=settings.warehouse_dir / "warehouse_validation.json",
        ),
    )
    monkeypatch.setattr(
        pipeline_cli,
        "collect_product_metrics",
        lambda raw_df, clean_df, featured_df, contract_version, pipeline_version: {
            "contract_version": contract_version,
            "pipeline_version": pipeline_version,
        },
    )
    monkeypatch.setattr(
        pipeline_cli,
        "save_product_metrics",
        lambda payload, output_path=None: _write_text_artifact(
            tmp_path / "metrics" / "product_metrics.json", '{"status":"ok"}'
        ),
    )
    monkeypatch.setattr(
        pipeline_cli, "load_metrics_baseline", lambda settings: {"total_revenue": 100.0}
    )
    monkeypatch.setattr(
        pipeline_cli,
        "build_metrics_regression_report",
        lambda payload, settings, baseline_metrics: {
            "status": "fail",
            "failed_metrics": ["total_revenue"],
        },
    )
    monkeypatch.setattr(
        pipeline_cli,
        "save_metrics_regression_report",
        lambda report, settings, output_path=None: _write_text_artifact(
            tmp_path / "metrics" / "product_metrics_regression.json",
            '{"status":"fail","failed_metrics":["total_revenue"]}',
        ),
    )
    monkeypatch.setattr(
        pipeline_cli,
        "save_metrics_baseline",
        lambda payload, settings: _write_text_artifact(
            tmp_path / "metrics" / "product_metrics_baseline.json", '{"status":"initialized"}'
        ),
    )
    monkeypatch.setattr(
        pipeline_cli, "detect_discount_spikes", lambda frame: pd.DataFrame({"severity": []})
    )
    monkeypatch.setattr(
        pipeline_cli,
        "export_discount_spike_alerts",
        lambda frame, output_path=None: _write_text_artifact(
            tmp_path / "tables" / "discount_spike_alerts.csv", "severity\nhigh\n"
        ),
    )

    with pytest.raises(SystemExit, match="total_revenue"):
        pipeline_cli.run(fail_on_kpi_regression=True)

    assert fake_logger.exception_messages == []
    assert any("Pipeline terminated:" in message for message in fake_logger.error_messages)
    status_payload = json.loads(
        (tmp_path / "runs" / "run-123" / "run_status.json").read_text(encoding="utf-8")
    )
    assert status_payload["status"] == "terminated"
