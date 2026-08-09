from pathlib import Path
import os
import shutil
import stat

from sqlalchemy import create_engine, text

from src.config.settings import CONFIG

BASE_DIR = Path(__file__).resolve().parent

CLEAR_DIRECTORIES = [
    BASE_DIR / "data" / "raw",
    BASE_DIR / "data" / "dirty",
    BASE_DIR / "data" / "clean",
    BASE_DIR / "data" / "processed",
    BASE_DIR / "data" / "forecasts",
    BASE_DIR / "data" / "gold",
    BASE_DIR / "logs",
]

REMOVE_DIRECTORIES = [
    BASE_DIR / "great_expectations",
]

REMOVE_EXTENSIONS = [
    ".csv",
    ".json",
    ".parquet",
    ".xlsx",
    ".log",
]

DB_TABLES = [
    "forecast_results",
    "inventory_thresholds",
    "stock_risk_analysis",
    "movement_recommendations",
    "financial_summary",
    "financial_impact",
]


def handle_remove_readonly(func, path, exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def get_engine():

    db = CONFIG["database"]

    url = (
        f"postgresql+psycopg2://"
        f"{db['user']}:{db['password']}"
        f"@{db['host']}:{db['port']}"
        f"/{db['database']}"
    )

    return create_engine(url)


def clear_database():

    print("\nResetting PostgreSQL...")

    try:

        engine = get_engine()

        with engine.begin() as conn:

            for table in DB_TABLES:

                print(f"  Dropping table: {table}")

                conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))

        print("Database reset complete.")

    except Exception as e:

        print(f"Database reset skipped: {e}")


def clear_directory(path):

    if not path.exists():

        path.mkdir(parents=True, exist_ok=True)

        return

    for item in path.iterdir():

        try:

            if item.is_file():

                item.unlink()

            elif item.is_dir():

                shutil.rmtree(item, onexc=handle_remove_readonly)

        except Exception as e:

            print(f"Could not remove {item}: {e}")


def remove_directory(path):

    if not path.exists():

        return

    try:

        shutil.rmtree(path, onexc=handle_remove_readonly)

    except Exception as e:

        print(f"Could not remove {path}: {e}")


def clear_python_cache():

    print("\nRemoving Python cache...")

    for cache in BASE_DIR.rglob("__pycache__"):

        try:

            shutil.rmtree(cache, onexc=handle_remove_readonly)

            print(f"  Removed {cache}")

        except PermissionError:

            print(f"  Skipped (in use): {cache}")

        except Exception as e:

            print(f"  Could not remove {cache}: {e}")

    for pyc in BASE_DIR.rglob("*.pyc"):

        try:

            pyc.unlink()

        except PermissionError:

            print(f"  Skipped (in use): {pyc}")

        except Exception as e:

            print(f"  Could not remove {pyc}: {e}")


def remove_generated_files():

    print("\nRemoving generated files...")

    for file in BASE_DIR.rglob("*"):

        if not file.is_file():

            continue

        if file.suffix not in REMOVE_EXTENSIONS:

            continue

        if file.name in (
            "requirements.txt",
            "pyproject.toml",
        ):

            continue

        try:

            file.unlink()

        except Exception as e:

            print(f"Could not remove {file}: {e}")


def main():

    print("=" * 60)
    print("RESETTING DOMAIN C6 PIPELINE ENVIRONMENT")
    print("=" * 60)

    print(f"\nProject root: {BASE_DIR}")

    for directory in CLEAR_DIRECTORIES:

        print(f"\nClearing: {directory}")

        clear_directory(directory)

    for directory in REMOVE_DIRECTORIES:

        print(f"\nRemoving: {directory}")

        remove_directory(directory)

    clear_python_cache()

    remove_generated_files()

    clear_database()

    print("\n" + "=" * 60)
    print("RESET COMPLETE")
    print("=" * 60)

    print("""
Your project is ready for a fresh pipeline run.

Run:

python -m pipelines.run_pipeline
""")


if __name__ == "__main__":
    main()
