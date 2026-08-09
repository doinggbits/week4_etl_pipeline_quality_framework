import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"

LOG_DIR = BASE_DIR / "logs"


DATA_DIR.mkdir(exist_ok=True)


LOG_DIR.mkdir(exist_ok=True)


# CONFIG = {
#     "pipeline": {
#         "name": "KPC Project ETL",
#         "environment": os.getenv("ENVIRONMENT", "development"),
#     },
#     "database": {
#         "host": os.getenv("DB_HOST", "localhost"),
#         "port": int(os.getenv("DB_PORT", 5432)),
#         "database": os.getenv("DB_NAME"),
#         "user": os.getenv("DB_USER", "postgres"),
#         "password": os.getenv("DB_PASSWORD"),
#     }
# }

CONFIG = {
    "pipeline": {
        "name": "KPC Project ETL",
        "environment": os.getenv("ENVIRONMENT"),
    },
    "database": {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT")),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    },
}
