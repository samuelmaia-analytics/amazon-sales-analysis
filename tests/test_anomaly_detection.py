import pandas as pd

from amazon_sales_analysis.anomaly_detection import detect_discount_spikes


def _fixture_df() -> pd.DataFrame:
    records: list[dict[str, object]] = []
    dates = pd.date_range("2024-01-01", periods=8, freq="D")
    discounts = [10, 11, 9, 10, 10, 11, 10, 45]
    for day, discount in zip(dates, discounts, strict=True):
        records.append(
            {
                "order_id": int(day.day),
                "order_date": day,
                "product_id": 100 + int(day.day),
                "product_category": "Electronics",
                "price": 100.0,
                "discount_percent": float(discount),
                "quantity_sold": 2,
                "customer_region": "North",
                "payment_method": "Card",
                "rating": 4.5,
                "review_count": 10,
                "discounted_price": 90.0,
                "total_revenue": 180.0,
                "gross_revenue": 200.0,
            }
        )
    return pd.DataFrame(records)


def test_detect_discount_spikes_flags_large_spike() -> None:
    alerts = detect_discount_spikes(_fixture_df(), z_threshold=2.0, min_observations=5)

    assert not alerts.empty
    assert "severity" in alerts.columns
    assert float(alerts["z_score"].max()) >= 2.0
