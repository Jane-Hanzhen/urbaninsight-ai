#!/usr/bin/env bash

set -e

for variable_name in URBANINSIGHT_DATA_PATH URBANINSIGHT_DB_PATH PORT; do
  if [ -z "${!variable_name:-}" ]; then
    echo "Error: required environment variable ${variable_name} is not set." >&2
    exit 1
  fi
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/3] Importing indicators..."
python scripts/import_data.py \
  --csv "$URBANINSIGHT_DATA_PATH" \
  --database "$URBANINSIGHT_DB_PATH"

echo "[2/3] Running PCA-TOPSIS analysis..."
python scripts/run_analysis.py \
  --database "$URBANINSIGHT_DB_PATH"

echo "[3/3] Starting FastAPI..."
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "$PORT"
