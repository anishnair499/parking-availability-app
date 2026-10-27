#!/bin/bash
set -euo pipefail

# cron has no PATH/cwd to speak of, so pin both here
cd "$(dirname "$0")"
PY="../venv/bin/python"

echo "=== forecast run $(date '+%Y-%m-%d %H:%M:%S') ==="

# TODO: refresh availability.csv here (pull from wherever ayaan's sensor data lands)
# the forecast is anchored on the newest reading, so a stale csv means a stale forecast

# skip publishing if the newest reading is older than max_min (15), so the app's
# sensors-down banner stays honest instead of being masked by a fresh-looking forecast
$PY -c "
import sys
from ingest import load_csv, warn_stale, max_min
sys.exit(0 if warn_stale(load_csv()) <= max_min else 2)
" || { echo "csv is stale, not publishing"; exit 0; }

$PY predict_week.py
