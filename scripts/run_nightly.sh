#!/usr/bin/env bash
# Nightly wrapper for cron. Adjust PROJECT_DIR and the venv path.
set -euo pipefail

cd -
mkdir -p logs

source venv/bin/activate
python run_pipeline.py >> logs/cron.log 2>&1
