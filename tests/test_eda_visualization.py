from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg", force=True)

from amazon_sales_analysis import eda, visualization


def _eda_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_date": ["2024-01-15", "2024-02-10", "2024-02-18"],
            "price": [100.0, 120.0, 80.0],
            "discount_percent": [10, 20, 5],
            "quantity_sold": [2, 1, 3],
            "rating": [4.8, 4.1, 4.6],
            "total_revenue": [180.0, 96.0, 228.0],
            "product_category": ["Electronics", "Home", "Electronics"],
        }
    )


def test_basic_eda_exports_expected_figures(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(eda, "FIGURES_DIR", tmp_path)
    eda.basic_eda(_eda_fixture())

    assert (tmp_path / "dist_price.png").exists()
    assert (tmp_path / "correlation_matrix.png").exists()


def test_visualization_exports_expected_figures(tmp_path: Path, monkeypatch) -> None:
    frame = _eda_fixture().copy()
    frame["order_date"] = pd.to_datetime(frame["order_date"])

    monkeypatch.setattr(visualization, "FIGURES_DIR", tmp_path)
    visualization.sales_trend_over_time(frame)
    visualization.top_categories_by_sales(frame, top_n=2)

    assert (tmp_path / "sales_trend_over_time.png").exists()
    assert (tmp_path / "top_categories_by_sales.png").exists()
