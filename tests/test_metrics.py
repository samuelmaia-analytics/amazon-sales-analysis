import json

import pandas as pd

from amazon_sales_analysis.feature_engineering import build_features
from amazon_sales_analysis.metrics import (
    build_metrics_regression_report,
    collect_product_metrics,
    save_metrics_baseline,
    save_metrics_regression_report,
    save_product_metrics,
)


def _base_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": [1, 2],
            "order_date": ["2024-01-15", "2024-01-20"],
            "product_id": [10, 11],
            "product_category": ["Electronics", "Beauty"],
            "price": [100.0, 50.0],
            "discount_percent": [10, 20],
            "quantity_sold": [2, 1],
            "customer_region": ["North", "South"],
            "payment_method": ["Card", "Pix"],
            "rating": [4.8, 4.2],
            "review_count": [50, 8],
            "discounted_price": [90.0, 40.0],
            "total_revenue": [180.0, 40.0],
        }
    )


def test_collect_product_metrics_has_core_fields() -> None:
    raw_df = _base_df()
    clean_df = _base_df()
    featured_df = build_features(clean_df)

    metrics = collect_product_metrics(
        raw_df,
        clean_df,
        featured_df,
        contract_version="1.0.0",
        pipeline_version="0.2.0",
    )
    assert metrics["contract_version"] == "1.0.0"
    assert metrics["pipeline_version"] == "0.2.0"
    assert metrics["raw_row_count"] == 2
    assert metrics["clean_row_count"] == 2
    assert "north_star_nrr" in metrics
    assert "avg_ticket" in metrics
    assert "headline_insights" in metrics


def test_collect_product_metrics_regression_values() -> None:
    raw_df = _base_df()
    clean_df = _base_df()
    featured_df = build_features(clean_df)

    metrics = collect_product_metrics(
        raw_df,
        clean_df,
        featured_df,
        contract_version="1.0.0",
        pipeline_version="0.2.0",
    )

    assert metrics["total_revenue"] == 220.0
    assert metrics["gross_revenue"] == 250.0
    assert metrics["discount_leakage"] == 30.0
    assert metrics["north_star_nrr"] == 0.88
    assert metrics["avg_ticket"] == 110.0


def test_save_product_metrics_writes_json(tmp_path) -> None:
    output_path = tmp_path / "metrics.json"
    saved_path = save_product_metrics(
        {"metrics_version": "1.0.0", "contract_version": "1.0.0"},
        output_path=output_path,
    )
    payload = json.loads(saved_path.read_text(encoding="utf-8"))
    assert payload["metrics_version"] == "1.0.0"


def test_metrics_regression_report_flags_significant_drift(tmp_path) -> None:
    current_metrics: dict[str, float | int] = {
        "total_revenue": 130.0,
        "gross_revenue": 140.0,
        "discount_leakage": 10.0,
        "north_star_nrr": 0.85,
        "total_orders": 2,
        "avg_ticket": 65.0,
        "clean_row_count": 2,
        "row_retention_rate": 1.0,
    }
    baseline_metrics: dict[str, float | int] = {
        "total_revenue": 100.0,
        "gross_revenue": 110.0,
        "discount_leakage": 10.0,
        "north_star_nrr": 0.9,
        "total_orders": 2,
        "avg_ticket": 50.0,
        "clean_row_count": 2,
        "row_retention_rate": 1.0,
    }
    settings = type(
        "SettingsStub",
        (),
        {"metrics_dir": tmp_path, "kpi_regression_tolerance_pct": 0.15},
    )()

    save_metrics_baseline(baseline_metrics, settings=settings)
    report = build_metrics_regression_report(
        current_metrics,
        settings=settings,
        baseline_metrics=baseline_metrics,
    )
    report_path = save_metrics_regression_report(report, settings=settings)

    stored_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert stored_report["status"] == "fail"
    assert "total_revenue" in stored_report["failed_metrics"]
