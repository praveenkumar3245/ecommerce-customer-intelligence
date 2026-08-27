#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" scripts/run_pipeline.py --regenerate
"$PYTHON_BIN" -m unittest discover -s tests -v

echo "Pipeline complete. Open reports/figures/executive_dashboard.png or excel/Ecommerce_Analytics_Dashboard.xlsx."

