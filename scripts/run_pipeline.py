import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from amazon_sales_analysis.config import TABLES_DIR
from amazon_sales_analysis.contracts import enforce_raw_contract, export_contract_snapshot
from amazon_sales_analysis.data_ingestion import download_amazon_sales_dataset
from amazon_sales_analysis.data_preprocessing import (
    clean_sales_data,
    load_raw_sales_data,
    save_processed_data,
)
from amazon_sales_analysis.decision_engine import build_actionable_recommendations
from amazon_sales_analysis.anomaly_detection import (
    detect_discount_spikes,
    export_discount_spike_alerts,
)
from amazon_sales_analysis.eda import basic_eda
from amazon_sales_analysis.evaluation import build_executive_summary
from amazon_sales_analysis.feature_engineering import build_features
from amazon_sales_analysis.logging_config import configure_logging
from amazon_sales_analysis.metrics import collect_product_metrics, save_product_metrics
from amazon_sales_analysis.modeling import rank_discount_opportunities
from amazon_sales_analysis.quality import enforce_clean_quality_gates
from amazon_sales_analysis.table_organization import build_executive_tables
from amazon_sales_analysis.visualization import sales_trend_over_time, top_categories_by_sales

CONTRACT_VERSION = "1.0.0"


def main() -> None:
    configure_logging()
    logger = logging.getLogger("pipeline")

    logger.info("[1/8] Downloading raw dataset")
    download_amazon_sales_dataset()

    logger.info("[2/8] Loading raw data")
    raw_df = load_raw_sales_data()
    enforce_raw_contract(raw_df)
    contract_path = export_contract_snapshot(contract_version=CONTRACT_VERSION)
    logger.info("Data contract snapshot saved to: %s", contract_path)

    logger.info("[3/8] Cleaning dataset")
    clean_df = clean_sales_data(raw_df)
    enforce_clean_quality_gates(clean_df)
    output_path = save_processed_data(clean_df)
    logger.info("Processed dataset saved to: %s", output_path)

    logger.info("[4/8] Building business features")
    featured_df = build_features(clean_df)

    logger.info("[5/8] Running exploratory analysis and visual exports")
    basic_eda(featured_df)
    sales_trend_over_time(featured_df)
    top_categories_by_sales(featured_df)

    logger.info("[6/8] Evaluating business impact and opportunities")
    executive_summary = build_executive_summary(featured_df)
    opportunities = rank_discount_opportunities(featured_df)
    recommendations = build_actionable_recommendations(featured_df)
    organized_tables = build_executive_tables(featured_df)

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    executive_path = TABLES_DIR / "executive_summary.csv"
    opportunities_path = TABLES_DIR / "discount_opportunities.csv"
    recommendations_path = TABLES_DIR / "actionable_recommendations.csv"
    executive_summary.to_csv(executive_path, index=False)
    opportunities.to_csv(opportunities_path, index=False)
    recommendations.to_csv(recommendations_path, index=False)

    for table_name, table_df in organized_tables.items():
        table_df.to_csv(TABLES_DIR / f"{table_name}.csv", index=False)

    logger.info("Executive summary saved to: %s", executive_path)
    logger.info("Opportunities table saved to: %s", opportunities_path)
    logger.info("Actionable recommendations saved to: %s", recommendations_path)
    metrics_payload = collect_product_metrics(
        raw_df,
        clean_df,
        featured_df,
        contract_version=CONTRACT_VERSION,
    )
    metrics_path = save_product_metrics(metrics_payload)
    logger.info("Product metrics saved to: %s", metrics_path)

    logger.info("[7/8] Running anomaly detection on discount spikes")
    spike_alerts = detect_discount_spikes(featured_df)
    alerts_path = export_discount_spike_alerts(spike_alerts)
    logger.info("Discount spike alerts saved to: %s", alerts_path)

    logger.info("[8/8] Pipeline completed successfully")


if __name__ == "__main__":
    main()
