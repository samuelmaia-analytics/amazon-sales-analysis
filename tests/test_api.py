import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import api


@pytest.fixture(autouse=True)
def restore_api_paths():
    original_dataset_path = api.DATASET_PATH
    original_alerts_path = api.ALERTS_PATH
    original_detector = api.detect_discount_spikes
    api._read_processed_data.cache_clear()
    yield
    api.DATASET_PATH = original_dataset_path
    api.ALERTS_PATH = original_alerts_path
    api.detect_discount_spikes = original_detector
    api._read_processed_data.cache_clear()


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


def test_metrics_summary_returns_404_when_processed_dataset_is_missing(tmp_path) -> None:
    api.DATASET_PATH = tmp_path / "missing.csv"
    client = TestClient(api.app)

    response = client.get("/metrics/summary")

    assert response.status_code == 404
    assert "Processed dataset not found" in response.json()["detail"]


def test_discount_spikes_falls_back_to_runtime_detection(tmp_path, monkeypatch) -> None:
    dataset_path = tmp_path / "amazon_sales_clean.csv"
    frame = pd.DataFrame(
        {
            "order_id": [1, 2, 3, 4, 5],
            "order_date": [
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
                "2024-01-04",
                "2024-01-05",
            ],
            "product_id": [10, 10, 10, 10, 10],
            "product_category": ["Beauty"] * 5,
            "price": [100.0] * 5,
            "discount_percent": [5.0, 5.0, 5.0, 5.0, 30.0],
            "quantity_sold": [1, 1, 1, 1, 1],
            "customer_region": ["North"] * 5,
            "payment_method": ["Card"] * 5,
            "rating": [4.5] * 5,
            "review_count": [10] * 5,
            "discounted_price": [95.0, 95.0, 95.0, 95.0, 70.0],
            "total_revenue": [95.0, 95.0, 95.0, 95.0, 70.0],
        }
    )
    frame.to_csv(dataset_path, index=False)
    fallback_alerts = pd.DataFrame(
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

    api.DATASET_PATH = dataset_path
    api.ALERTS_PATH = tmp_path / "missing_alerts.csv"

    def fake_detect_discount_spikes(
        frame: pd.DataFrame, *, z_threshold: float = 2.5, min_observations: int = 5
    ) -> pd.DataFrame:
        del frame, z_threshold, min_observations
        return fallback_alerts

    monkeypatch.setattr(api, "detect_discount_spikes", fake_detect_discount_spikes)
    client = TestClient(api.app)

    response = client.get("/alerts/discount-spikes")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["product_category"] == "Beauty"


def test_warehouse_category_revenue_endpoint_uses_query_service(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "query_category_revenue",
        lambda: pd.DataFrame(
            {
                "product_category": ["Beauty"],
                "revenue": [90.0],
                "orders": [1],
                "avg_discount_percent": [10.0],
            }
        ),
    )
    monkeypatch.setattr(
        api,
        "warehouse_query_metadata",
        lambda: {"warehouse_table": "gold_commercial_performance", "duckdb_available": False},
    )
    client = TestClient(api.app)

    response = client.get("/warehouse/category-revenue")

    assert response.status_code == 200
    payload = response.json()
    assert payload["rows"][0]["product_category"] == "Beauty"
    assert payload["metadata"]["warehouse_table"] == "gold_commercial_performance"


def test_pipeline_runs_endpoint_returns_history(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "summarize_run_history",
        lambda limit=5: [{"run_id": "run-1", "total_revenue": 100.0}],
    )
    client = TestClient(api.app)

    response = client.get("/pipeline/runs")

    assert response.status_code == 200
    assert response.json()["runs"][0]["run_id"] == "run-1"


def test_pipeline_compare_latest_returns_404_without_enough_runs(monkeypatch) -> None:
    monkeypatch.setattr(
        api, "compare_latest_runs", lambda: (_ for _ in ()).throw(ValueError("missing"))
    )
    client = TestClient(api.app)

    response = client.get("/pipeline/runs/compare-latest")

    assert response.status_code == 404


def test_operations_latest_returns_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        api,
        "latest_operational_summary",
        lambda: {"run_id": "run-1", "overall_status": "healthy"},
    )
    client = TestClient(api.app)

    response = client.get("/operations/latest")

    assert response.status_code == 200
    assert response.json()["run_id"] == "run-1"


def test_health_endpoint_reports_operational_flags(tmp_path, monkeypatch) -> None:
    dataset_path = tmp_path / "amazon_sales_clean.csv"
    alerts_path = tmp_path / "discount_spike_alerts.csv"
    warehouse_db_path = tmp_path / "amazon_sales.duckdb"
    dataset_path.write_text("order_id\n1\n", encoding="utf-8")
    alerts_path.write_text("severity\nhigh\n", encoding="utf-8")
    warehouse_db_path.write_text("db", encoding="utf-8")

    api.DATASET_PATH = dataset_path
    api.ALERTS_PATH = alerts_path
    monkeypatch.setattr(
        api,
        "get_settings",
        lambda: type("Settings", (), {"warehouse_db_path": warehouse_db_path})(),
    )
    client = TestClient(api.app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["processed_dataset_available"] is True
    assert payload["alerts_snapshot_available"] is True
    assert payload["warehouse_db_available"] is True


def test_readiness_endpoint_reports_degraded_when_inputs_are_missing(tmp_path, monkeypatch) -> None:
    api.DATASET_PATH = tmp_path / "missing.csv"
    api.ALERTS_PATH = tmp_path / "missing_alerts.csv"
    monkeypatch.setattr(
        api,
        "get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "warehouse_db_path": tmp_path / "missing.duckdb",
                "gold_data_dir": tmp_path / "gold",
            },
        )(),
    )
    client = TestClient(api.app)

    response = client.get("/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["checks"]["processed_dataset_available"] is False
