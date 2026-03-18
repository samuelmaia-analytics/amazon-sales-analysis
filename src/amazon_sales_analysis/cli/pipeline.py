from __future__ import annotations

import logging

from amazon_sales_analysis import __version__
from amazon_sales_analysis.anomaly_detection import (
    detect_discount_spikes,
    export_discount_spike_alerts,
)
from amazon_sales_analysis.config import ensure_directories, get_settings
from amazon_sales_analysis.contracts import enforce_raw_contract, export_contract_snapshot
from amazon_sales_analysis.data_ingestion import (
    RAW_FILENAME,
    RAW_SUBDIR,
    download_amazon_sales_dataset,
)
from amazon_sales_analysis.data_preprocessing import (
    clean_sales_data,
    load_raw_sales_data,
    save_processed_data,
    validate_raw_sales_data,
)
from amazon_sales_analysis.decision_engine import build_actionable_recommendations
from amazon_sales_analysis.insights import generate_executive_insights
from amazon_sales_analysis.logging_config import configure_logging
from amazon_sales_analysis.metrics import collect_product_metrics, save_product_metrics
from amazon_sales_analysis.pipelines.runtime import (
    PipelineRunContext,
    profile_dataframe,
    write_dataframe_artifact,
    write_json_artifact,
)
from amazon_sales_analysis.quality import enforce_clean_quality_gates
from amazon_sales_analysis.sales_analysis import build_executive_report, prepare_sales_frame
from amazon_sales_analysis.table_organization import build_executive_tables
from amazon_sales_analysis.visualization import build_storytelling_visuals
from amazon_sales_analysis.warehouse import materialize_gold_mart

CONTRACT_VERSION = "2.0.0"
PIPELINE_VERSION = __version__


def main() -> None:
    settings = get_settings()
    run_context = PipelineRunContext.create(settings)
    configure_logging(run_id=run_context.run_id)
    logger = logging.getLogger("pipeline")

    try:
        ensure_directories(settings)

        logger.info("[1/8] Ensuring source dataset availability")
        download_amazon_sales_dataset(settings=settings)
        dataset_path = settings.raw_data_dir / RAW_SUBDIR / RAW_FILENAME

        logger.info("[2/8] Loading and validating raw data")
        raw_df = load_raw_sales_data()
        enforce_raw_contract(raw_df)
        validate_raw_sales_data(raw_df)
        contract_path = export_contract_snapshot(contract_version=CONTRACT_VERSION)
        logger.info("Data contract snapshot saved to: %s", contract_path)

        logger.info("[3/8] Materializing bronze layer and cleaning source data")
        bronze_path = write_dataframe_artifact(
            raw_df, settings.bronze_data_dir / f"{run_context.run_id}_amazon_sales_raw.csv"
        )
        clean_df = clean_sales_data(raw_df)
        enforce_clean_quality_gates(clean_df)
        processed_path = save_processed_data(clean_df)
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
        warehouse_result = materialize_gold_mart(featured_df, settings=settings)
        logger.info("Warehouse materialization status: %s", warehouse_result.status)

        settings.tables_dir.mkdir(parents=True, exist_ok=True)
        for table_name, table_df in tables.items():
            write_dataframe_artifact(table_df, settings.tables_dir / f"{table_name}.csv")
        recommendations_path = write_dataframe_artifact(
            recommendations, settings.tables_dir / "actionable_recommendations.csv"
        )
        insights_path = write_dataframe_artifact(
            report.insights,
            settings.tables_dir / "executive_insights.csv",
        )
        alerts_path = export_discount_spike_alerts(anomalies)
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
        metrics_path = save_product_metrics(metrics_payload)
        logger.info("Product metrics saved to: %s", metrics_path)

        logger.info("[7/8] Writing execution manifest")
        manifest_payload = run_context.manifest_payload(
            pipeline_version=PIPELINE_VERSION,
            dataset_path=dataset_path,
            processed_output_path=processed_path,
            contract_snapshot_path=contract_path,
            metrics_path=metrics_path,
            alerts_path=alerts_path,
            table_outputs={name: settings.tables_dir / f"{name}.csv" for name in tables},
            recommendations_path=recommendations_path,
            insights_path=insights_path,
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
            },
            data_profiles={
                "raw": profile_dataframe(raw_df),
                "clean": profile_dataframe(clean_df),
                "featured": profile_dataframe(featured_df),
            },
        )
        write_json_artifact(manifest_payload, run_context.manifest_path)
        logger.info("Execution manifest saved to: %s", run_context.manifest_path)

        logger.info("[8/8] Pipeline completed successfully")
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        raise
