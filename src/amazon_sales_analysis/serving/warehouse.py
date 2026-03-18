from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pandas as pd

from ..config import Settings, get_settings
from ..pipelines.runtime import write_json_artifact

WAREHOUSE_TABLE_NAME = "gold_commercial_performance"
WAREHOUSE_VIEW_NAME = "vw_category_revenue"
WAREHOUSE_HISTORY_TABLE_NAME = "gold_commercial_performance_history"


@dataclass(frozen=True)
class WarehouseMaterializationResult:
    status: str
    database_path: Path
    table_name: str
    view_name: str
    validation_output_path: Path
    materialization_mode: str
    message: str


def duckdb_available() -> bool:
    return importlib.util.find_spec("duckdb") is not None


def warehouse_validation_query(
    table_name: str = WAREHOUSE_TABLE_NAME, *, settings: Settings | None = None
) -> str:
    resolved_settings = settings or get_settings()
    validation_template = (
        resolved_settings.project_root / "sql" / "warehouse_validation.sql"
    ).read_text(encoding="utf-8")
    return validation_template.replace("gold_commercial_performance", table_name).strip()


def warehouse_bootstrap_queries(
    table_name: str = WAREHOUSE_TABLE_NAME, *, settings: Settings | None = None
) -> dict[str, str]:
    resolved_settings = settings or get_settings()
    create_view_template = (
        resolved_settings.project_root / "sql" / "gold_commercial_mart.sql"
    ).read_text(encoding="utf-8")
    return {
        "create_view": create_view_template.replace("gold_commercial_performance", table_name)
        .replace("vw_category_revenue", WAREHOUSE_VIEW_NAME)
        .strip(),
        "validation_query": warehouse_validation_query(table_name, settings=resolved_settings),
    }


def _write_query_artifacts(settings: Settings, queries: dict[str, str]) -> dict[str, Path]:
    settings.warehouse_dir.mkdir(parents=True, exist_ok=True)
    written_paths: dict[str, Path] = {}
    for name, query in queries.items():
        target = settings.warehouse_dir / f"{name}.sql"
        with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=target.parent) as handle:
            handle.write(query + "\n")
            temporary_path = Path(handle.name)
        temporary_path.replace(target)
        written_paths[name] = target
    return written_paths


def materialize_gold_mart(
    df: pd.DataFrame, *, settings: Settings | None = None, run_id: str | None = None
) -> WarehouseMaterializationResult:
    resolved_settings = settings or get_settings()
    resolved_settings.warehouse_dir.mkdir(parents=True, exist_ok=True)
    validation_output_path = resolved_settings.warehouse_dir / "warehouse_validation.json"
    queries = warehouse_bootstrap_queries(settings=resolved_settings)
    materialization_mode = resolved_settings.warehouse_materialization_mode
    if materialization_mode not in {"replace", "append_history"}:
        raise ValueError(
            "warehouse_materialization_mode must be one of: replace, append_history"
        )
    _write_query_artifacts(resolved_settings, queries)

    if not duckdb_available():
        skipped_payload = {
            "status": "skipped",
            "reason": "duckdb_not_installed",
            "database_path": str(resolved_settings.warehouse_db_path),
            "table_name": WAREHOUSE_TABLE_NAME,
            "view_name": WAREHOUSE_VIEW_NAME,
            "materialization_mode": materialization_mode,
            "queries": {
                name: str(path)
                for name, path in _write_query_artifacts(resolved_settings, queries).items()
            },
        }
        write_json_artifact(skipped_payload, validation_output_path)
        return WarehouseMaterializationResult(
            status="skipped",
            database_path=resolved_settings.warehouse_db_path,
            table_name=WAREHOUSE_TABLE_NAME,
            view_name=WAREHOUSE_VIEW_NAME,
            validation_output_path=validation_output_path,
            materialization_mode=materialization_mode,
            message="duckdb not installed; SQL assets generated but mart not materialized",
        )

    import duckdb

    connection = duckdb.connect(str(resolved_settings.warehouse_db_path))
    try:
        connection.register("featured_df", df)
        connection.execute(
            f"CREATE OR REPLACE TABLE {WAREHOUSE_TABLE_NAME} AS SELECT * FROM featured_df"
        )
        if materialization_mode == "append_history":
            history_df = df.copy()
            history_df["pipeline_run_id"] = run_id or "unknown"
            history_df["materialized_at_utc"] = pd.Timestamp.utcnow().isoformat()
            connection.register("history_df", history_df)
            connection.execute(
                f"CREATE TABLE IF NOT EXISTS {WAREHOUSE_HISTORY_TABLE_NAME} "
                "AS SELECT * FROM history_df WHERE 1 = 0"
            )
            connection.execute(
                f"INSERT INTO {WAREHOUSE_HISTORY_TABLE_NAME} SELECT * FROM history_df"
            )
        connection.execute(queries["create_view"])
        validation_rows = connection.execute(queries["validation_query"]).fetchdf()
    finally:
        connection.close()

    materialized_payload: dict[str, Any] = {
        "status": "materialized",
        "database_path": str(resolved_settings.warehouse_db_path),
        "table_name": WAREHOUSE_TABLE_NAME,
        "view_name": WAREHOUSE_VIEW_NAME,
        "materialization_mode": materialization_mode,
        "validation_preview": validation_rows.to_dict(orient="records"),
    }
    write_json_artifact(materialized_payload, validation_output_path)
    return WarehouseMaterializationResult(
        status="materialized",
        database_path=resolved_settings.warehouse_db_path,
        table_name=WAREHOUSE_TABLE_NAME,
        view_name=WAREHOUSE_VIEW_NAME,
        validation_output_path=validation_output_path,
        materialization_mode=materialization_mode,
        message="gold mart materialized in duckdb",
    )
