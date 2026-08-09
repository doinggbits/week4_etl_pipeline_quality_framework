# KPC Regional Demand & Stock-Out Pipeline

An end-to-end ETL pipeline that generates, cleans, validates, forecasts, and analyzes
regional product demand and inventory data, then loads the results into PostgreSQL.

The pipeline runs the following stages in order:

1. Data generation (master data + transactions)
2. Dirty data simulation
3. Cleaning
4. Great Expectations validation
5. Forecasting (Prophet)
6. Threshold engine
7. Stock-risk engine
8. Financial impact engine
9. Movement optimizer
10. Load to PostgreSQL

---

## 1. Prerequisites

- Python 3.11+ (tested with the dependency versions below)
- PostgreSQL server (local or remote), running and accepting TCP/IP connections
- Windows, macOS, or Linux with a shell / PowerShell

---

## 2. Install Dependencies

From the project root (`Week_4/`), create and activate a virtual environment, then
install the required packages.

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### `requirements.txt`
```
numpy==2.3.3
pandas==3.0.3
openpyxl==3.1.5
matplotlib==3.10.6
seaborn==0.13.2
plotly==6.9.0
great_expectations==1.19.0
scikit-learn==1.7.0
joblib==1.5.2
prophet==1.3.0
cmdstanpy==1.3.0
requests==2.34.2
retry-requests==2.0.0
ipykernel==7.3.0
psycopg2-binary
sqlalchemy
python-dotenv
```

> **Note:** `prophet` and `cmdstanpy` compile a Stan model on first use — the first
> pipeline run will take longer while `cmdstanpy` installs its backend. This is
> expected and only happens once.

---

## 3. Set Up the `.env` File

Create a file named `.env` in the project root (same folder as `reset_pipeline.py`
and the `pipelines/` directory). This stores your PostgreSQL connection details and
any environment settings — never commit this file to version control.

```env
# --- PostgreSQL connection ---
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kpc_pipeline
DB_USER=postgres
DB_PASSWORD=your_password_here

# --- Pipeline environment ---
ENVIRONMENT=development
```

Make sure the PostgreSQL server is running and reachable before starting the
pipeline — if it isn't, the reset step will skip the database reset (you'll see a
`Connection refused` message) and the final load-to-PostgreSQL stage will fail.

Add `.env` to your `.gitignore` if it isn't there already.

---

## 4. Reset the Environment (optional but recommended)

Before a fresh run, clear out generated data, logs, and previous pipeline tables:

```bash
python -m reset_pipeline
```

This clears `data/raw`, `data/dirty`, `data/clean`, `data/processed`,
`data/forecasts`, `data/gold`, and `logs/`, removes the `great_expectations`
folder and Python caches, and drops the pipeline's PostgreSQL tables
(`forecast_results`, `inventory_thresholds`, `stock_risk_analysis`,
`movement_recommendations`, `financial_summary`, `financial_impact`).

---

## 5. Run the Pipeline

```bash
python -m pipelines.run_pipeline
```

This runs all ten stages end-to-end. On completion you'll find:

- Generated/cleaned CSVs in `data/raw`, `data/dirty`, `data/clean`
- Gold-layer outputs in `data/gold/` (forecasts, thresholds, risk analysis,
  movement recommendations, financial impact)
- The same tables loaded into your PostgreSQL database
- Logs in `logs/`

---

## 6. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `Connection refused` on reset/load | PostgreSQL isn't running, or `.env` values are wrong | Start PostgreSQL and double-check `DB_HOST`/`DB_PORT`/`DB_USER`/`DB_PASSWORD` |
| Great Expectations `FAIL`/`ALERT` rows | Expected — the pipeline intentionally injects dirty data to test validation | Review `data/gold` outputs and validation logs; this is not necessarily an error |
| Slow first forecasting run | `cmdstanpy` compiling its Stan backend | Wait for it to finish; subsequent runs are faster |
| `ModuleNotFoundError` | Virtual environment not activated, or a dependency missing | Re-activate `venv` and re-run `pip install -r requirements.txt` |
