import shutil
from pathlib import Path

from .config import KAGGLE_DATASET, RAW_DATA_DIR

RAW_SUBDIR = "amazon_sales"
RAW_FILENAME = "amazon_sales_dataset.csv"


def download_amazon_sales_dataset() -> Path:
    """Download dataset from Kaggle Hub and copy it to data/raw/amazon_sales."""
    target_dir = RAW_DATA_DIR / RAW_SUBDIR
    target_dir.mkdir(parents=True, exist_ok=True)
    existing_dataset = target_dir / RAW_FILENAME

    try:
        import kagglehub
    except ImportError as exc:
        if existing_dataset.exists():
            print(f"kagglehub nao instalado. Usando dataset local existente em: {existing_dataset}")
            return target_dir
        raise ImportError(
            "kagglehub nao instalado e nao existe dataset local em data/raw. "
            "Execute: pip install kagglehub"
        ) from exc

    print(f"Baixando dataset '{KAGGLE_DATASET}' via kagglehub...")
    source_path = Path(kagglehub.dataset_download(KAGGLE_DATASET))

    for item in source_path.iterdir():
        destination = target_dir / item.name
        if item.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(item, destination)
        else:
            shutil.copy2(item, destination)

    print(f"Download concluido. Arquivos em: {target_dir}")
    return target_dir
