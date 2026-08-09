import pandas as pd
import numpy as np
# from pathlib import Path

from src.config.settings import DATA_DIR
from src.utils.io import save_dataframe
from src.utils.logger import get_logger

logger = get_logger(__name__)


np.random.seed(42)


def add_duplicates(df, percentage=0.01):

    duplicate_count = int(len(df) * percentage)

    duplicates = df.sample(duplicate_count, random_state=42)

    return pd.concat([df, duplicates], ignore_index=True)


def add_whitespace(df, columns):

    for column in columns:

        if column in df.columns:

            mask = np.random.rand(len(df)) < 0.05

            df.loc[mask, column] = " " + df.loc[mask, column].astype(str) + " "

    return df


def corrupt_names(df, column, replacements):

    if column not in df.columns:
        return df

    for old, new in replacements.items():

        mask = df[column] == old

        df.loc[mask, column] = new

    return df


def add_missing_values(df, columns, percentage=0.01):

    for column in columns:

        if column in df.columns:

            mask = np.random.rand(len(df)) < percentage

            df.loc[mask, column] = np.nan

    return df


def corrupt_dates(df, column):

    if column not in df.columns:
        return df

    sample = df.sample(int(len(df) * 0.03), random_state=42)

    for index in sample.index:

        date = pd.to_datetime(df.loc[index, column])

        df.loc[index, column] = date.strftime("%d/%m/%Y")

    return df


def corrupt_numbers(df, columns):

    for column in columns:

        if column in df.columns:

            df[column] = df[column].astype("object")

            mask = np.random.rand(len(df)) < 0.03

            df.loc[mask, column] = df.loc[mask, column].apply(lambda x: f"{x:,}")

    return df


def process_file(filename):

    raw_path = DATA_DIR / "raw"

    dirty_path = DATA_DIR / "dirty"

    output_file = dirty_path / filename

    df = pd.read_csv(raw_path / filename)

    df = add_duplicates(df)

    if filename == "regions.csv":

        df = corrupt_names(
            df,
            "region_name",
            {"Nairobi": "NAIROBI", "Mombasa": " mombasa ", "Kisumu": "kisumu"},
        )

        df = add_missing_values(df, ["latitude"])

    elif filename == "products.csv":

        df = corrupt_names(df, "product_name", {"Diesel": "diesel", "Petrol": "PETROL"})

    elif filename == "regional_demand.csv":

        df = corrupt_dates(df, "date")

        df = corrupt_numbers(df, ["actual_demand_barrels"])

    elif filename == "regional_inventory.csv":

        df = corrupt_numbers(df, ["opening_stock", "closing_stock"])

        df = add_missing_values(df, ["received_stock"])

    if output_file.exists():
        output_file.unlink()

    save_dataframe(df, dirty_path / filename)

    logger.info(f"Dirty generated: {filename}")


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

        process_file(file)

    logger.info("Dirty dataset generation completed")


if __name__ == "__main__":

    run()
