# from pathlib import Path
import pandas as pd

from src.config.settings import DATA_DIR
from src.utils.io import save_dataframe
from src.utils.logger import get_logger

logger = get_logger(__name__)


def generate_regions():

    regions = [
        {
            "region_id": "REG001",
            "region_name": "Mombasa",
            "county": "Mombasa",
            "latitude": -4.0435,
            "longitude": 39.6682,
            "population_factor": 1.10,
        },
        {
            "region_id": "REG002",
            "region_name": "Nairobi",
            "county": "Nairobi",
            "latitude": -1.2921,
            "longitude": 36.8219,
            "population_factor": 1.80,
        },
        {
            "region_id": "REG003",
            "region_name": "Nakuru",
            "county": "Nakuru",
            "latitude": -0.3031,
            "longitude": 36.0800,
            "population_factor": 1.20,
        },
        {
            "region_id": "REG004",
            "region_name": "Eldoret",
            "county": "Uasin Gishu",
            "latitude": 0.5143,
            "longitude": 35.2698,
            "population_factor": 0.90,
        },
        {
            "region_id": "REG005",
            "region_name": "Kisumu",
            "county": "Kisumu",
            "latitude": -0.0917,
            "longitude": 34.7680,
            "population_factor": 0.95,
        },
    ]

    return pd.DataFrame(regions)


def generate_products():

    products = [
        {
            "product_id": "PROD001",
            "product_name": "Petrol",
            "price_per_litre": 195,
            "cost_per_litre": 175,
            "density": 0.74,
            "holding_cost_per_barrel": 8,
        },
        {
            "product_id": "PROD002",
            "product_name": "Diesel",
            "price_per_litre": 210,
            "cost_per_litre": 188,
            "density": 0.84,
            "holding_cost_per_barrel": 9,
        },
        {
            "product_id": "PROD003",
            "product_name": "Jet A1",
            "price_per_litre": 180,
            "cost_per_litre": 165,
            "density": 0.80,
            "holding_cost_per_barrel": 7,
        },
        {
            "product_id": "PROD004",
            "product_name": "Kerosene",
            "price_per_litre": 160,
            "cost_per_litre": 145,
            "density": 0.81,
            "holding_cost_per_barrel": 6,
        },
    ]

    return pd.DataFrame(products)


def generate_depots():

    depots = [
        {
            "depot_id": "DEP001",
            "depot_name": "Mombasa Depot",
            "region_id": "REG001",
            "storage_capacity_barrels": 500000,
            "minimum_operating_stock": 80000,
        },
        {
            "depot_id": "DEP002",
            "depot_name": "Nairobi Depot",
            "region_id": "REG002",
            "storage_capacity_barrels": 350000,
            "minimum_operating_stock": 60000,
        },
        {
            "depot_id": "DEP003",
            "depot_name": "Nakuru Depot",
            "region_id": "REG003",
            "storage_capacity_barrels": 200000,
            "minimum_operating_stock": 40000,
        },
        {
            "depot_id": "DEP004",
            "depot_name": "Eldoret Depot",
            "region_id": "REG004",
            "storage_capacity_barrels": 150000,
            "minimum_operating_stock": 30000,
        },
        {
            "depot_id": "DEP005",
            "depot_name": "Kisumu Depot",
            "region_id": "REG005",
            "storage_capacity_barrels": 120000,
            "minimum_operating_stock": 25000,
        },
    ]

    return pd.DataFrame(depots)


def generate_pipeline_network():

    pipelines = [
        {
            "pipeline_id": "PL001",
            "line_name": "Line 5",
            "source_depot": "DEP001",
            "destination_depot": "DEP002",
            "diameter_inches": 20,
            "capacity_m3_hr": 1300,
            "capacity_barrels_day": 196256,
            "lead_time_days": 1,
            "route_distance_km": 440,
            "transport_cost_per_barrel": 1.5,
        },
        {
            "pipeline_id": "PL002",
            "line_name": "Line 4",
            "source_depot": "DEP002",
            "destination_depot": "DEP003",
            "diameter_inches": 14,
            "capacity_m3_hr": 515,
            "capacity_barrels_day": 77729,
            "lead_time_days": 2,
            "route_distance_km": 160,
            "transport_cost_per_barrel": 1.2,
        },
        {
            "pipeline_id": "PL003",
            "line_name": "Line 4",
            "source_depot": "DEP003",
            "destination_depot": "DEP004",
            "diameter_inches": 14,
            "capacity_m3_hr": 515,
            "capacity_barrels_day": 77729,
            "lead_time_days": 2,
            "route_distance_km": 150,
            "transport_cost_per_barrel": 1.2,
        },
        {
            "pipeline_id": "PL004",
            "line_name": "Line 6",
            "source_depot": "DEP003",
            "destination_depot": "DEP005",
            "diameter_inches": 10,
            "capacity_m3_hr": 290,
            "capacity_barrels_day": 43767,
            "lead_time_days": 2,
            "route_distance_km": 140,
            "transport_cost_per_barrel": 1.1,
        },
    ]

    return pd.DataFrame(pipelines)


def run():

    logger.info("Generating master data")

    output_path = DATA_DIR / "raw"

    regions = generate_regions()
    products = generate_products()
    depots = generate_depots()
    pipelines = generate_pipeline_network()

    save_dataframe(regions, output_path / "regions.csv")

    save_dataframe(products, output_path / "products.csv")

    save_dataframe(depots, output_path / "depots.csv")

    save_dataframe(pipelines, output_path / "pipeline_network.csv")

    logger.info("Master data generation completed")

    return {
        "regions": regions,
        "products": products,
        "depots": depots,
        "pipelines": pipelines,
    }


if __name__ == "__main__":

    run()
