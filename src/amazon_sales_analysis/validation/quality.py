from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ..config import Settings, get_settings
from ..pipelines.runtime import write_json_artifact
from ..transformations.data_preprocessing import audit_data_quality


@dataclass(frozen=True)
class QualityGateResult:
    check: str
    status: str
    value: int | float
    threshold: str
    message: str


def build_quality_gate_report(
    df: pd.DataFrame, settings: Settings | None = None
) -> list[QualityGateResult]:
    resolved_settings = settings or get_settings()
    quality_audit = audit_data_quality(df).set_index("check")["value"].to_dict()

    return [
        QualityGateResult(
            check="row_count",
            status="pass" if len(df) > 0 else "fail",
            value=int(len(df)),
            threshold="> 0",
            message="dataset limpo nao pode ser vazio",
        ),
        QualityGateResult(
            check="discount_percent_range",
            status=(
                "pass"
                if not (df["discount_percent"].lt(0).any() or df["discount_percent"].gt(100).any())
                else "fail"
            ),
            value=int(((df["discount_percent"] < 0) | (df["discount_percent"] > 100)).sum()),
            threshold="0 invalid rows",
            message="discount_percent deve permanecer na faixa [0, 100]",
        ),
        QualityGateResult(
            check="rating_range",
            status="pass" if not (df["rating"].lt(0).any() or df["rating"].gt(5).any()) else "fail",
            value=int(((df["rating"] < 0) | (df["rating"] > 5)).sum()),
            threshold="0 invalid rows",
            message="rating deve permanecer na faixa [0, 5]",
        ),
        QualityGateResult(
            check="quantity_positive",
            status="pass" if not df["quantity_sold"].le(0).any() else "fail",
            value=int(df["quantity_sold"].le(0).sum()),
            threshold="0 invalid rows",
            message="quantity_sold deve ser maior que zero",
        ),
        QualityGateResult(
            check="price_positive",
            status="pass" if not df["price"].lt(0).any() else "fail",
            value=int(df["price"].lt(0).sum()),
            threshold="0 invalid rows",
            message="price nao pode ser negativo",
        ),
        QualityGateResult(
            check="business_key_duplicates",
            status=(
                "pass"
                if int(quality_audit.get("duplicated_order_product_date", 0)) == 0
                else "fail"
            ),
            value=int(quality_audit.get("duplicated_order_product_date", 0)),
            threshold="0 duplicate rows",
            message="a chave de negocio order_id + product_id + order_date deve ser unica",
        ),
        QualityGateResult(
            check="data_freshness_days",
            status=(
                "pass"
                if 0
                <= int(quality_audit.get("freshness_days", -1))
                <= resolved_settings.max_data_staleness_days
                else "fail"
            ),
            value=int(quality_audit.get("freshness_days", -1)),
            threshold=f"<= {resolved_settings.max_data_staleness_days} days",
            message="o dataset nao deve estar obsoleto para o SLA definido",
        ),
    ]


def enforce_clean_quality_gates(df: pd.DataFrame, settings: Settings | None = None) -> None:
    report = build_quality_gate_report(df, settings)
    failed_checks = [item for item in report if item.status == "fail"]
    if failed_checks:
        messages = [
            (f"{item.check}: {item.message} " f"(value={item.value}, threshold={item.threshold})")
            for item in failed_checks
        ]
        raise ValueError("Quality gate falhou: " + " | ".join(messages))


def summarize_quality_gates(df: pd.DataFrame, settings: Settings | None = None) -> pd.DataFrame:
    report = build_quality_gate_report(df, settings)
    return pd.DataFrame(
        [
            {
                "check": item.check,
                "status": item.status,
                "value": item.value,
                "threshold": item.threshold,
                "message": item.message,
            }
            for item in report
        ]
    )


def export_quality_gate_report(
    df: pd.DataFrame,
    settings: Settings | None = None,
    output_path: Path | None = None,
) -> Path:
    resolved_settings = settings or get_settings()
    report = build_quality_gate_report(df, resolved_settings)
    payload = {
        "status": "fail" if any(item.status == "fail" for item in report) else "pass",
        "checks": [
            {
                "check": item.check,
                "status": item.status,
                "value": item.value,
                "threshold": item.threshold,
                "message": item.message,
            }
            for item in report
        ],
    }
    target = output_path or (resolved_settings.metrics_dir / "quality_gates.json")
    return write_json_artifact(payload, target)
