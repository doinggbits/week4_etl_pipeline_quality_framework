import pandas as pd

from src.config.settings import DATA_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_risk():

    path = DATA_DIR / "gold" / "stock_risk_analysis.csv"

    return pd.read_csv(path)


def load_inventory():

    path = DATA_DIR / "clean" / "regional_inventory.csv"

    return pd.read_csv(path)


def load_pipelines():

    path = DATA_DIR / "clean" / "pipeline_network.csv"

    return pd.read_csv(path)


def calculate_surplus(df):

    df["surplus_barrels"] = (df.closing_stock - df.stock_threshold).clip(lower=0)

    return df


def calculate_deficit(df):

    df["deficit_barrels"] = (df.stock_threshold - df.closing_stock).clip(lower=0)

    return df


def optimize_movements():

    risk = load_risk()

    pipelines = load_pipelines()

    risk = calculate_surplus(risk)

    risk = calculate_deficit(risk)

    recommendations = []

    movement_id = 1

    shortages = risk[risk.deficit_barrels > 0]

    surplus = risk[risk.surplus_barrels > 0]

    for _, shortage in shortages.iterrows():

        required = shortage.deficit_barrels

        product = shortage.product_id

        possible_sources = surplus[surplus.product_id == product]

        if possible_sources.empty:

            recommendations.append(
                {
                    "movement_id": f"REC{movement_id:05}",
                    "destination_depot": shortage.depot_id,
                    "product_id": product,
                    "recommended_barrels": required,
                    "status": "NO_SOURCE_AVAILABLE",
                }
            )

            movement_id += 1

            continue

        source = possible_sources.sort_values("surplus_barrels", ascending=False).iloc[
            0
        ]

        route = pipelines[
            (pipelines.source_depot == source.depot_id)
            & (pipelines.destination_depot == shortage.depot_id)
        ]

        if route.empty:

            pipeline_id = "NO_DIRECT_ROUTE"

            transport_cost = 0

        else:

            pipeline = route.iloc[0]

            pipeline_id = pipeline.pipeline_id

            transport_cost = required * pipeline.transport_cost_per_barrel

        move_amount = min(required, source.surplus_barrels)

        recommendations.append(
            {
                "movement_id": f"REC{movement_id:05}",
                "source_depot": source.depot_id,
                "destination_depot": shortage.depot_id,
                "product_id": product,
                "recommended_barrels": round(move_amount, 2),
                "pipeline_id": pipeline_id,
                "transport_cost_ksh": round(transport_cost, 2),
                "priority": shortage.risk_level,
                "reason": "Prevent stock-out",
            }
        )

        movement_id += 1

    return pd.DataFrame(recommendations)


def save_movements(df):

    output = DATA_DIR / "gold" / "movement_recommendations.csv"

    output.parent.mkdir(exist_ok=True)

    df.drop_duplicates().to_csv(output, index=False)

    logger.info(f"Movement recommendations saved: {output}")


def run():

    logger.info("Running movement optimizer")

    result = optimize_movements()

    save_movements(result)

    return result


if __name__ == "__main__":

    run()
