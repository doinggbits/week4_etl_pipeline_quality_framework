import pandas as pd

from src.config.settings import DATA_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_LEAD_TIME_DAYS = 5

SAFETY_STOCK_PERCENTAGE = 0.20


def load_inventory():

    path = DATA_DIR / "clean" / "regional_inventory.csv"

    return pd.read_csv(path)


def load_forecast():

    path = DATA_DIR / "gold" / "forecast_results.csv"

    df = pd.read_csv(path)

    df["forecast_date"] = pd.to_datetime(df["forecast_date"])

    return df


def calculate_average_forecast(forecast):

    demand = (
        forecast.groupby(["region_id", "product_id"])["predicted_demand_barrels"]
        .mean()
        .reset_index()
    )

    demand.rename(
        columns={"predicted_demand_barrels": "average_daily_forecast"}, inplace=True
    )

    return demand


def load_depots():

    path = DATA_DIR / "clean" / "depots.csv"

    return pd.read_csv(path)


def calculate_thresholds():

    inventory = load_inventory()

    forecast = load_forecast()

    depots = load_depots()

    demand = calculate_average_forecast(forecast)


    inventory = inventory.merge(
        depots[["depot_id", "region_id"]], on="depot_id", how="left"
    )

    result = inventory.merge(demand, on=["region_id", "product_id"], how="left")

    result["average_daily_forecast"] = result["average_daily_forecast"].fillna(0)

    result["lead_time_demand"] = result.average_daily_forecast * DEFAULT_LEAD_TIME_DAYS

    result["safety_stock"] = result.lead_time_demand * SAFETY_STOCK_PERCENTAGE

    result["stock_threshold"] = result.lead_time_demand + result.safety_stock

    result["threshold_status"] = "HEALTHY"

    result.loc[result.closing_stock < result.stock_threshold, "threshold_status"] = (
        "LOW_STOCK"
    )

    result["demand_coverage"] = (
        result.closing_stock / result.average_daily_forecast
    ).replace([float("inf")], 0)

    result["demand_attainability"] = "SUFFICIENT"

    result.loc[
        result.closing_stock < result.average_daily_forecast, "demand_attainability"
    ] = "DEFICIT"

    result["recommended_replenishment"] = (
        result.stock_threshold - result.closing_stock
    ).clip(lower=0)

    return result


def save_thresholds(df):

    output = DATA_DIR / "gold" / "inventory_thresholds.csv"

    output.parent.mkdir(exist_ok=True)

    df.drop_duplicates().to_csv(output, index=False)

    logger.info(f"Saved threshold analysis: {output}")


def run():

    logger.info("Running threshold engine")

    result = calculate_thresholds()

    save_thresholds(result)

    return result


if __name__ == "__main__":

    run()
