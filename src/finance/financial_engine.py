import pandas as pd

from src.config.settings import DATA_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


BARREL_TO_LITRE = 158.987


def load_movements():

    path = DATA_DIR / "gold" / "movement_recommendations.csv"

    return pd.read_csv(path)


def load_products():

    path = DATA_DIR / "clean" / "products.csv"

    return pd.read_csv(path)


def load_inventory_risk():

    path = DATA_DIR / "gold" / "stock_risk_analysis.csv"

    return pd.read_csv(path)


def calculate_financial_impact():

    movements = load_movements()

    products = load_products()

    risk = load_inventory_risk()

    movements = movements.merge(
        products[
            [
                "product_id",
                "price_per_litre",
                "cost_per_litre",
                "holding_cost_per_barrel",
            ]
        ],
        on="product_id",
        how="left",
    )

    movements["barrels_moved"] = movements["recommended_barrels"].fillna(0)

    movements["litres_moved"] = movements.barrels_moved * BARREL_TO_LITRE

    movements["revenue_protected_ksh"] = (
        movements.litres_moved * movements.price_per_litre
    )

    movements["product_value_ksh"] = movements.litres_moved * movements.cost_per_litre

    movements["transport_cost_ksh"] = movements["transport_cost_ksh"].fillna(0)

    movements["holding_cost_ksh"] = (
        movements.barrels_moved * movements.holding_cost_per_barrel
    )

    movements["net_business_benefit_ksh"] = (
        movements.revenue_protected_ksh
        - movements.transport_cost_ksh
        - movements.holding_cost_ksh
    )

    return movements


def create_financial_summary(df):

    summary = {
        "total_barrels_moved": df.barrels_moved.sum(),
        "revenue_protected_ksh": df.revenue_protected_ksh.sum(),
        "transport_cost_ksh": df.transport_cost_ksh.sum(),
        "holding_cost_ksh": df.holding_cost_ksh.sum(),
        "net_business_benefit_ksh": df.net_business_benefit_ksh.sum(),
    }

    return pd.DataFrame([summary])


def save_results(df, summary):

    output = DATA_DIR / "gold"

    output.mkdir(exist_ok=True)

    df.drop_duplicates().to_csv(output / "financial_impact.csv", index=False)

    summary.to_csv(output / "financial_summary.csv", index=False)

    logger.info("Financial analysis saved")


def run():

    logger.info("Running financial impact engine")

    result = calculate_financial_impact()

    summary = create_financial_summary(result)

    save_results(result, summary)

    return result


if __name__ == "__main__":

    run()
