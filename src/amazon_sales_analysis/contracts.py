from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .config import CONTRACTS_DIR

RAW_REQUIRED_COLUMNS = {
    "order_id",
    "order_date",
    "product_id",
    "product_category",
    "price",
    "discount_percent",
    "quantity_sold",
    "customer_region",
    "payment_method",
    "rating",
    "review_count",
    "discounted_price",
    "total_revenue",
}


@dataclass(frozen=True)
class DataContractResult:
    is_valid: bool
    errors: list[str]


def validate_raw_contract(df: pd.DataFrame) -> DataContractResult:
    errors: list[str] = []
    missing_columns = RAW_REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        errors.append(f"Colunas obrigatorias ausentes no dataset: {missing}")
    if df.empty:
        errors.append("Dataset bruto nao pode ser vazio.")

    return DataContractResult(is_valid=not errors, errors=errors)


def enforce_raw_contract(df: pd.DataFrame) -> None:
    result = validate_raw_contract(df)
    if not result.is_valid:
        raise ValueError(" | ".join(result.errors))


def export_contract_snapshot(*, contract_version: str, output_path: Path | None = None) -> Path:
    payload = {
        "contract_version": contract_version,
        "required_columns": sorted(RAW_REQUIRED_COLUMNS),
        "description": "Raw sales dataset contract expected by preprocessing pipeline.",
    }
    target = output_path or (CONTRACTS_DIR / "sales_dataset.contract.json")
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target
