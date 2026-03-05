import pandas as pd
from app import api
from fastapi.testclient import TestClient


def test_revenue_metrics_v1_endpoint(tmp_path) -> None:
    dataset_path = tmp_path / "amazon_sales_clean.csv"
    frame = pd.DataFrame(
        {
            "order_id": [1, 2],
            "order_date": ["2024-01-01", "2024-01-02"],
            "product_id": [10, 11],
            "product_category": ["Beauty", "Electronics"],
            "price": [100.0, 200.0],
            "discount_percent": [10.0, 20.0],
            "quantity_sold": [1, 1],
            "customer_region": ["North", "South"],
            "payment_method": ["Card", "Pix"],
            "rating": [4.8, 4.6],
            "review_count": [10, 20],
            "discounted_price": [90.0, 160.0],
            "total_revenue": [90.0, 160.0],
        }
    )
    frame.to_csv(dataset_path, index=False)

    api.DATASET_PATH = dataset_path
    client = TestClient(api.app)
    response = client.get("/api/v1/revenue_metrics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_revenue"] == 250.0
    assert payload["gross_revenue"] == 300.0
    assert payload["discount_leakage"] == 50.0
