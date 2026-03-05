import json

import pandas as pd

from amazon_sales_analysis.feature_engineering import build_features
from amazon_sales_analysis.metrics import collect_product_metrics, save_product_metrics


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


def test_save_product_metrics_writes_json(tmp_path) -> None:
    output_path = tmp_path / "metrics.json"
    saved_path = save_product_metrics(
        {"metrics_version": "1.0.0", "contract_version": "1.0.0"},
        output_path=output_path,
    )
    payload = json.loads(saved_path.read_text(encoding="utf-8"))
    assert payload["metrics_version"] == "1.0.0"
