from src.config.settings import DATA_DIR

def raw_path(filename: str):
    return DATA_DIR / "raw" / filename

def dirty_path(filename: str):
    return DATA_DIR / "dirty" / filename

def clean_path(filename: str):
    return DATA_DIR / "clean" / filename

def processed_path(filename: str):
    return DATA_DIR / "processed" / filename

def forecast_path(filename: str):
    return DATA_DIR / "forecasts" / filename

def report_path(filename: str):
    return DATA_DIR / "reports" / filename
