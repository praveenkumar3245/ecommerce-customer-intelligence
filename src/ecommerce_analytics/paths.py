from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "project_config.json"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
WAREHOUSE_DIR = PROJECT_ROOT / "data" / "warehouse"
REPORT_DIR = PROJECT_ROOT / "reports"
FIGURE_DIR = REPORT_DIR / "figures"
ARTIFACT_DIR = PROJECT_ROOT / "artifacts"
SQL_DIR = PROJECT_ROOT / "sql"


def ensure_project_dirs() -> None:
    for path in (RAW_DIR, PROCESSED_DIR, WAREHOUSE_DIR, REPORT_DIR, FIGURE_DIR, ARTIFACT_DIR):
        path.mkdir(parents=True, exist_ok=True)

