# from datetime import timedelta
import numpy as np
import pandas as pd

from src.config.settings import DATA_DIR
from src.utils.io import load_dataframe, save_dataframe
from src.utils.logger import get_logger

logger = get_logger(__name__)


RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)


def load_master_data():

    path = DATA_DIR / "raw"

    regions = load_dataframe(path / "regions.csv")

    products = load_dataframe(path / "products.csv")

    depots = load_dataframe(path / "depots.csv")

    pipelines = load_dataframe(path / "pipeline_network.csv")

    return (regions, products, depots, pipelines)


def generate_daily_demand(regions, products, start_date, end_date):

    records = []

    dates = pd.date_range(start_date, end_date)

    product_multiplier = {"Petrol": 1.0, "Diesel": 1.2, "Jet A1": 0.5, "Kerosene": 0.3}

    for date in dates:

        for _, region in regions.iterrows():

            for _, product in products.iterrows():

                base = (
                    5000
                    * region.population_factor
                    * product_multiplier[product.product_name]
                )

                weekend_factor = 0.85 if date.weekday() >= 5 else 1

                seasonal_factor = 1 + 0.15 * np.sin(date.dayofyear / 365 * 2 * np.pi)

                noise = np.random.normal(1, 0.05)

                demand = base * weekend_factor * seasonal_factor * noise

                records.append(
                    {
                        "date": date,
                        "region_id": region.region_id,
                        "product_id": product.product_id,
                        "actual_demand_barrels": round(max(demand, 0), 2),
                    }
                )

    return pd.DataFrame(records)


def generate_movements(pipelines, products, start_date, end_date):

    records = []

    movement_id = 1

    dates = pd.date_range(start_date, end_date)

    for date in dates:

        for _, pipeline in pipelines.iterrows():

            for _, product in products.iterrows():

                utilization = np.random.uniform(0.55, 0.85)

                barrels = pipeline.capacity_barrels_day * utilization

                records.append(
                    {
                        "movement_id": f"MOV{movement_id:06}",
                        "date": date,
                        "pipeline_id": pipeline.pipeline_id,
                        "source_depot": pipeline.source_depot,
                        "destination_depot": pipeline.destination_depot,
                        "product_id": product.product_id,
                        "barrels": round(barrels, 2),
                        "transport_cost": round(
                            barrels * pipeline.transport_cost_per_barrel, 2
                        ),
                    }
                )

                movement_id += 1

    return pd.DataFrame(records)


def generate_inventory(depots, products, movements, demand, start_date, end_date):

    records = []

    inventory = {}

    for _, depot in depots.iterrows():

        for _, product in products.iterrows():

            inventory[(depot.depot_id, product.product_id)] = (
                depot.storage_capacity_barrels * 0.5
            )

    dates = pd.date_range(start_date, end_date)

    for date in dates:

        daily_moves = movements[movements.date == date]

        daily_demand = demand[demand.date == date]

        for _, depot in depots.iterrows():

            for _, product in products.iterrows():

                key = (depot.depot_id, product.product_id)

                opening = inventory[key]

                received = daily_moves[
                    (daily_moves.destination_depot == depot.depot_id)
                    & (daily_moves.product_id == product.product_id)
                ].barrels.sum()

                region_id = depots[depots.depot_id == depot.depot_id].region_id.iloc[0]

                demand_value = daily_demand[
                    (daily_demand.region_id == region_id)
                    & (daily_demand.product_id == product.product_id)
                ].actual_demand_barrels.sum()

                available = opening + received

                fulfilled_demand = min(available, demand_value)

                remaining = available - fulfilled_demand

                requested_dispatch = daily_moves[
                    (daily_moves.source_depot == depot.depot_id)
                    & (daily_moves.product_id == product.product_id)
                ].barrels.sum()

                actual_dispatch = min(remaining, requested_dispatch)

                closing = remaining - actual_dispatch

                inventory[key] = closing

                records.append(
                    {
                        "date": date,
                        "depot_id": depot.depot_id,
                        "product_id": product.product_id,
                        "opening_stock": round(opening, 2),
                        "received_stock": round(received, 2),
                        "demand": round(demand_value, 2),
                        "fulfilled_demand": round(fulfilled_demand, 2),
                        "dispatched_stock": round(actual_dispatch, 2),
                        "requested_dispatch": round(requested_dispatch, 2),
                        "closing_stock": round(closing, 2),
                        "capacity": depot.storage_capacity_barrels,
                    }
                )

    return pd.DataFrame(records)


def run():

    logger.info("Generating transactions")

    regions, products, depots, pipelines = load_master_data()

    start = "2024-01-01"

    end = "2026-12-31"

    demand = generate_daily_demand(regions, products, start, end)

    movements = generate_movements(pipelines, products, start, end)

    inventory = generate_inventory(depots, products, movements, demand, start, end)

    output = DATA_DIR / "raw"

    save_dataframe(demand, output / "regional_demand.csv")

    save_dataframe(movements, output / "product_movements.csv")

    save_dataframe(inventory, output / "regional_inventory.csv")

    logger.info("Transaction generation completed")


if __name__ == "__main__":

    run()
