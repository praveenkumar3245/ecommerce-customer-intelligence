from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import pandas as pd


@dataclass
class CheckResult:
    check: str
    passed: bool
    observed: Any
    expectation: str


def validate_data(
    customers: pd.DataFrame,
    products: pd.DataFrame,
    sessions: pd.DataFrame,
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
) -> pd.DataFrame:
    """Run referential, logical, and financial controls over the generated data."""

    checks: list[CheckResult] = []

    def add(check: str, passed: bool, observed: Any, expectation: str) -> None:
        checks.append(CheckResult(check, bool(passed), observed, expectation))

    for label, frame, key in (
        ("customers", customers, "customer_id"),
        ("products", products, "product_id"),
        ("sessions", sessions, "session_id"),
        ("orders", orders, "order_id"),
        ("order_items", order_items, "order_item_id"),
    ):
        duplicates = int(frame[key].duplicated().sum())
        add(f"{label}: primary key uniqueness", duplicates == 0, duplicates, "0 duplicate keys")

    invalid_session_customers = set(sessions["customer_id"].dropna()) - set(customers["customer_id"])
    invalid_order_customers = set(orders["customer_id"].dropna()) - set(customers["customer_id"])
    invalid_item_orders = set(order_items["order_id"]) - set(orders["order_id"])
    invalid_item_products = set(order_items["product_id"]) - set(products["product_id"])
    add("sessions -> customers", not invalid_session_customers, len(invalid_session_customers), "0 orphan keys")
    add("orders -> customers", not invalid_order_customers, len(invalid_order_customers), "0 orphan keys")
    add("order_items -> orders", not invalid_item_orders, len(invalid_item_orders), "0 orphan keys")
    add("order_items -> products", not invalid_item_products, len(invalid_item_products), "0 orphan keys")

    funnel_violations = int(
        (
            (sessions["added_to_cart"] > sessions["viewed_product"])
            | (sessions["checkout_started"] > sessions["added_to_cart"])
            | (sessions["converted"] > sessions["checkout_started"])
        ).sum()
    )
    add("funnel stages are monotonic", funnel_violations == 0, funnel_violations, "0 stage-order violations")

    converted_session_orders = sessions.loc[sessions["converted"].eq(1), "order_id"].notna().all()
    unconverted_session_orders = sessions.loc[sessions["converted"].eq(0), "order_id"].isna().all()
    add(
        "order assignment matches conversion",
        converted_session_orders and unconverted_session_orders,
        bool(converted_session_orders and unconverted_session_orders),
        "converted sessions have one order; others have none",
    )

    item_rollup = order_items.groupby("order_id", as_index=False)["line_gross_revenue"].sum()
    finance = orders[["order_id", "gross_revenue"]].merge(item_rollup, on="order_id", how="left")
    max_order_variance = float((finance["gross_revenue"] - finance["line_gross_revenue"]).abs().max())
    add("order totals reconcile to line items", max_order_variance < 0.011, round(max_order_variance, 6), "variance < EUR 0.01")

    expected_net = (
        orders["gross_revenue"]
        - orders["discount_amount"]
        + orders["shipping_revenue"]
        - orders["refund_amount"]
    ).round(2)
    max_net_variance = float((orders["net_revenue"] - expected_net).abs().max())
    add("net revenue formula", max_net_variance < 0.011, round(max_net_variance, 6), "variance < EUR 0.01")

    nonnegative = ["gross_revenue", "discount_amount", "shipping_revenue", "refund_amount", "net_revenue"]
    negative_values = int((orders[nonnegative] < 0).sum().sum())
    add("financial values are non-negative", negative_values == 0, negative_values, "0 negative values")

    order_dates = pd.to_datetime(orders["order_date"])
    session_dates = pd.to_datetime(sessions["session_date"])
    add(
        "date range",
        order_dates.min() >= session_dates.min() and order_dates.max() <= session_dates.max(),
        f"{order_dates.min().date()} to {order_dates.max().date()}",
        "orders fall inside the session date range",
    )

    result = pd.DataFrame(asdict(item) for item in checks)
    if not result["passed"].all():
        failures = result.loc[~result["passed"]].to_string(index=False)
        raise ValueError(f"Data-quality validation failed:\n{failures}")
    return result

