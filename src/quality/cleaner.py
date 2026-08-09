import pandas as pd
# import numpy as np

from src.config.settings import DATA_DIR
from src.utils.io import save_dataframe
from src.utils.logger import get_logger

logger = get_logger(__name__)


def clean_text(df, columns):

    for column in columns:

        if column in df.columns:

            df[column] = df[column].astype(str).str.strip().str.lower()

    return df


def normalize_products(df):

    if "product_name" not in df.columns:

        return df

    mapping = {
        "diesel fuel": "Diesel",
        "diesel": "Diesel",
        "petrol": "Petrol",
        "super petrol": "Petrol",
        "jet a1": "Jet A1",
        "jet": "Jet A1",
        "kerosene": "Kerosene",
    }

    df["product_name"] = df["product_name"].replace(mapping)

    return df


def normalize_regions(df):

    if "region_name" not in df.columns:

        return df

    mapping = {
        "nairobi": "Nairobi",
        "nairobii": "Nairobi",
        "mombasa": "Mombasa",
        "nakuru": "Nakuru",
        "eldoret": "Eldoret",
        "kisumu": "Kisumu",
    }

    df["region_name"] = df["region_name"].replace(mapping)

    return df


def clean_numeric(df, columns):

    for column in columns:

        if column in df.columns:

            df[column] = df[column].astype(str).str.replace(",", "", regex=False)

            df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


def clean_dates(df, columns):

    for column in columns:

        if column in df.columns:

            df[column] = pd.to_datetime(df[column], errors="coerce")

    return df


def remove_duplicates(df):

    before = len(df)

    df = df.drop_duplicates()

    removed = before - len(df)

    logger.info(f"Removed {removed} duplicate rows")

    return df


def handle_missing_values(df, filename):

    zero_fill_columns = {"received_stock", "dispatched_stock"}

    for column in zero_fill_columns:

        if column in df.columns:

            df[column] = df[column].fillna(0)

    critical_inventory_columns = {
        "opening_stock",
        "closing_stock",
        "demand",
        "capacity",
    }

    for column in critical_inventory_columns:

        if column in df.columns:

            missing = df[column].isna().sum()

            if missing > 0:

                logger.warning(f"{filename}: {missing} missing values in {column}")

    return df


def clean_file(filename):

    dirty = DATA_DIR / "dirty"

    clean = DATA_DIR / "clean"

    df = pd.read_csv(dirty / filename)

    logger.info(f"Cleaning {filename}")

    df = remove_duplicates(df)

    if filename == "regions.csv":

        df = clean_text(df, ["region_name"])

        df = normalize_regions(df)

    elif filename == "products.csv":

        df = clean_text(df, ["product_name"])

        df = normalize_products(df)

    elif filename == "regional_demand.csv":

        df = clean_dates(df, ["date"])

        df = clean_numeric(df, ["actual_demand_barrels"])

    elif filename == "regional_inventory.csv":

        df = clean_numeric(
            df,
            [
                "opening_stock",
                "received_stock",
                "closing_stock",
                "demand",
                "dispatched_stock",
                "capacity",
            ],
        )

    df = handle_missing_values(df, filename)

    save_dataframe(df, clean / filename)

    return df


def run():

    files = [
        "regions.csv",
        "products.csv",
        "depots.csv",
        "pipeline_network.csv",
        "regional_demand.csv",
        "product_movements.csv",
        "regional_inventory.csv",
    ]

    for file in files:

        clean_file(file)

    logger.info("Cleaning completed")


if __name__ == "__main__":

    run()
