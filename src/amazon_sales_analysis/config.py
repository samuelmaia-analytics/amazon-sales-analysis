from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KAGGLE_DATASET = "aliiihussain/amazon-sales-dataset"


def _load_env_file(env_file: Path) -> None:
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def _resolve_project_path(value: str | None, default: Path) -> Path:
    if not value:
        return default

    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def _get_bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    environment: str
    project_root: Path
    data_dir: Path
    raw_data_dir: Path
    bronze_data_dir: Path
    silver_data_dir: Path
    gold_data_dir: Path
    warehouse_dir: Path
    warehouse_db_path: Path
    processed_data_dir: Path
    external_data_dir: Path
    reports_dir: Path
    figures_dir: Path
    tables_dir: Path
    metrics_dir: Path
    contracts_dir: Path
    pipeline_runs_dir: Path
    kaggle_dataset: str
    log_level: str
    enable_dataset_download: bool
    max_data_staleness_days: int
    kpi_regression_tolerance_pct: float
    warehouse_materialization_mode: str


def build_settings() -> Settings:
    _load_env_file(PROJECT_ROOT / ".env")

    data_dir = _resolve_project_path(os.getenv("AMAZON_SALES_DATA_DIR"), PROJECT_ROOT / "data")
    reports_dir = _resolve_project_path(
        os.getenv("AMAZON_SALES_REPORTS_DIR"), PROJECT_ROOT / "reports"
    )
    contracts_dir = _resolve_project_path(
        os.getenv("AMAZON_SALES_CONTRACTS_DIR"), PROJECT_ROOT / "contracts"
    )

    return Settings(
        environment=os.getenv("AMAZON_SALES_ENV", "dev"),
        project_root=PROJECT_ROOT,
        data_dir=data_dir,
        raw_data_dir=data_dir / "raw",
        bronze_data_dir=data_dir / "bronze",
        silver_data_dir=data_dir / "silver",
        gold_data_dir=data_dir / "gold",
        warehouse_dir=data_dir / "warehouse",
        warehouse_db_path=data_dir / "warehouse" / "amazon_sales.duckdb",
        processed_data_dir=data_dir / "processed",
        external_data_dir=data_dir / "external",
        reports_dir=reports_dir,
        figures_dir=reports_dir / "figures",
        tables_dir=reports_dir / "tables",
        metrics_dir=reports_dir / "metrics",
        contracts_dir=contracts_dir,
        pipeline_runs_dir=reports_dir / "runs",
        kaggle_dataset=os.getenv("AMAZON_SALES_KAGGLE_DATASET", DEFAULT_KAGGLE_DATASET),
        log_level=os.getenv("AMAZON_SALES_LOG_LEVEL", "INFO").upper(),
        enable_dataset_download=_get_bool_env("AMAZON_SALES_ENABLE_DOWNLOAD", True),
        max_data_staleness_days=int(os.getenv("AMAZON_SALES_MAX_DATA_STALENESS_DAYS", "45")),
        kpi_regression_tolerance_pct=float(
            os.getenv("AMAZON_SALES_KPI_REGRESSION_TOLERANCE_PCT", "0.15")
        ),
        warehouse_materialization_mode=os.getenv(
            "AMAZON_SALES_WAREHOUSE_MATERIALIZATION_MODE", "replace"
        ).lower(),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return build_settings()


def ensure_directories(settings: Settings | None = None) -> None:
    resolved_settings = settings or get_settings()
    for directory in [
        resolved_settings.raw_data_dir,
        resolved_settings.bronze_data_dir,
        resolved_settings.silver_data_dir,
        resolved_settings.gold_data_dir,
        resolved_settings.warehouse_dir,
        resolved_settings.processed_data_dir,
        resolved_settings.external_data_dir,
        resolved_settings.figures_dir,
        resolved_settings.tables_dir,
        resolved_settings.metrics_dir,
        resolved_settings.contracts_dir,
        resolved_settings.pipeline_runs_dir,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


_DEFAULT_SETTINGS = get_settings()

DATA_DIR = _DEFAULT_SETTINGS.data_dir
RAW_DATA_DIR = _DEFAULT_SETTINGS.raw_data_dir
BRONZE_DATA_DIR = _DEFAULT_SETTINGS.bronze_data_dir
SILVER_DATA_DIR = _DEFAULT_SETTINGS.silver_data_dir
GOLD_DATA_DIR = _DEFAULT_SETTINGS.gold_data_dir
WAREHOUSE_DIR = _DEFAULT_SETTINGS.warehouse_dir
PROCESSED_DATA_DIR = _DEFAULT_SETTINGS.processed_data_dir
EXTERNAL_DATA_DIR = _DEFAULT_SETTINGS.external_data_dir
REPORTS_DIR = _DEFAULT_SETTINGS.reports_dir
FIGURES_DIR = _DEFAULT_SETTINGS.figures_dir
TABLES_DIR = _DEFAULT_SETTINGS.tables_dir
METRICS_DIR = _DEFAULT_SETTINGS.metrics_dir
CONTRACTS_DIR = _DEFAULT_SETTINGS.contracts_dir
PIPELINE_RUNS_DIR = _DEFAULT_SETTINGS.pipeline_runs_dir
KAGGLE_DATASET = _DEFAULT_SETTINGS.kaggle_dataset
