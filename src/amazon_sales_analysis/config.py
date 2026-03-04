from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"
METRICS_DIR = REPORTS_DIR / "metrics"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

KAGGLE_DATASET = "aliiihussain/amazon-sales-dataset"


def ensure_directories() -> None:
    for directory in [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        EXTERNAL_DATA_DIR,
        FIGURES_DIR,
        TABLES_DIR,
        METRICS_DIR,
        CONTRACTS_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


ensure_directories()
