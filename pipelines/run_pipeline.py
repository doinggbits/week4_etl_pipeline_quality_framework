import sys
import time
from datetime import datetime

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


def run_stage(name, fn, *args, **kwargs):
    """Run one stage: log start/end/duration; log the traceback and re-raise on failure."""
    start = time.perf_counter()
    logger.info(f"START  | {name}")
    try:
        result = fn(*args, **kwargs)
    except Exception:
        logger.exception(f"FAILED | {name} after {time.perf_counter() - start:.2f}s")
        raise
    logger.info(f"END    | {name} ({time.perf_counter() - start:.2f}s)")
    return result


def main():
    run_start = datetime.now()
    logger.info("=" * 50)
    logger.info("KPC REGIONAL DEMAND & STOCK-OUT PIPELINE")
    logger.info("=" * 50)
    logger.info(f"Run started at {run_start:%Y-%m-%d %H:%M:%S}")
    logger.info(f"Pipeline configuration: {CONFIG['pipeline']}")

    try:
        run_stage("Master data generation", generate_master)
        run_stage("Transaction generation", generate_transactions)
        run_stage("Baseline validation", validate)
        run_stage("Dirty data simulation", create_dirty)
        run_stage("Cleaning", clean)
        run_stage("Inventory reconciliation", reconcile_inventory)

        # Quality gate: nothing downstream runs if this fails
        gx_result = run_stage("Great Expectations validation", gx_validate)
        if not gx_result["passed"]:
            raise RuntimeError(
                "Data quality gate failed; halting before forecasting/load. "
                f"Critical failures: {gx_result['critical_failures']} | "
                f"GX results: {gx_result['gx_results']}"
            )

        run_stage("Forecasting", generate_forecasts)
        run_stage("Threshold engine", calculate_thresholds)
        run_stage("Stock-risk engine", calculate_risk)
        run_stage("Movement optimizer", optimize_movements)
        run_stage("Financial engine", calculate_financials)
        run_stage("PostgreSQL load", load_gold_tables)

    except Exception:
        logger.error(f"Pipeline FAILED after {datetime.now() - run_start}")
        sys.exit(1)  # non-zero exit so cron/monitoring detects the failure

    # Reached only if every stage succeeded
    logger.info(f"Pipeline completed successfully in {datetime.now() - run_start}")


if __name__ == "__main__":
    main()
