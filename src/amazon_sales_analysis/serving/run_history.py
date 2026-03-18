from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from ..config import Settings, get_settings

TRACKED_KPIS = [
    "total_revenue",
    "gross_revenue",
    "discount_leakage",
    "north_star_nrr",
    "total_orders",
    "avg_ticket",
    "clean_row_count",
    "row_retention_rate",
]

DRIFT_RATIO_THRESHOLDS = {
    "critical": 0.20,
    "high": 0.10,
    "medium": 0.05,
}


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    started_at_utc: str
    manifest_path: Path
    manifest: dict[str, Any]
    metrics: dict[str, Any]


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _classify_drift(delta_ratio: float) -> str:
    absolute_ratio = abs(delta_ratio)
    if absolute_ratio >= DRIFT_RATIO_THRESHOLDS["critical"]:
        return "critical"
    if absolute_ratio >= DRIFT_RATIO_THRESHOLDS["high"]:
        return "high"
    if absolute_ratio >= DRIFT_RATIO_THRESHOLDS["medium"]:
        return "medium"
    return "stable"


def list_run_records(settings: Settings | None = None) -> list[RunRecord]:
    resolved_settings = settings or get_settings()
    records: list[RunRecord] = []

    for manifest_path in sorted(
        resolved_settings.pipeline_runs_dir.glob("*/execution_manifest.json"),
        reverse=True,
    ):
        manifest = _load_json(manifest_path)
        metrics_path = Path(manifest["outputs"]["metrics"]["path"])
        metrics = _load_json(metrics_path) if metrics_path.exists() else {}
        records.append(
            RunRecord(
                run_id=str(manifest.get("run_id", manifest_path.parent.name)),
                started_at_utc=str(manifest.get("started_at_utc", "")),
                manifest_path=manifest_path,
                manifest=manifest,
                metrics=metrics,
            )
        )
    return records


def summarize_run_history(settings: Settings | None = None, limit: int = 5) -> list[dict[str, Any]]:
    records = list_run_records(settings)[:limit]
    summary: list[dict[str, Any]] = []
    for record in records:
        summary.append(
            {
                "run_id": record.run_id,
                "started_at_utc": record.started_at_utc,
                "completed_at_utc": record.manifest.get("completed_at_utc", ""),
                "duration_seconds": record.manifest.get("duration_seconds", 0.0),
                "status": record.manifest.get("status", "unknown"),
                "pipeline_version": record.manifest.get("pipeline_version", ""),
                "raw_rows": record.manifest.get("row_counts", {}).get("raw", 0),
                "clean_rows": record.manifest.get("row_counts", {}).get("clean", 0),
                "alerts": record.manifest.get("row_counts", {}).get("alerts", 0),
                "total_revenue": record.metrics.get("total_revenue", 0.0),
                "avg_ticket": record.metrics.get("avg_ticket", 0.0),
            }
        )
    return summary


def compare_latest_runs(settings: Settings | None = None) -> dict[str, Any]:
    records = list_run_records(settings)
    if len(records) < 2:
        raise ValueError("At least two pipeline runs are required to compare KPI drift.")

    latest = records[0]
    previous = records[1]
    deltas: dict[str, dict[str, float | str]] = {}
    severities: list[str] = []

    for key in TRACKED_KPIS:
        latest_value = float(latest.metrics.get(key, 0.0))
        previous_value = float(previous.metrics.get(key, 0.0))
        delta = latest_value - previous_value
        delta_ratio = (delta / previous_value) if previous_value else 0.0
        severity = _classify_drift(delta_ratio)
        severities.append(severity)
        deltas[key] = {
            "latest": latest_value,
            "previous": previous_value,
            "delta": delta,
            "delta_ratio": delta_ratio,
            "severity": severity,
        }

    overall_severity = "stable"
    if "critical" in severities:
        overall_severity = "critical"
    elif "high" in severities:
        overall_severity = "high"
    elif "medium" in severities:
        overall_severity = "medium"

    return {
        "latest_run_id": latest.run_id,
        "previous_run_id": previous.run_id,
        "latest_started_at_utc": latest.started_at_utc,
        "previous_started_at_utc": previous.started_at_utc,
        "overall_severity": overall_severity,
        "kpi_deltas": deltas,
    }
