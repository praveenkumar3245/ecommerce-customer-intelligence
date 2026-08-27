from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .paths import CONFIG_PATH, RAW_DIR, ensure_project_dirs
from .quality import validate_data


CHANNELS = ["Organic Search", "Paid Search", "Social", "Email", "Affiliate", "Direct"]
CHANNEL_WEIGHTS = np.array([0.27, 0.23, 0.16, 0.11, 0.09, 0.14])
DEVICES = ["Mobile", "Desktop", "Tablet"]
DEVICE_WEIGHTS = [0.60, 0.34, 0.06]

STATE_DATA = [
    ("North Rhine-Westphalia", "West", "Cologne", 0.215),
    ("Bavaria", "South", "Munich", 0.158),
    ("Baden-Wuerttemberg", "South", "Stuttgart", 0.135),
    ("Lower Saxony", "North", "Hanover", 0.096),
    ("Hesse", "Central", "Frankfurt", 0.076),
    ("Berlin", "East", "Berlin", 0.044),
    ("Saxony", "East", "Leipzig", 0.049),
    ("Rhineland-Palatinate", "West", "Mainz", 0.049),
    ("Schleswig-Holstein", "North", "Kiel", 0.035),
    ("Brandenburg", "East", "Potsdam", 0.030),
    ("Saxony-Anhalt", "East", "Magdeburg", 0.026),
    ("Thuringia", "East", "Erfurt", 0.025),
    ("Hamburg", "North", "Hamburg", 0.023),
    ("Mecklenburg-Western Pomerania", "North", "Rostock", 0.019),
    ("Saarland", "West", "Saarbruecken", 0.012),
    ("Bremen", "North", "Bremen", 0.007),
]

CATEGORY_SPECS = {
    "Electronics": (["Audio", "Smart Home", "Accessories"], (24, 320), 0.33),
    "Home & Living": (["Kitchen", "Decor", "Storage"], (12, 180), 0.28),
    "Sports & Outdoors": (["Fitness", "Cycling", "Outdoor"], (15, 220), 0.30),
    "Beauty & Care": (["Skincare", "Haircare", "Wellness"], (8, 95), 0.24),
    "Fashion": (["Apparel", "Footwear", "Bags"], (14, 160), 0.38),
    "Books & Stationery": (["Books", "Office", "Creative"], (5, 65), 0.22),
    "Pet Supplies": (["Food", "Care", "Accessories"], (6, 110), 0.26),
}


def _load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sample_dates(rng: np.random.Generator, start: pd.Timestamp, end: pd.Timestamp, n: int) -> pd.DatetimeIndex:
    days = (end - start).days
    offsets = rng.integers(0, days + 1, size=n)
    return pd.to_datetime(start + pd.to_timedelta(offsets, unit="D"))


def _build_customers(rng: np.random.Generator, cfg: dict) -> pd.DataFrame:
    n = cfg["n_customers"]
    start = pd.Timestamp(cfg["start_date"])
    end = pd.Timestamp(cfg["end_date"])
    states = [row[0] for row in STATE_DATA]
    weights = np.array([row[3] for row in STATE_DATA])
    weights = weights / weights.sum()
    state_idx = rng.choice(len(states), size=n, p=weights)

    signup_dates = _sample_dates(rng, start, end - pd.Timedelta(days=30), n)
    acquisition_channel = rng.choice(CHANNELS, size=n, p=CHANNEL_WEIGHTS)
    preferred_device = rng.choice(DEVICES, size=n, p=DEVICE_WEIGHTS)
    loyalty = rng.beta(2.2, 4.5, size=n)
    affiliate_boost = np.where(acquisition_channel == "Affiliate", 0.16, 0.0)
    email_boost = np.where(acquisition_channel == "Email", 0.11, 0.0)
    loyalty = np.clip(loyalty + affiliate_boost + email_boost, 0, 1)

    return pd.DataFrame(
        {
            "customer_id": [f"C{i:06d}" for i in range(1, n + 1)],
            "signup_date": signup_dates.strftime("%Y-%m-%d"),
            "acquisition_channel": acquisition_channel,
            "state": [STATE_DATA[i][0] for i in state_idx],
            "region": [STATE_DATA[i][1] for i in state_idx],
            "city": [STATE_DATA[i][2] for i in state_idx],
            "preferred_device": preferred_device,
            "marketing_consent": rng.choice([0, 1], size=n, p=[0.28, 0.72]),
            "loyalty_score": np.round(loyalty, 4),
        }
    )


def _build_products(rng: np.random.Generator, cfg: dict) -> pd.DataFrame:
    n = cfg["n_products"]
    categories = list(CATEGORY_SPECS)
    category = rng.choice(categories, size=n, p=[0.20, 0.18, 0.15, 0.13, 0.16, 0.10, 0.08])
    rows: list[dict] = []
    adjective = ["Core", "Nova", "Urban", "Alpine", "Pure", "Flex", "Prime", "Eco", "Studio", "Motion"]
    noun = ["One", "Plus", "Pro", "Mini", "Max", "Select", "Go", "Edge", "Essential", "Classic"]
    for i, cat in enumerate(category, start=1):
        subcats, price_range, cost_ratio = CATEGORY_SPECS[cat]
        subcat = rng.choice(subcats)
        low, high = price_range
        price = float(np.round(np.exp(rng.uniform(np.log(low), np.log(high))), 2))
        margin_noise = rng.uniform(-0.05, 0.05)
        unit_cost = float(np.round(price * np.clip(1 - cost_ratio + margin_noise, 0.45, 0.88), 2))
        rows.append(
            {
                "product_id": f"P{i:04d}",
                "sku": f"{cat[:3].upper().replace(' ', '')}-{i:05d}",
                "product_name": f"{rng.choice(adjective)} {subcat} {rng.choice(noun)}",
                "category": cat,
                "subcategory": subcat,
                "brand": f"Brand {chr(65 + (i % 12))}",
                "unit_price": price,
                "unit_cost": unit_cost,
                "launch_date": _sample_dates(rng, pd.Timestamp("2022-01-01"), pd.Timestamp(cfg["end_date"]), 1)[0].strftime("%Y-%m-%d"),
            }
        )
    return pd.DataFrame(rows)


def _choose_session_channel(
    rng: np.random.Generator, customer_idx: np.ndarray, customer_channels: np.ndarray, known: np.ndarray
) -> np.ndarray:
    channel = rng.choice(CHANNELS, size=len(customer_idx), p=CHANNEL_WEIGHTS)
    keep_acquisition = known & (rng.random(len(customer_idx)) < 0.46)
    channel[keep_acquisition] = customer_channels[customer_idx[keep_acquisition]]
    return channel


def _build_sessions(rng: np.random.Generator, cfg: dict, customers: pd.DataFrame) -> pd.DataFrame:
    n = cfg["n_sessions"]
    start = pd.Timestamp(cfg["start_date"])
    end = pd.Timestamp(cfg["end_date"])
    known = rng.random(n) < 0.78

    engagement_weights = 0.25 + customers["loyalty_score"].to_numpy() ** 1.6
    engagement_weights /= engagement_weights.sum()
    customer_idx = rng.choice(len(customers), size=n, p=engagement_weights)
    customer_ids = customers["customer_id"].to_numpy()[customer_idx].astype(object)
    customer_ids[~known] = None

    signup = pd.to_datetime(customers["signup_date"]).to_numpy(dtype="datetime64[D]")
    start_day = np.datetime64(start.date(), "D")
    end_day = np.datetime64(end.date(), "D")
    available_start = np.where(known, signup[customer_idx], start_day)
    span = (end_day - available_start).astype(int)
    offset = (rng.random(n) * (span + 1)).astype(int)
    session_dates = available_start + offset.astype("timedelta64[D]")

    customer_channels = customers["acquisition_channel"].to_numpy()
    channel = _choose_session_channel(rng, customer_idx, customer_channels, known)
    preferred_device = customers["preferred_device"].to_numpy()[customer_idx]
    device = rng.choice(DEVICES, size=n, p=DEVICE_WEIGHTS)
    use_preferred = known & (rng.random(n) < 0.64)
    device[use_preferred] = preferred_device[use_preferred]

    channel_factor = pd.Series(channel).map(
        {"Organic Search": 0.00, "Paid Search": -0.02, "Social": -0.05, "Email": 0.09, "Affiliate": 0.07, "Direct": 0.05}
    ).to_numpy()
    device_factor = pd.Series(device).map({"Mobile": -0.035, "Desktop": 0.035, "Tablet": -0.01}).to_numpy()
    loyalty = customers["loyalty_score"].to_numpy()[customer_idx] * known
    known_factor = known.astype(float) * 0.035

    p_view = np.clip(0.71 + channel_factor * 0.35 + device_factor, 0.56, 0.88)
    viewed = rng.random(n) < p_view
    p_add = np.clip(0.235 + channel_factor + loyalty * 0.105 + device_factor, 0.11, 0.48)
    added = viewed & (rng.random(n) < p_add)
    p_checkout = np.clip(0.57 + channel_factor * 0.7 + loyalty * 0.08 + device_factor, 0.36, 0.78)
    checkout = added & (rng.random(n) < p_checkout)
    p_convert = np.clip(0.67 + channel_factor * 0.65 + loyalty * 0.10 + known_factor + device_factor, 0.40, 0.88)
    converted = checkout & (rng.random(n) < p_convert)

    campaign_map = {
        "Organic Search": ["SEO - Always On", "Content Guides", "Brand Search"],
        "Paid Search": ["Brand - DE", "Shopping - Core", "Nonbrand - High Intent"],
        "Social": ["Prospecting Video", "Retargeting Dynamic", "Creator Partnership"],
        "Email": ["Lifecycle CRM", "Weekly Offers", "Cart Recovery"],
        "Affiliate": ["Premium Publishers", "Cashback Partners", "Comparison Sites"],
        "Direct": ["Direct / None"],
    }
    campaign = np.array([rng.choice(campaign_map[ch]) for ch in channel], dtype=object)

    state_map = customers["state"].to_numpy()[customer_idx].astype(object)
    region_map = customers["region"].to_numpy()[customer_idx].astype(object)
    guest_state_idx = rng.choice(len(STATE_DATA), size=(~known).sum(), p=np.array([r[3] for r in STATE_DATA]) / sum(r[3] for r in STATE_DATA))
    state_map[~known] = [STATE_DATA[i][0] for i in guest_state_idx]
    region_map[~known] = [STATE_DATA[i][1] for i in guest_state_idx]

    pages = 1 + viewed.astype(int) * rng.integers(1, 5, n) + added.astype(int) * rng.integers(1, 4, n) + checkout.astype(int) * rng.integers(1, 3, n)
    duration = np.maximum(12, (pages * rng.normal(36, 9, n) + added * 55 + checkout * 70).astype(int))

    sessions = pd.DataFrame(
        {
            "session_id": [f"S{i:07d}" for i in range(1, n + 1)],
            "customer_id": customer_ids,
            "session_date": pd.to_datetime(session_dates).strftime("%Y-%m-%d"),
            "channel": channel,
            "campaign": campaign,
            "device": device,
            "state": state_map,
            "region": region_map,
            "pages_viewed": pages,
            "session_duration_seconds": duration,
            "viewed_product": viewed.astype(int),
            "added_to_cart": added.astype(int),
            "checkout_started": checkout.astype(int),
            "converted": converted.astype(int),
            "order_id": None,
        }
    )
    return sessions.sort_values(["session_date", "session_id"]).reset_index(drop=True)


def _build_orders_and_items(
    rng: np.random.Generator, sessions: pd.DataFrame, customers: pd.DataFrame, products: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    converted_idx = sessions.index[sessions["converted"].eq(1)].to_numpy()
    order_ids = np.array([f"O{i:06d}" for i in range(1, len(converted_idx) + 1)], dtype=object)
    sessions.loc[converted_idx, "order_id"] = order_ids

    customer_acquisition = customers.set_index("customer_id")["acquisition_channel"].to_dict()
    product_price = products["unit_price"].to_numpy()
    product_cost = products["unit_cost"].to_numpy()
    category = products["category"].to_numpy()
    popularity = np.exp(-np.arange(len(products)) / (len(products) * 0.85))

    orders_rows: list[dict] = []
    item_rows: list[dict] = []
    item_id = 1
    last_order_date: dict[str, pd.Timestamp] = {}
    customer_order_number: dict[str, int] = {}

    for order_no, (session_index, order_id) in enumerate(zip(converted_idx, order_ids), start=1):
        session = sessions.loc[session_index]
        customer_id = session["customer_id"]
        order_date = pd.Timestamp(session["session_date"])
        acquisition = customer_acquisition.get(customer_id, "Guest")
        affinity_boost = 1 if acquisition in {"Affiliate", "Email"} else 0
        n_items = int(np.clip(1 + rng.poisson(0.75 + 0.28 * affinity_boost), 1, 5))

        weights = popularity.copy()
        if acquisition == "Affiliate":
            weights *= np.power(product_price / np.median(product_price), 0.34)
        if session["channel"] == "Email":
            weights *= np.where(np.isin(category, ["Beauty & Care", "Pet Supplies", "Home & Living"]), 1.35, 0.92)
        weights /= weights.sum()
        selected_products = rng.choice(len(products), size=n_items, replace=False, p=weights)

        gross = 0.0
        cost = 0.0
        for product_index in selected_products:
            qty = int(rng.choice([1, 2, 3], p=[0.81, 0.16, 0.03]))
            line_gross = float(np.round(product_price[product_index] * qty, 2))
            line_cost = float(np.round(product_cost[product_index] * qty, 2))
            gross += line_gross
            cost += line_cost
            item_rows.append(
                {
                    "order_item_id": f"OI{item_id:07d}",
                    "order_id": order_id,
                    "product_id": products.iloc[product_index]["product_id"],
                    "quantity": qty,
                    "unit_price": float(product_price[product_index]),
                    "unit_cost": float(product_cost[product_index]),
                    "line_gross_revenue": line_gross,
                    "line_cost": line_cost,
                }
            )
            item_id += 1

        discount_rate = {
            "Organic Search": 0.035,
            "Paid Search": 0.065,
            "Social": 0.085,
            "Email": 0.075,
            "Affiliate": 0.055,
            "Direct": 0.025,
        }[session["channel"]]
        discount_rate = float(np.clip(rng.normal(discount_rate, 0.025), 0, 0.20))
        discount = float(np.round(gross * discount_rate, 2))
        shipping = 0.0 if gross - discount >= 59 else 4.90

        primary_categories = category[selected_products]
        return_probability = 0.035 + (0.055 if "Fashion" in primary_categories else 0) + (0.018 if session["device"] == "Mobile" else 0)
        status_draw = rng.random()
        if status_draw < 0.018:
            status = "Cancelled"
            refund = float(np.round(gross - discount + shipping, 2))
        elif status_draw < 0.018 + return_probability:
            status = "Returned"
            refund = float(np.round(gross - discount + shipping, 2))
        else:
            status = "Completed"
            refund = 0.0
        net_revenue = float(np.round(max(0.0, gross - discount + shipping - refund), 2))
        gross_profit = float(np.round(max(0.0, net_revenue - cost if status == "Completed" else 0.0), 2))

        previous = last_order_date.get(customer_id) if customer_id else None
        order_number = customer_order_number.get(customer_id, 0) + 1 if customer_id else 1
        days_since_previous = (order_date - previous).days if previous is not None else None
        if customer_id:
            last_order_date[customer_id] = order_date
            customer_order_number[customer_id] = order_number

        orders_rows.append(
            {
                "order_id": order_id,
                "session_id": session["session_id"],
                "customer_id": customer_id,
                "order_date": order_date.strftime("%Y-%m-%d"),
                "channel": session["channel"],
                "campaign": session["campaign"],
                "device": session["device"],
                "state": session["state"],
                "region": session["region"],
                "order_status": status,
                "customer_order_number": order_number,
                "days_since_previous_order": days_since_previous,
                "gross_revenue": round(gross, 2),
                "discount_amount": discount,
                "shipping_revenue": shipping,
                "refund_amount": refund,
                "net_revenue": net_revenue,
                "cost_of_goods": round(cost, 2),
                "gross_profit": gross_profit,
            }
        )

    return pd.DataFrame(orders_rows), pd.DataFrame(item_rows), sessions


def generate(config_path: Path = CONFIG_PATH) -> None:
    ensure_project_dirs()
    cfg = _load_config(config_path)
    rng = np.random.default_rng(cfg["seed"])

    customers = _build_customers(rng, cfg)
    products = _build_products(rng, cfg)
    sessions = _build_sessions(rng, cfg, customers)
    orders, order_items, sessions = _build_orders_and_items(rng, sessions, customers, products)
    quality = validate_data(customers, products, sessions, orders, order_items)

    for name, frame in (
        ("customers", customers),
        ("products", products),
        ("sessions", sessions),
        ("orders", orders),
        ("order_items", order_items),
    ):
        frame.to_csv(RAW_DIR / f"{name}.csv", index=False)
    quality.to_csv(RAW_DIR / "data_quality_report.csv", index=False)

    metadata = {
        "description": "Synthetic but behaviorally realistic German e-commerce data generated for portfolio use.",
        "seed": cfg["seed"],
        "date_range": [cfg["start_date"], cfg["end_date"]],
        "snapshot_date": cfg["snapshot_date"],
        "row_counts": {
            "customers": len(customers),
            "products": len(products),
            "sessions": len(sessions),
            "orders": len(orders),
            "order_items": len(order_items),
        },
        "quality_checks_passed": int(quality["passed"].sum()),
        "quality_checks_total": len(quality),
    }
    (RAW_DIR / "dataset_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the synthetic e-commerce dataset.")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args()
    generate(args.config)


if __name__ == "__main__":
    main()

