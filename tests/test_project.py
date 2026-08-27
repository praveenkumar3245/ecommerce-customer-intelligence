from __future__ import annotations

import json
import sqlite3
import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ecommerce_analytics.quality import validate_data  # noqa: E402


class EcommerceAnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw = ROOT / "data" / "raw"
        cls.frames = {
            name: pd.read_csv(raw / f"{name}.csv", low_memory=False)
            for name in ("customers", "products", "sessions", "orders", "order_items")
        }
        cls.database = ROOT / "data" / "warehouse" / "ecommerce_analytics.sqlite"

    def test_python_quality_suite_passes(self) -> None:
        report = validate_data(**self.frames)
        self.assertTrue(report["passed"].all())
        self.assertGreaterEqual(len(report), 15)

    def test_sql_quality_suite_has_zero_failures(self) -> None:
        query = (ROOT / "sql" / "01_data_quality.sql").read_text(encoding="utf-8")
        with sqlite3.connect(self.database) as connection:
            audit = pd.read_sql_query(query, connection)
        self.assertEqual(int(audit["failures"].sum()), 0)

    def test_funnel_is_monotonic(self) -> None:
        sessions = self.frames["sessions"]
        totals = sessions[["viewed_product", "added_to_cart", "checkout_started", "converted"]].sum()
        self.assertGreaterEqual(totals["viewed_product"], totals["added_to_cart"])
        self.assertGreaterEqual(totals["added_to_cart"], totals["checkout_started"])
        self.assertGreaterEqual(totals["checkout_started"], totals["converted"])

    def test_kpis_reconcile_to_order_data(self) -> None:
        kpis = json.loads((ROOT / "reports" / "kpi_summary.json").read_text(encoding="utf-8"))
        orders = self.frames["orders"]
        completed = orders[orders["order_status"].eq("Completed")]
        self.assertAlmostEqual(kpis["net_revenue"], orders["net_revenue"].sum(), places=2)
        self.assertEqual(kpis["completed_orders"], len(completed))
        self.assertAlmostEqual(kpis["aov"], completed["net_revenue"].mean(), places=2)

    def test_every_conversion_maps_to_one_order(self) -> None:
        sessions = self.frames["sessions"]
        converted_order_ids = sessions.loc[sessions["converted"].eq(1), "order_id"]
        self.assertTrue(converted_order_ids.notna().all())
        self.assertEqual(converted_order_ids.nunique(), len(self.frames["orders"]))


if __name__ == "__main__":
    unittest.main()

