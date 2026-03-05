from pathlib import Path

import pandas as pd

from .config import PROCESSED_DATA_DIR, RAW_DATA_DIR
from .contracts import RAW_REQUIRED_COLUMNS
from .validation import sales_schema

RAW_SUBDIR = "amazon_sales"
RAW_FILENAME = "amazon_sales_dataset.csv"
PROCESSED_FILENAME = "amazon_sales_clean.csv"


def load_raw_sales_data(raw_subdir: str = RAW_SUBDIR, filename: str = RAW_FILENAME) -> pd.DataFrame:
    source_path = RAW_DATA_DIR / raw_subdir / filename
    if not source_path.exists():
        raise FileNotFoundError(f"Arquivo bruto não encontrado: {source_path}")
    return pd.read_csv(source_path)


def clean_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    missing_columns = RAW_REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Colunas obrigatorias ausentes no dataset: {missing}")

    cleaned = df.copy()
    cleaned["order_date"] = pd.to_datetime(cleaned["order_date"], errors="coerce")

    numeric_columns = [
        "order_id",
        "product_id",
        "price",
        "discount_percent",
        "quantity_sold",
        "rating",
        "review_count",
        "discounted_price",
        "total_revenue",
    ]
    cleaned[numeric_columns] = cleaned[numeric_columns].apply(pd.to_numeric, errors="coerce")

    cleaned = cleaned.dropna(subset=["order_date", "price", "discount_percent", "quantity_sold"])
    cleaned = cleaned[(cleaned["quantity_sold"] > 0) & (cleaned["price"] >= 0)]
    cleaned["discount_percent"] = cleaned["discount_percent"].clip(lower=0, upper=100)
    cleaned["rating"] = cleaned["rating"].clip(lower=0, upper=5)

    cleaned["discounted_price"] = cleaned["price"] * (1 - cleaned["discount_percent"] / 100)
    cleaned["total_revenue"] = cleaned["discounted_price"] * cleaned["quantity_sold"]

    return cleaned.reset_index(drop=True)


def validate_raw_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    try:
        return sales_schema.validate(df, lazy=True)
    except Exception as exc:
        raise ValueError(f"Falha na validacao do schema com pandera: {exc}") from exc


def save_processed_data(df: pd.DataFrame, filename: str = PROCESSED_FILENAME) -> Path:
    output_path = PROCESSED_DATA_DIR / filename
    df.to_csv(output_path, index=False)
    return output_path
