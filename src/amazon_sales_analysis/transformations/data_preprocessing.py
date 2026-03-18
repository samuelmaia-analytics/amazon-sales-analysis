from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import cast

import pandas as pd

from ..config import get_settings
from ..validation.contracts import RAW_REQUIRED_COLUMNS
from ..validation.schema import sales_schema

RAW_SUBDIR = "amazon_sales"
RAW_FILENAME = "amazon_sales_dataset.csv"
PROCESSED_FILENAME = "amazon_sales_clean.csv"


def read_sales_dataset(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Arquivo de vendas nao encontrado: {path}") from exc
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"Arquivo de vendas vazio ou invalido: {path}") from exc
    except Exception as exc:
        raise ValueError(f"Falha ao ler arquivo de vendas em {path}: {exc}") from exc


def load_raw_sales_data(raw_subdir: str = RAW_SUBDIR, filename: str = RAW_FILENAME) -> pd.DataFrame:
    source_path = get_settings().raw_data_dir / raw_subdir / filename
    if not source_path.exists():
        raise FileNotFoundError(f"Arquivo bruto nao encontrado: {source_path}")
    return read_sales_dataset(source_path)


def clean_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    missing_columns = RAW_REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Colunas obrigatorias ausentes no dataset: {missing}")

    cleaned = df.copy()
    cleaned["order_date"] = pd.to_datetime(cleaned["order_date"], errors="coerce")
    for column in ["product_category", "customer_region", "payment_method"]:
        cleaned[column] = cleaned[column].fillna("Unknown").astype(str).str.strip()

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
    cleaned = cleaned.drop_duplicates(subset=["order_id", "product_id", "order_date"], keep="last")
    cleaned["discount_percent"] = cleaned["discount_percent"].clip(lower=0, upper=100)
    cleaned["rating"] = cleaned["rating"].clip(lower=0, upper=5)

    cleaned["discounted_price"] = cleaned["price"] * (1 - cleaned["discount_percent"] / 100)
    cleaned["total_revenue"] = cleaned["discounted_price"] * cleaned["quantity_sold"]

    return cleaned.reset_index(drop=True)


def validate_raw_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    try:
        validated = sales_schema.validate(df, lazy=True)
        return cast(pd.DataFrame, validated)
    except Exception as exc:
        raise ValueError(f"Falha na validacao do schema com pandera: {exc}") from exc


def audit_data_quality(df: pd.DataFrame) -> pd.DataFrame:
    order_date_series = (
        df["order_date"] if "order_date" in df.columns else pd.Series(dtype="object")
    )
    max_order_date = pd.to_datetime(order_date_series, errors="coerce").max()
    freshness_days = (
        int((pd.Timestamp.utcnow().tz_localize(None) - max_order_date).days)
        if pd.notna(max_order_date)
        else -1
    )
    return pd.DataFrame(
        {
            "check": [
                "row_count",
                "null_values",
                "duplicated_order_id",
                "duplicated_order_product_date",
                "discount_out_of_range",
                "rating_out_of_range",
                "freshness_days",
            ],
            "value": [
                len(df),
                int(df.isna().sum().sum()),
                int(df["order_id"].duplicated().sum()),
                int(df.duplicated(subset=["order_id", "product_id", "order_date"]).sum()),
                int(((df["discount_percent"] < 0) | (df["discount_percent"] > 100)).sum()),
                int(((df["rating"] < 0) | (df["rating"] > 5)).sum()),
                freshness_days,
            ],
        }
    )


def save_processed_data(df: pd.DataFrame, filename: str = PROCESSED_FILENAME) -> Path:
    output_path = get_settings().processed_data_dir / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=output_path.parent) as handle:
        df.to_csv(handle, index=False)
        temporary_path = Path(handle.name)
    temporary_path.replace(output_path)
    return output_path
