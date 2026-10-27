import sys

import pandas as pd
import great_expectations as gx

from src.config.settings import DATA_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)

SUITE_NAME = "inventory_quality_suite"

NUMERIC_COLUMNS = [
    "opening_stock",
    "received_stock",
    "demand",
    "dispatched_stock",
    "capacity",
]


def load_inventory():
    path = DATA_DIR / "clean" / "regional_inventory.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing inventory file {path}")
    return pd.read_csv(path)


def load_depots():
    return pd.read_csv(DATA_DIR / "clean" / "depots.csv")


def create_context():
    # File-backed context: creates ./gx in the project root.
    # Commit that folder (expectation suite JSON lives in gx/expectations/).
    return gx.get_context(mode="file", project_root_dir=".")


def inventory_business_rules(df):
    results = {}

    results["missing_values"] = int(df.isnull().sum().sum())
    results["negative_quantity_values"] = int((df[NUMERIC_COLUMNS] < 0).sum().sum())

    calculated = df.opening_stock + df.received_stock - df.demand - df.dispatched_stock
    results["inventory_balance_errors"] = int(
        ((calculated - df.closing_stock).abs() > 1).sum()
    )

    results["capacity_exceeded"] = int((df.closing_stock > df.capacity).sum())
    results["stockout_events"] = int((df.closing_stock <= 0).sum())

    return results


def validate_relationships(df):
    depots = load_depots()
    valid_depots = set(depots.depot_id)
    return {"invalid_depot_ids": int((~df.depot_id.isin(valid_depots)).sum())}


def build_suite(context):
    """Define and persist the expectation suite (saved to gx/expectations/)."""
    E = gx.expectations
    suite = gx.ExpectationSuite(name=SUITE_NAME)

    suite.add_expectation(E.ExpectTableRowCountToBeBetween(min_value=1))

    for col in ["closing_stock", "depot_id", "product_id"]:
        suite.add_expectation(E.ExpectColumnValuesToNotBeNull(column=col))

    for col in NUMERIC_COLUMNS + ["closing_stock"]:
        suite.add_expectation(E.ExpectColumnValuesToBeBetween(column=col, min_value=0))

    return context.suites.add_or_update(suite)


def run_gx_checks(df):
    context = create_context()

    datasource = context.data_sources.add_or_update_pandas("kpc_inventory")
    asset = datasource.add_dataframe_asset("inventory_asset")
    batch_definition = asset.add_batch_definition_whole_dataframe("inventory_batch")

    suite = build_suite(context)

    validation_definition = context.validation_definitions.add_or_update(
        gx.ValidationDefinition(
            data=batch_definition, suite=suite, name="inventory_validation"
        )
    )

    run_result = validation_definition.run(batch_parameters={"dataframe": df})

    results = {}
    for r in run_result.results:
        cfg = r.expectation_config
        column = cfg.kwargs.get("column", "table")
        results[f"{cfg.type}:{column}"] = r
    return results


def run():
    logger.info("Running data quality validation")

    df = load_inventory()
    business = inventory_business_rules(df)
    relationships = validate_relationships(df)
    gx_results = run_gx_checks(df)

    logger.info("BUSINESS QUALITY REPORT")
    for key, value in business.items():
        if key in ("stockout_events", "capacity_exceeded"):
            status = "ALERT" if value > 0 else "PASS"
        else:
            status = "FAIL" if value > 0 else "PASS"
        logger.info(f"  {key:<30}{value:<10}{status}")

    logger.info("RELATIONSHIP CHECKS")
    for key, value in relationships.items():
        logger.info(f"  {key:<30}{value}")

    logger.info("GREAT EXPECTATIONS")
    gx_summary = {}
    for key, result in gx_results.items():
        gx_summary[key] = bool(result.success)
        logger.info(f"  {key:<45}{'PASS' if result.success else 'FAIL'}")

    critical_failures = {
        "missing_values": business["missing_values"],
        "negative_quantity_values": business["negative_quantity_values"],
        "inventory_balance_errors": business["inventory_balance_errors"],
        "invalid_depot_ids": relationships["invalid_depot_ids"],
    }

    failed_business = any(v > 0 for v in critical_failures.values())
    failed_gx = any(not ok for ok in gx_summary.values())
    pipeline_failed = failed_business or failed_gx

    summary = {
        "passed": not pipeline_failed,
        "critical_failures": critical_failures,
        "business_alerts": {
            "stockout_events": business["stockout_events"],
            "capacity_exceeded": business["capacity_exceeded"],
        },
        "gx_results": gx_summary,
    }

    if pipeline_failed:
        failing = [k for k, v in critical_failures.items() if v > 0]
        failing += [k for k, ok in gx_summary.items() if not ok]
        logger.error(f"FINAL STATUS: FAILED | failing checks: {failing}")
    else:
        logger.info("FINAL STATUS: PASSED")

    return summary


if __name__ == "__main__":
    result = run()
    if not result["passed"]:
        sys.exit(1)
