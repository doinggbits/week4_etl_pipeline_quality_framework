import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

def save_dataframe(df: pd.DataFrame, path: Path, overwrite: bool = True):
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists() and not overwrite:
        logger.info(f"Skipping existing file: {path.name}")
        return

    df.to_csv(path, index=False)
    logger.info(f"Saved {path.name} ({len(df):,} rows)")

def load_dataframe(path: Path) -> pd.DataFrame:
    logger.info(f"Loading {path.name}")
    return pd.read_csv(path)
