import numpy as np
import pandas as pd

from src.config.settings import DATA_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


BARREL_TO_LITRE = 158.987


def load_thresholds():
    return pd.read_csv(DATA_DIR / "gold" / "inventory_thresholds.csv")


def load_products():
    return pd.read_csv(DATA_DIR / "clean" / "products.csv")


def load_depots():
    return pd.read_csv(DATA_DIR / "clean" / "depots.csv")


def calculate_stock_risk():

    inventory = load_thresholds()
    products = load_products()
    depots = load_depots()

    inventory = inventory.merge(depots, on="depot_id", how="left")

    inventory = inventory.merge(
        products[["product_id", "product_name", "price_per_litre", "cost_per_litre"]],
        on="product_id",
        how="left",
    )

    inventory["stock_deficit_barrels"] = (
        inventory["stock_threshold"] - inventory["closing_stock"]
    ).clip(lower=0)

    inventory["stock_surplus_barrels"] = (
        inventory["closing_stock"] - inventory["stock_threshold"]
    ).clip(lower=0)

    inventory["stock_cover_days"] = np.where(
        inventory["average_daily_forecast"] > 0,
        inventory["closing_stock"] / inventory["average_daily_forecast"],
        999.0,
    )

    inventory["stock_cover_days"] = inventory["stock_cover_days"].fillna(0)

    inventory["availability_status"] = "SAFE"

    inventory.loc[
        inventory["closing_stock"] < inventory["stock_threshold"], "availability_status"
    ] = "STOCK BELOW THRESHOLD"

    inventory["demand_attainable"] = (
        inventory["closing_stock"] >= inventory["average_daily_forecast"]
    )

    inventory["demand_status"] = "DEMAND CAN BE MET"

    inventory.loc[inventory["demand_attainable"] == False, "demand_status"] = (
        "DEMAND DEFICIT EXPECTED"
    )

    inventory["lost_sales_value_ksh"] = (
        inventory["stock_deficit_barrels"]
        * BARREL_TO_LITRE
        * inventory["price_per_litre"]
    )

    inventory["potential_profit_loss_ksh"] = (
        inventory["stock_deficit_barrels"]
        * BARREL_TO_LITRE
        * (inventory["price_per_litre"] - inventory["cost_per_litre"])
    )

    cover_conditions = [
        inventory["stock_cover_days"] < 1,
        inventory["stock_cover_days"] < 3,
        inventory["stock_cover_days"] < 7,
        inventory["stock_cover_days"] < 14,
    ]
    cover_scores = [35, 28, 18, 8]
    cover_points = np.select(cover_conditions, cover_scores, default=0)

    demand_points = np.where(inventory["demand_attainable"] == False, 20, 0)

    deficit_ratio = np.where(
        inventory["stock_threshold"] > 0,
        inventory["stock_deficit_barrels"] / inventory["stock_threshold"],
        np.where(inventory["stock_deficit_barrels"] > 0, 1.0, 0.0),
    )

    deficit_conditions = [
        deficit_ratio > 0.5,
        deficit_ratio > 0.25,
        deficit_ratio > 0,
    ]
    deficit_scores = [25, 15, 8]
    deficit_points = np.select(deficit_conditions, deficit_scores, default=0)

    exposure_conditions = [
        inventory["lost_sales_value_ksh"] >= 200_000_000,
        inventory["lost_sales_value_ksh"] >= 50_000_000,
        inventory["lost_sales_value_ksh"] >= 10_000_000,
    ]
    exposure_scores = [20, 14, 8]
    exposure_points = np.select(exposure_conditions, exposure_scores, default=0)

    inventory["risk_score"] = (
        cover_points + demand_points + deficit_points + exposure_points
    )

    inventory["risk_level"] = "LOW"
    inventory.loc[inventory["risk_score"] >= 30, "risk_level"] = "MEDIUM"
    inventory.loc[inventory["risk_score"] >= 60, "risk_level"] = "HIGH"
    inventory.loc[inventory["risk_score"] >= 90, "risk_level"] = "CRITICAL"

    logger.info(
        "Risk level distribution: %s", inventory["risk_level"].value_counts().to_dict()
    )

    high_risk_depot_actions = {
        "Nairobi Depot": "Dispatch additional stock from Mombasa Depot via Line 5 immediately.",
        "Nakuru Depot": "Transfer stock from Nairobi Depot via Line 4.",
        "Eldoret Depot": "Dispatch replenishment from Nakuru Depot through western pipeline.",
        "Kisumu Depot": "Dispatch replenishment from Nakuru Depot through western route.",
        "Mombasa Depot": "Increase refinery receipts and prepare additional pipeline dispatch.",
    }
    default_high_action = "Urgent replenishment required."
    large_deficit_suffix = " Large deficit detected; management approval recommended."

    inventory["recommended_action"] = (
        "Continue normal operation and monitor inventory levels."
    )

    medium_mask = inventory["risk_level"] == "MEDIUM"
    inventory.loc[
        medium_mask & (inventory["demand_attainable"] == False), "recommended_action"
    ] = "Review pipeline allocation and prioritize dispatch."
    inventory.loc[
        medium_mask & (inventory["demand_attainable"] == True), "recommended_action"
    ] = "Plan replenishment within pipeline lead time."

    high_mask = inventory["risk_level"] == "HIGH"
    inventory.loc[high_mask, "recommended_action"] = (
        inventory.loc[high_mask, "depot_name"]
        .map(high_risk_depot_actions)
        .fillna(default_high_action)
    )

    large_deficit_mask = high_mask & (inventory["stock_deficit_barrels"] >= 50000)
    inventory.loc[large_deficit_mask, "recommended_action"] += large_deficit_suffix

    critical_mask = inventory["risk_level"] == "CRITICAL"
    inventory.loc[critical_mask, "recommended_action"] = (
        "Immediate executive escalation. Activate emergency replenishment plan."
    )

    return inventory


def save_risk(df):

    output = DATA_DIR / "gold" / "stock_risk_analysis.csv"
    output.parent.mkdir(exist_ok=True)

    df.drop_duplicates().to_csv(output, index=False)

    logger.info(f"Risk analysis saved: {output}")


def run():
    logger.info("Running enterprise stock risk engine")

    result = calculate_stock_risk()
    save_risk(result)

    return result


if __name__ == "__main__":
    run()
