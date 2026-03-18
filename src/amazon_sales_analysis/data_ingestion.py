from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path

from .config import Settings, get_settings

RAW_SUBDIR = "amazon_sales"
RAW_FILENAME = "amazon_sales_dataset.csv"


def download_amazon_sales_dataset(
    *,
    settings: Settings | None = None,
    force_download: bool = False,
    retries: int = 3,
    retry_delay_seconds: float = 1.0,
) -> Path:
    """Download the raw dataset or reuse the local raw layer when it already exists."""
    resolved_settings = settings or get_settings()
    target_dir = resolved_settings.raw_data_dir / RAW_SUBDIR
    target_dir.mkdir(parents=True, exist_ok=True)
    existing_dataset = target_dir / RAW_FILENAME
    logger = logging.getLogger(__name__)

    if existing_dataset.exists() and not force_download:
        logger.info("Reusing existing raw dataset at %s", existing_dataset)
        return target_dir

    if not resolved_settings.enable_dataset_download:
        if existing_dataset.exists():
            logger.info("Dataset download disabled. Using local dataset at %s", existing_dataset)
            return target_dir
        raise RuntimeError(
            "Dataset download is disabled and no local raw dataset is available. "
            "Set AMAZON_SALES_ENABLE_DOWNLOAD=true or provide the raw CSV locally."
        )

    try:
        import kagglehub
    except ImportError as exc:
        if existing_dataset.exists():
            logger.warning(
                "kagglehub unavailable. Using existing raw dataset at %s", existing_dataset
            )
            return target_dir
        raise ImportError(
            "kagglehub nao instalado e nao existe dataset local em data/raw. "
            "Execute: pip install kagglehub"
        ) from exc

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            logger.info(
                "Downloading dataset '%s' via kagglehub (attempt %s/%s)",
                resolved_settings.kaggle_dataset,
                attempt,
                retries,
            )
            source_path = Path(kagglehub.dataset_download(resolved_settings.kaggle_dataset))

            for item in source_path.iterdir():
                destination = target_dir / item.name
                if item.is_dir():
                    if destination.exists():
                        shutil.rmtree(destination)
                    shutil.copytree(item, destination)
                else:
                    shutil.copy2(item, destination)

            logger.info("Dataset download completed. Files available at %s", target_dir)
            return target_dir
        except Exception as exc:
            last_error = exc
            if attempt == retries:
                break
            logger.warning("Dataset download attempt %s failed: %s", attempt, exc)
            time.sleep(retry_delay_seconds)

    raise RuntimeError(f"Failed to download raw dataset after {retries} attempts.") from last_error
