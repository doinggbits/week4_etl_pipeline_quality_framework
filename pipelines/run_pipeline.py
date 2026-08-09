from src.utils.logger import get_logger
from src.config.settings import CONFIG
from src.ingestion.master_generator import run as generate_master
from src.ingestion.transaction_generator import run as generate_transactions
from src.quality.baseline_validator import run as validate
from src.quality.dirty_generator import run as create_dirty
from src.quality.cleaner import run as clean
from src.inventory.reconciliation import run as reconcile_inventory
from src.quality.gx_validator import run as gx_validate
from src.forecasting.forecast_service import generate_forecasts
from src.inventory.threshold_service import run as calculate_thresholds
from src.risk.risk_engine import run as calculate_risk
from src.movement.movement_optimizer import run as optimize_movements
from src.finance.financial_engine import run as calculate_financials
from src.database.postgres_loader import load_gold_tables

logger = get_logger(__name__)


def main():
    logger.info("||||||||||||||||||||||||||||||||||||||||")
    logger.info("KPC REGIONAL DEMAND & STOCK-OUT PIPELINE")
    logger.info("||||||||||||||||||||||||||||||||||||||||")
    logger.info(f"Pipeline configuration: {CONFIG['pipeline']}")
    logger.info("///////// Pending ...  Data generation")
    logger.info("///////// Pending ...  Dirty data simulation")
    logger.info("///////// Pending ...  Cleaning")
    logger.info("///////// Pending ...  Great Expectations validation")
    logger.info("///////// Pending ...  Forecasting")
    logger.info("///////// Pending ...  Threshold engine")
    logger.info("///////// Pending ...  Stock-risk engine")
    logger.info("///////// Pending ...  Financial engine")
    logger.info("///////// Pending ...  Movement optimizer")
    logger.info("///////// Pending ...  Notifications")
    logger.info("Pipeline completed successfully")

    print("//////Starting ...")

    generate_master()
    generate_transactions()

    print("//////Validating ...")
    validate()

    print("//////Mocking ...")
    create_dirty()

    print("//////Cleaning ...")
    clean()

    print("//////Reconciling ...")
    reconcile_inventory()

    print("//////Safety nets ...")
    gx_validate()

    print("//////Forecasting")
    generate_forecasts()

    print("//////Calculating threshold ...")
    calculate_thresholds()

    print("//////Calculating risk ...")
    calculate_risk()

    print("//////Optimizing movements ...")
    optimize_movements()

    print("//////Calculating financial impact ...")
    calculate_financials()

    print("//////Loading into PostgreSQL...")
    load_gold_tables()

    print("//////Pipeline Complete!")


if __name__ == "__main__":
    main()
