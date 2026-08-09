import pandas as pd

from prophet import Prophet

from src.config.settings import DATA_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


FORECAST_DAYS = 30

MIN_HISTORY_POINTS = 60


def load_demand_data():

    path = DATA_DIR / "clean" / "regional_demand.csv"

    if not path.exists():

        raise FileNotFoundError(f"Missing demand file: {path}")

    df = pd.read_csv(path)

    required_columns = ["date", "region_id", "product_id", "actual_demand_barrels"]

    missing = [col for col in required_columns if col not in df.columns]

    if missing:

        raise ValueError(f"Demand data missing columns: {missing}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    df["actual_demand_barrels"] = pd.to_numeric(
        df["actual_demand_barrels"], errors="coerce"
    )

    before = len(df)

    df = df.dropna(subset=["date", "region_id", "product_id", "actual_demand_barrels"])

    df = df[df.actual_demand_barrels >= 0]

    logger.info(f"Demand cleaning removed {before-len(df)} rows")

    return df


def prepare_history(df, region_id, product_id):

    history = df[(df.region_id == region_id) & (df.product_id == product_id)].copy()

    history = history.rename(columns={"date": "ds", "actual_demand_barrels": "y"})

    history = history[["ds", "y"]]

    history = history.dropna()

    history = history.sort_values("ds")

    history = history.groupby("ds", as_index=False)["y"].mean()

    return history


def forecast_region_product(history, region_id, product_id):

    if len(history) < MIN_HISTORY_POINTS:

        logger.warning(
            f"Skipping {region_id}-{product_id}. " f"Only {len(history)} records."
        )

        return None

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
    )

    model.fit(history)

    future = model.make_future_dataframe(periods=FORECAST_DAYS, freq="D")

    forecast = model.predict(future)

    future_forecast = forecast[forecast.ds > history.ds.max()]

    result = pd.DataFrame(
        {
            "forecast_date": future_forecast.ds,
            "region_id": region_id,
            "product_id": product_id,
            "predicted_demand_barrels": future_forecast.yhat.clip(lower=0),
            "lower_bound": future_forecast.yhat_lower.clip(lower=0),
            "upper_bound": future_forecast.yhat_upper.clip(lower=0),
        }
    )

    return result


def generate_forecasts():

    logger.info("Starting demand forecasting")

    demand = load_demand_data()

    results = []

    combinations = demand[["region_id", "product_id"]].drop_duplicates()

    logger.info(f"Forecast combinations: {len(combinations)}")

    for _, row in combinations.iterrows():

        history = prepare_history(demand, row.region_id, row.product_id)

        forecast = forecast_region_product(history, row.region_id, row.product_id)

        if forecast is not None:

            results.append(forecast)

    if not results:

        raise Exception("No forecasts generated. " "Check demand history.")

    final = pd.concat(results, ignore_index=True)

    final = final.dropna()

    final = final.drop_duplicates(subset=["forecast_date", "region_id", "product_id"])

    output_dir = DATA_DIR / "gold"

    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "forecast_results.csv"

    final.to_csv(output_file, index=False)

    logger.info(f"Forecast saved: {output_file}")

    return final


if __name__ == "__main__":

    generate_forecasts()
