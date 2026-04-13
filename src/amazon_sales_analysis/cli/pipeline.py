from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import cast

from amazon_sales_analysis import __version__
from amazon_sales_analysis.anomaly_detection import (
    detect_discount_spikes,
    export_discount_spike_alerts,
)
from amazon_sales_analysis.config import ensure_directories, get_settings
from amazon_sales_analysis.decision_engine import build_actionable_recommendations
from amazon_sales_analysis.ingestion.data_ingestion import (
    RAW_FILENAME,
    RAW_SUBDIR,
    download_amazon_sales_dataset,
)
from amazon_sales_analysis.insights import generate_executive_insights
from amazon_sales_analysis.observability.logging_config import configure_logging
from amazon_sales_analysis.observability.metrics import (
    build_metrics_regression_report,
    collect_product_metrics,
    load_metrics_baseline,
    save_metrics_baseline,
    save_metrics_regression_report,
    save_product_metrics,
)
from amazon_sales_analysis.pipelines.runtime import (
    PipelineRunContext,
    profile_dataframe,
    prune_pipeline_runs,
    publish_latest_artifact,
    write_dataframe_artifact,
    write_json_artifact,
)
from amazon_sales_analysis.sales_analysis import build_executive_report, prepare_sales_frame
from amazon_sales_analysis.serving.operations import (
    build_operational_summary_payload,
    write_operational_summary,
)
from amazon_sales_analysis.serving.warehouse import materialize_gold_mart
from amazon_sales_analysis.table_organization import build_executive_tables
from amazon_sales_analysis.transformations.data_preprocessing import (
    clean_sales_data,
    load_raw_sales_data,
    save_processed_data,
    validate_raw_sales_data,
)
from amazon_sales_analysis.validation.contracts import (
    enforce_raw_contract,
    export_contract_snapshot,
)
from amazon_sales_analysis.validation.quality import (
    enforce_clean_quality_gates,
    export_quality_gate_report,
)
from amazon_sales_analysis.visualization import build_storytelling_visuals

CONTRACT_VERSION = "2.0.0"
PIPELINE_VERSION = __version__


def _json_artifact_or_missing(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"status": "missing", "path": str(path)}
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute the end-to-end Amazon sales analytics pipeline."
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Force a fresh raw dataset download instead of reusing the local raw layer.",
    )
    parser.add_argument(
        "--fail-on-kpi-regression",
        action="store_true",
        help="Exit with error when KPI regression exceeds the configured tolerance.",
    )
    parser.add_argument(
        "--retention-runs",
        type=int,
        default=30,
        help="How many most recent pipeline runs to retain under reports/runs.",
    )
    return parser


def run(
    *,
    force_download: bool = False,
    fail_on_kpi_regression: bool = False,
    retention_runs: int = 30,
) -> None:
    settings = get_settings()
    run_context = PipelineRunContext.create(settings)
    configure_logging(run_id=run_context.run_id)
    logger = logging.getLogger("pipeline")
    write_json_artifact(
        run_context.completion_payload(status="running"),
        run_context.status_path,
    )

    try:
        ensure_directories(settings)
        run_tables_dir = run_context.artifact_dir / "tables"
        run_metrics_dir = run_context.artifact_dir / "metrics"
        run_contracts_dir = run_context.artifact_dir / "contracts"
        run_tables_dir.mkdir(parents=True, exist_ok=True)
        run_metrics_dir.mkdir(parents=True, exist_ok=True)
        run_contracts_dir.mkdir(parents=True, exist_ok=True)

        logger.info("[1/8] Ensuring source dataset availability")
        download_amazon_sales_dataset(settings=settings, force_download=force_download)
        dataset_path = settings.raw_data_dir / RAW_SUBDIR / RAW_FILENAME

        logger.info("[2/8] Loading and validating raw data")
        raw_df = load_raw_sales_data()
        enforce_raw_contract(raw_df)
        validate_raw_sales_data(raw_df)
        contract_path = export_contract_snapshot(
            contract_version=CONTRACT_VERSION,
            output_path=run_contracts_dir / "sales_dataset.contract.json",
        )
        publish_latest_artifact(contract_path, settings.contracts_dir / "sales_dataset.contract.json")
        logger.info("Data contract snapshot saved to: %s", contract_path)

        logger.info("[3/8] Materializing bronze layer and cleaning source data")
        bronze_path = write_dataframe_artifact(
            raw_df, settings.bronze_data_dir / f"{run_context.run_id}_amazon_sales_raw.csv"
        )
        clean_df = clean_sales_data(raw_df)
        enforce_clean_quality_gates(clean_df)
        processed_path = save_processed_data(clean_df)
        quality_report_path = export_quality_gate_report(
            clean_df,
            settings=settings,
            output_path=run_metrics_dir / "quality_gates.json",
        )
        publish_latest_artifact(quality_report_path, settings.metrics_dir / "quality_gates.json")
        silver_path = write_dataframe_artifact(
            clean_df, settings.silver_data_dir / f"{run_context.run_id}_amazon_sales_clean.csv"
        )
        logger.info("Processed dataset saved to: %s", processed_path)

        logger.info("[4/8] Building the commercial performance model")
        featured_df = prepare_sales_frame(clean_df)
        gold_path = write_dataframe_artifact(
            featured_df, settings.gold_data_dir / f"{run_context.run_id}_commercial_mart.csv"
        )
        insights = generate_executive_insights(featured_df)
        report = build_executive_report(featured_df, insights)

        logger.info("[5/8] Exporting executive storytelling outputs and analytical mart")
        build_storytelling_visuals(featured_df)
        tables = build_executive_tables(featured_df)
        recommendations = build_actionable_recommendations(featured_df)
        anomalies = detect_discount_spikes(featured_df)
        warehouse_result = materialize_gold_mart(
            featured_df, settings=settings, run_id=run_context.run_id
        )
        logger.info("Warehouse materialization status: %s", warehouse_result.status)

        settings.tables_dir.mkdir(parents=True, exist_ok=True)
        run_table_paths: dict[str, Path] = {}
        for table_name, table_df in tables.items():
            run_table_path = write_dataframe_artifact(table_df, run_tables_dir / f"{table_name}.csv")
            publish_latest_artifact(run_table_path, settings.tables_dir / f"{table_name}.csv")
            run_table_paths[table_name] = run_table_path
        recommendations_run_path = write_dataframe_artifact(
            recommendations, run_tables_dir / "actionable_recommendations.csv"
        )
        publish_latest_artifact(
            recommendations_run_path, settings.tables_dir / "actionable_recommendations.csv"
        )
        insights_run_path = write_dataframe_artifact(
            report.insights,
            run_tables_dir / "executive_insights.csv",
        )
        publish_latest_artifact(insights_run_path, settings.tables_dir / "executive_insights.csv")
        alerts_path = export_discount_spike_alerts(
            anomalies, output_path=run_tables_dir / "discount_spike_alerts.csv"
        )
        publish_latest_artifact(alerts_path, settings.tables_dir / "discount_spike_alerts.csv")
        logger.info("Executive tables saved to: %s", settings.tables_dir)
        logger.info("Discount spike alerts saved to: %s", alerts_path)

        logger.info("[6/8] Persisting KPI package")
        metrics_payload = collect_product_metrics(
            raw_df,
            clean_df,
            featured_df,
            contract_version=CONTRACT_VERSION,
            pipeline_version=PIPELINE_VERSION,
        )
        metrics_path = save_product_metrics(
            metrics_payload,
            output_path=run_metrics_dir / "product_metrics.json",
        )
        publish_latest_artifact(metrics_path, settings.metrics_dir / "product_metrics.json")
        baseline_metrics = load_metrics_baseline(settings=settings)
        metrics_regression_report = build_metrics_regression_report(
            metrics_payload,
            settings=settings,
            baseline_metrics=baseline_metrics,
        )
        metrics_regression_path = save_metrics_regression_report(
            metrics_regression_report,
            settings=settings,
            output_path=run_metrics_dir / "product_metrics_regression.json",
        )
        publish_latest_artifact(
            metrics_regression_path,
            settings.metrics_dir / "product_metrics_regression.json",
        )
        if baseline_metrics is None:
            baseline_path = save_metrics_baseline(metrics_payload, settings=settings)
            logger.info("KPI baseline initialized at: %s", baseline_path)
        elif metrics_regression_report["status"] == "fail":
            logger.warning(
                "KPI regression drift detected for: %s",
                ", ".join(metrics_regression_report["failed_metrics"]),
            )
            if fail_on_kpi_regression:
                raise SystemExit(
                    "KPI regression drift exceeded tolerance for: "
                    + ", ".join(metrics_regression_report["failed_metrics"])
                )
        logger.info("Product metrics saved to: %s", metrics_path)

        logger.info("[7/8] Writing execution manifest")
        manifest_payload = run_context.manifest_payload(
            pipeline_version=PIPELINE_VERSION,
            dataset_path=dataset_path,
            processed_output_path=processed_path,
            contract_snapshot_path=contract_path,
            metrics_path=metrics_path,
            alerts_path=alerts_path,
            table_outputs=run_table_paths,
            recommendations_path=recommendations_run_path,
            insights_path=insights_run_path,
            row_counts={
                "raw": int(len(raw_df)),
                "clean": int(len(clean_df)),
                "featured": int(len(featured_df)),
                "alerts": int(len(anomalies)),
            },
            layer_outputs={
                "bronze_raw_snapshot": bronze_path,
                "silver_clean_snapshot": silver_path,
                "gold_commercial_mart": gold_path,
                "warehouse_validation": warehouse_result.validation_output_path,
                "quality_gates": quality_report_path,
                "metrics_regression": metrics_regression_path,
            },
            data_profiles={
                "raw": profile_dataframe(raw_df),
                "clean": profile_dataframe(clean_df),
                "featured": profile_dataframe(featured_df),
            },
            status="succeeded",
        )
        write_json_artifact(manifest_payload, run_context.manifest_path)
        operational_summary = build_operational_summary_payload(
            run_id=run_context.run_id,
            started_at_utc=run_context.started_at_utc,
            pipeline_version=PIPELINE_VERSION,
            row_counts=manifest_payload["row_counts"],
            quality_report=_json_artifact_or_missing(quality_report_path),
            metrics_regression=_json_artifact_or_missing(metrics_regression_path),
            warehouse_validation=_json_artifact_or_missing(warehouse_result.validation_output_path),
        )
        operational_summary_path = write_operational_summary(
            operational_summary,
            output_path=run_context.artifact_dir / "operational_summary.json",
            settings=settings,
        )
        write_operational_summary(
            operational_summary,
            output_path=settings.metrics_dir / "operational_summary_latest.json",
            settings=settings,
        )
        write_json_artifact(
            run_context.completion_payload(status="succeeded"),
            run_context.status_path,
        )
        logger.info("Execution manifest saved to: %s", run_context.manifest_path)
        logger.info("Operational summary saved to: %s", operational_summary_path)

        removed_runs = prune_pipeline_runs(settings.pipeline_runs_dir, keep_last_runs=retention_runs)
        if removed_runs:
            logger.info(
                "Pipeline run retention applied. Removed %s obsolete run directories.",
                len(removed_runs),
            )

        logger.info("[8/8] Pipeline completed successfully")
    except SystemExit as exc:
        write_json_artifact(
            run_context.completion_payload(status="terminated", error_message=str(exc)),
            run_context.status_path,
        )
        logger.error("Pipeline terminated: %s", exc)
        raise
    except Exception as exc:
        write_json_artifact(
            run_context.completion_payload(status="failed", error_message=str(exc)),
            run_context.status_path,
        )
        logger.exception("Pipeline failed: %s", exc)
        raise


def main() -> None:
    args = build_parser().parse_args()
    run(
        force_download=args.force_download,
        fail_on_kpi_regression=args.fail_on_kpi_regression,
        retention_runs=args.retention_runs,
    )
