from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from ..config import Settings, get_settings
from ..pipelines.runtime import write_json_artifact
from .run_history import list_run_records


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _artifact_payload(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {"status": "missing", "path": str(path) if path is not None else ""}
    payload = _load_json(path)
    payload.setdefault("path", str(path))
    return payload


def build_operational_summary_payload(
    *,
    run_id: str,
    started_at_utc: str,
    pipeline_version: str,
    row_counts: dict[str, int],
    quality_report: dict[str, Any],
    metrics_regression: dict[str, Any],
    warehouse_validation: dict[str, Any],
) -> dict[str, Any]:
    overall_status = "healthy"
    if any(
        artifact.get("status") in {"fail", "missing"}
        for artifact in [quality_report, metrics_regression, warehouse_validation]
    ):
        overall_status = "attention"
    elif metrics_regression.get("status") == "baseline_initialized":
        overall_status = "baseline_initialized"

    return {
        "run_id": run_id,
        "started_at_utc": started_at_utc,
        "pipeline_version": pipeline_version,
        "overall_status": overall_status,
        "row_counts": row_counts,
        "quality_gates": quality_report,
        "metrics_regression": metrics_regression,
        "warehouse_validation": warehouse_validation,
    }


def write_operational_summary(
    payload: dict[str, Any], *, output_path: Path | None = None, settings: Settings | None = None
) -> Path:
    resolved_settings = settings or get_settings()
    target = output_path or (resolved_settings.metrics_dir / "operational_summary_latest.json")
    return write_json_artifact(payload, target)


def latest_operational_summary(settings: Settings | None = None) -> dict[str, Any]:
    resolved_settings = settings or get_settings()
    records = list_run_records(settings=resolved_settings)
    if not records:
        raise FileNotFoundError("No pipeline run manifests found.")

    latest = records[0]
    layer_outputs = latest.manifest.get("outputs", {}).get("layers", {})
    status_path = latest.manifest_path.parent / "run_status.json"
    run_status = _artifact_payload(status_path)
    quality_report = _artifact_payload(
        Path(layer_outputs["quality_gates"]["path"]) if "quality_gates" in layer_outputs else None
    )
    metrics_regression = _artifact_payload(
        Path(layer_outputs["metrics_regression"]["path"])
        if "metrics_regression" in layer_outputs
        else None
    )
    warehouse_validation = _artifact_payload(
        Path(layer_outputs["warehouse_validation"]["path"])
        if "warehouse_validation" in layer_outputs
        else None
    )
    return build_operational_summary_payload(
        run_id=latest.run_id,
        started_at_utc=latest.started_at_utc,
        pipeline_version=str(latest.manifest.get("pipeline_version", "")),
        row_counts=cast(dict[str, int], latest.manifest.get("row_counts", {})),
        quality_report=quality_report,
        metrics_regression=metrics_regression,
        warehouse_validation=warehouse_validation,
    ) | {"run_status": run_status}
