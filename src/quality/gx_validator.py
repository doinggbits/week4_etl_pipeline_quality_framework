import pandas as pd
import great_expectations as gx

from src.config.settings import DATA_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_inventory():

    path = DATA_DIR / "clean" / "regional_inventory.csv"

    if not path.exists():

        raise FileNotFoundError(f"Missing inventory file {path}")

    df = pd.read_csv(path)

    return df


def load_depots():

    path = DATA_DIR / "clean" / "depots.csv"

    return pd.read_csv(path)


def create_context():

    return gx.get_context()


def inventory_business_rules(df):

    results = {}

    results["missing_values"] = df.isnull().sum().sum()

    numeric_columns = [
        "opening_stock",
        "received_stock",
        "demand",
        "dispatched_stock",
        "capacity",
    ]

    results["negative_quantity_values"] = (df[numeric_columns] < 0).sum().sum()

    calculated = df.opening_stock + df.received_stock - df.demand - df.dispatched_stock

    results["inventory_balance_errors"] = (
        (calculated - df.closing_stock).abs() > 1
    ).sum()

    results["capacity_exceeded"] = (df.closing_stock > df.capacity).sum()

    results["stockout_events"] = (df.closing_stock <= 0).sum()

    return results


def validate_relationships(df):

    results = {}

    depots = load_depots()

    valid_depots = set(depots.depot_id)

    invalid_depots = (~df.depot_id.isin(valid_depots)).sum()

    results["invalid_depot_ids"] = invalid_depots

    return results


def run_gx_checks(df):

    context = create_context()

    datasource_name = "kpc_inventory"

    try:

        datasource = context.data_sources.get(datasource_name)

    except Exception:

        datasource = context.data_sources.add_pandas(datasource_name)

    asset_name = "inventory_asset"

    try:

        asset = datasource.get_asset(asset_name)

    except Exception:

        asset = datasource.add_dataframe_asset(asset_name)

    batch_definition = asset.add_batch_definition_whole_dataframe("inventory_batch")

    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    results = {}

    expectations = {
        "row_count": gx.expectations.ExpectTableRowCountToBeBetween(min_value=1),
        "closing_stock_exists": gx.expectations.ExpectColumnValuesToNotBeNull(
            column="closing_stock"
        ),
        "depot_exists": gx.expectations.ExpectColumnValuesToNotBeNull(
            column="depot_id"
        ),
    }

    for name, expectation in expectations.items():

        results[name] = batch.validate(expectation)

    return results


def run():

    logger.info("Running data quality validation")

    df = load_inventory()

    business = inventory_business_rules(df)

    relationships = validate_relationships(df)

    gx_results = run_gx_checks(df)

    print("\n" + "=" * 70)

    print("BUSINESS QUALITY REPORT")

    print("=" * 70)

    for key, value in business.items():

        if key in ["stockout_events", "capacity_exceeded"]:

            status = "ALERT" if value > 0 else "PASS"

        else:

            status = "FAIL" if value > 0 else "PASS"

        print(f"{key:<35}{value:<10}{status}")

    print("\n")

    print("=" * 70)

    print("RELATIONSHIP CHECKS")

    print("=" * 70)

    for key, value in relationships.items():

        print(f"{key:<35}{value}")

    print("\n")

    print("=" * 70)

    print("GREAT EXPECTATIONS")

    print("=" * 70)

    gx_summary = {}

    for key, result in gx_results.items():

        gx_summary[key] = result.success

        print(f"{key:<35}{result.success}")

    critical_failures = {
        "missing_values": business["missing_values"],
        "negative_quantity_values": business["negative_quantity_values"],
        "inventory_balance_errors": business["inventory_balance_errors"],
        "invalid_depot_ids": relationships["invalid_depot_ids"],
    }

    failed = any(value > 0 for value in critical_failures.values())

    gx_failed = any(not result.success for result in gx_results.values())

    pipeline_failed = failed or gx_failed

    summary = {
        "passed": not pipeline_failed,
        "critical_failures": critical_failures,
        "business_alerts": {
            "stockout_events": business["stockout_events"],
            "capacity_exceeded": business["capacity_exceeded"],
        },
        "gx_results": gx_summary,
    }

    print("\n")

    print("=" * 70)

    if pipeline_failed:

        print("FINAL STATUS: FAILED")

    else:

        print("FINAL STATUS: PASSED")

    print("=" * 70)

    return summary


if __name__ == "__main__":

    result = run()

    if not result["passed"]:

        exit(1)
