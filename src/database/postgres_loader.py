from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from src.config.settings import CONFIG
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_engine():
    db = CONFIG["database"]

    url = (
        f"postgresql://"
        f"{db['user']}:{db['password']}"
        f"@{db['host']}:{db['port']}"
        f"/{db['database']}"
    )

    return create_engine(url)


def load_gold_tables():

    engine = get_engine()

    gold_path = Path("data/gold")

    tables = {
        "forecast_results": "forecast_results.csv",
        "inventory_thresholds": "inventory_thresholds.csv",
        "stock_risk_analysis": "stock_risk_analysis.csv",
        "movement_recommendations": "movement_recommendations.csv",
        "financial_summary": "financial_summary.csv",
        "financial_impact": "financial_impact.csv",
    }

    logger.info("Loading Gold Layer into PostgreSQL")

    for table, filename in tables.items():

        csv_file = gold_path / filename

        if not csv_file.exists():
            logger.warning(f"Missing {filename}")
            continue

        df = pd.read_csv(csv_file)

        df.to_sql(
            name=table,
            con=engine,
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=1000,
        )

        logger.info(f"{table} loaded ({len(df)} rows)")

    logger.info("Gold layer successfully loaded.")
