import pandas as pd

from src.config.settings import DATA_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


def reconcile_inventory(df):

    required_columns = ["opening_stock", "received_stock", "demand", "dispatched_stock"]

    missing = [col for col in required_columns if col not in df.columns]

    if missing:

        raise ValueError(f"Missing inventory columns: {missing}")

    df["available_stock"] = df["opening_stock"] + df["received_stock"]

    if "fulfilled_demand" not in df.columns:

        df["fulfilled_demand"] = df[["available_stock", "demand"]].min(axis=1)

    df["demand_shortage"] = (df["demand"] - df["fulfilled_demand"]).clip(lower=0)

    if "requested_dispatch" not in df.columns:

        df["requested_dispatch"] = df["dispatched_stock"]

    remaining_stock = df["available_stock"] - df["fulfilled_demand"]

    df["dispatched_stock"] = pd.concat(
        [remaining_stock, df["dispatched_stock"]], axis=1
    ).min(axis=1)

    df["closing_stock_calculated"] = (
        df["available_stock"] - df["fulfilled_demand"] - df["dispatched_stock"]
    )

    df["closing_stock_calculated"] = df["closing_stock_calculated"].clip(lower=0)

    if "closing_stock" in df.columns:

        df["inventory_difference"] = (
            df["closing_stock"] - df["closing_stock_calculated"]
        ).abs()

    df["closing_stock"] = df["closing_stock_calculated"]

    df.drop(columns=["closing_stock_calculated"], inplace=True)

    logger.info("Inventory reconciliation completed")

    return df


def run():

    input_file = DATA_DIR / "clean" / "regional_inventory.csv"

    output_file = input_file

    df = pd.read_csv(input_file)

    df = reconcile_inventory(df)

    df.to_csv(output_file, index=False)

    logger.info("Saved reconciled inventory")

    return df


if __name__ == "__main__":

    run()
