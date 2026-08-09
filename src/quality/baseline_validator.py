import pandas as pd

from src.config.settings import DATA_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


def check_duplicates(df, name):

    count = df.duplicated().sum()

    logger.info(f"{name} duplicates: {count}")

    return count


def check_missing(df, name):

    result = df.isnull().sum()

    missing = result[result > 0]

    logger.info(f"{name} missing values:\n{missing}")

    return missing


def validate_inventory_balance():

    path = DATA_DIR / "raw"

    inventory = pd.read_csv(path / "regional_inventory.csv")

    calculated = (
        inventory.opening_stock
        + inventory.received_stock
        - inventory.demand
        - inventory.dispatched_stock
    )

    errors = abs(calculated - inventory.closing_stock) > 1

    count = errors.sum()

    logger.info(f"Inventory balance errors: {count}")

    return count


def validate_negative_stock():

    inventory = pd.read_csv(DATA_DIR / "raw" / "regional_inventory.csv")

    negative = (inventory.closing_stock < 0).sum()

    logger.info(f"Negative stock records: {negative}")

    return negative


def validate_pipeline_capacity():

    path = DATA_DIR / "raw"

    movements = pd.read_csv(path / "product_movements.csv")

    pipelines = pd.read_csv(path / "pipeline_network.csv")

    merged = movements.merge(
        pipelines[["pipeline_id", "capacity_barrels_day"]], on="pipeline_id", how="left"
    )

    violations = (merged.barrels > merged.capacity_barrels_day).sum()

    logger.info(f"Pipeline capacity violations: {violations}")

    return violations


def validate_foreign_keys():

    path = DATA_DIR / "raw"

    products = pd.read_csv(path / "products.csv")

    inventory = pd.read_csv(path / "regional_inventory.csv")

    invalid_products = (~inventory.product_id.isin(products.product_id)).sum()

    logger.info(f"Invalid product IDs: {invalid_products}")

    return invalid_products


def run():

    logger.info("Starting baseline validation")

    path = DATA_DIR / "raw"

    files = [
        "regions.csv",
        "products.csv",
        "depots.csv",
        "pipeline_network.csv",
        "regional_demand.csv",
        "product_movements.csv",
        "regional_inventory.csv",
    ]

    results = {}

    for file in files:

        df = pd.read_csv(path / file)

        results[file] = {
            "rows": len(df),
            "duplicates": check_duplicates(df, file),
            "missing": check_missing(df, file).to_dict(),
        }

    results["inventory_balance_errors"] = validate_inventory_balance()

    results["negative_stock"] = validate_negative_stock()

    results["pipeline_capacity_errors"] = validate_pipeline_capacity()

    results["invalid_products"] = validate_foreign_keys()

    logger.info("Baseline validation completed")

    return results


if __name__ == "__main__":

    report = run()

    print(report)
