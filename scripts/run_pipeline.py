from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ecommerce_analytics.pipeline import run_pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the end-to-end analytics pipeline.")
    parser.add_argument("--regenerate", action="store_true", help="Regenerate raw data before analysis.")
    args = parser.parse_args()
    run_pipeline(force_generate=args.regenerate)


if __name__ == "__main__":
    main()

