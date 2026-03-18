from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4

import pandas as pd

from amazon_sales_analysis.config import Settings, ensure_directories, get_settings


def _atomic_write_text(target: Path, payload: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=target.parent) as handle:
        handle.write(payload)
        temporary_path = Path(handle.name)
    temporary_path.replace(target)


def write_dataframe_artifact(df: pd.DataFrame, target: Path) -> Path:
    _atomic_write_text(target, df.to_csv(index=False))
    return target


def write_json_artifact(payload: dict[str, Any], target: Path) -> Path:
    _atomic_write_text(target, json.dumps(payload, indent=2))
    return target


def compute_file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def profile_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    null_counts = {column: int(value) for column, value in df.isna().sum().to_dict().items()}
    dtypes = {column: str(dtype) for column, dtype in df.dtypes.to_dict().items()}
    order_date_series = (
        df["order_date"] if "order_date" in df.columns else pd.Series(dtype="object")
    )
    order_dates = pd.to_datetime(order_date_series, errors="coerce")
    max_order_date = order_dates.max()
    min_order_date = order_dates.min()
    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": list(df.columns),
        "dtypes": dtypes,
        "null_counts": null_counts,
        "min_order_date": min_order_date.isoformat() if pd.notna(min_order_date) else "",
        "max_order_date": max_order_date.isoformat() if pd.notna(max_order_date) else "",
    }


@dataclass(frozen=True)
class PipelineRunContext:
    run_id: str
    environment: str
    started_at_utc: str
    artifact_dir: Path
    manifest_path: Path

    @classmethod
    def create(cls, settings: Settings | None = None) -> PipelineRunContext:
        resolved_settings = settings or get_settings()
        ensure_directories(resolved_settings)
        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + f"-{uuid4().hex[:8]}"
        artifact_dir = resolved_settings.pipeline_runs_dir / run_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            run_id=run_id,
            environment=resolved_settings.environment,
            started_at_utc=datetime.now(UTC).isoformat(),
            artifact_dir=artifact_dir,
            manifest_path=artifact_dir / "execution_manifest.json",
        )

    @property
    def status_path(self) -> Path:
        return self.artifact_dir / "run_status.json"

    def completion_payload(
        self, *, status: str, error_message: str | None = None, completed_at_utc: str | None = None
    ) -> dict[str, Any]:
        completed_at = completed_at_utc or datetime.now(UTC).isoformat()
        started_at = datetime.fromisoformat(self.started_at_utc)
        finished_at = datetime.fromisoformat(completed_at)
        duration_seconds = max((finished_at - started_at).total_seconds(), 0.0)
        return {
            "run_id": self.run_id,
            "environment": self.environment,
            "started_at_utc": self.started_at_utc,
            "completed_at_utc": completed_at,
            "duration_seconds": round(duration_seconds, 3),
            "status": status,
            "error_message": error_message or "",
        }

    def manifest_payload(
        self,
        *,
        pipeline_version: str,
        dataset_path: Path,
        processed_output_path: Path,
        contract_snapshot_path: Path,
        metrics_path: Path,
        alerts_path: Path,
        table_outputs: dict[str, Path],
        recommendations_path: Path,
        insights_path: Path,
        row_counts: dict[str, int],
        layer_outputs: dict[str, Path] | None = None,
        data_profiles: dict[str, dict[str, Any]] | None = None,
        status: str = "succeeded",
        error_message: str | None = None,
        completed_at_utc: str | None = None,
    ) -> dict[str, Any]:
        completion = self.completion_payload(
            status=status,
            error_message=error_message,
            completed_at_utc=completed_at_utc,
        )
        table_artifacts = {
            name: {
                "path": str(path),
                "sha256": compute_file_sha256(path) if path.exists() else "",
            }
            for name, path in sorted(table_outputs.items())
        }
        layer_artifacts = {
            name: {
                "path": str(path),
                "sha256": compute_file_sha256(path) if path.exists() else "",
            }
            for name, path in sorted((layer_outputs or {}).items())
        }
        return {
            "run_id": self.run_id,
            "environment": self.environment,
            "started_at_utc": self.started_at_utc,
            "completed_at_utc": completion["completed_at_utc"],
            "duration_seconds": completion["duration_seconds"],
            "status": completion["status"],
            "error_message": completion["error_message"],
            "pipeline_version": pipeline_version,
            "dataset_path": str(dataset_path),
            "outputs": {
                "processed_dataset": {
                    "path": str(processed_output_path),
                    "sha256": (
                        compute_file_sha256(processed_output_path)
                        if processed_output_path.exists()
                        else ""
                    ),
                },
                "contract_snapshot": {
                    "path": str(contract_snapshot_path),
                    "sha256": (
                        compute_file_sha256(contract_snapshot_path)
                        if contract_snapshot_path.exists()
                        else ""
                    ),
                },
                "metrics": {
                    "path": str(metrics_path),
                    "sha256": compute_file_sha256(metrics_path) if metrics_path.exists() else "",
                },
                "alerts": {
                    "path": str(alerts_path),
                    "sha256": compute_file_sha256(alerts_path) if alerts_path.exists() else "",
                },
                "recommendations": {
                    "path": str(recommendations_path),
                    "sha256": (
                        compute_file_sha256(recommendations_path)
                        if recommendations_path.exists()
                        else ""
                    ),
                },
                "executive_insights": {
                    "path": str(insights_path),
                    "sha256": compute_file_sha256(insights_path) if insights_path.exists() else "",
                },
                "tables": table_artifacts,
                "layers": layer_artifacts,
            },
            "row_counts": row_counts,
            "data_profiles": data_profiles or {},
        }
