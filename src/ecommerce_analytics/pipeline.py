from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from .generate_data import generate
from .paths import (
    ARTIFACT_DIR,
    CONFIG_PATH,
    FIGURE_DIR,
    PROCESSED_DIR,
    PROJECT_ROOT,
    RAW_DIR,
    REPORT_DIR,
    SQL_DIR,
    WAREHOUSE_DIR,
    ensure_project_dirs,
)
from .quality import validate_data


def _load_raw() -> dict[str, pd.DataFrame]:
    return {
        name: pd.read_csv(RAW_DIR / f"{name}.csv", low_memory=False)
        for name in ("customers", "products", "sessions", "orders", "order_items")
    }


def _create_warehouse(frames: dict[str, pd.DataFrame]) -> Path:
    database_path = WAREHOUSE_DIR / "ecommerce_analytics.sqlite"
    if database_path.exists():
        database_path.unlink()
    with sqlite3.connect(database_path) as connection:
        for table_name, frame in frames.items():
            frame.to_sql(table_name, connection, index=False, if_exists="replace")
        connection.executescript((SQL_DIR / "00_database_objects.sql").read_text(encoding="utf-8"))
        connection.commit()
    return database_path


def _query(connection: sqlite3.Connection, filename: str) -> pd.DataFrame:
    return pd.read_sql_query((SQL_DIR / filename).read_text(encoding="utf-8"), connection)


def _derive_outputs(database_path: Path, cfg: dict) -> dict[str, pd.DataFrame]:
    with sqlite3.connect(database_path) as connection:
        monthly = _query(connection, "02_monthly_kpis.sql")
        rfm = _query(connection, "03_customer_rfm.sql")
        cohort = _query(connection, "04_cohort_retention.sql")
        funnel = _query(connection, "05_funnel_by_channel.sql")
        products = _query(connection, "06_product_performance.sql")
        regions = _query(connection, "07_regional_performance.sql")
        channel_value = _query(connection, "08_channel_90d_value.sql")

    monthly["revenue_mom_rate"] = monthly["net_revenue"].pct_change().replace([np.inf, -np.inf], np.nan)
    monthly["orders_mom_rate"] = monthly["completed_orders"].pct_change().replace([np.inf, -np.inf], np.nan)

    segment_summary = (
        rfm.groupby("rfm_segment", as_index=False)
        .agg(
            customers=("customer_id", "nunique"),
            net_revenue=("monetary_value", "sum"),
            avg_customer_value=("monetary_value", "mean"),
            avg_recency_days=("recency_days", "mean"),
            churn_rate=("churned_90d", "mean"),
        )
        .sort_values("net_revenue", ascending=False)
    )
    segment_summary[["net_revenue", "avg_customer_value", "avg_recency_days", "churn_rate"]] = segment_summary[
        ["net_revenue", "avg_customer_value", "avg_recency_days", "churn_rate"]
    ].round(4)

    category_summary = (
        products.groupby("category", as_index=False)
        .agg(
            units_sold=("units_sold", "sum"),
            orders=("orders", "sum"),
            net_revenue=("net_revenue", "sum"),
            gross_profit=("gross_profit", "sum"),
            avg_unit_return_rate=("unit_return_rate", "mean"),
        )
        .sort_values("net_revenue", ascending=False)
    )
    category_summary["gross_margin_rate"] = (
        category_summary["gross_profit"] / category_summary["net_revenue"].replace(0, np.nan)
    )
    category_summary = category_summary.round(4)

    return {
        "monthly_kpis": monthly,
        "customer_rfm": rfm,
        "segment_summary": segment_summary,
        "cohort_retention": cohort,
        "funnel_by_channel": funnel,
        "product_performance": products,
        "category_summary": category_summary,
        "regional_performance": regions,
        "channel_90d_value": channel_value,
    }


def _overall_kpis(frames: dict[str, pd.DataFrame], outputs: dict[str, pd.DataFrame]) -> dict:
    sessions = frames["sessions"]
    orders = frames["orders"]
    completed = orders[orders["order_status"].eq("Completed")]
    purchasers = completed["customer_id"].dropna()
    customer_frequency = completed.dropna(subset=["customer_id"]).groupby("customer_id")["order_id"].nunique()
    rfm = outputs["customer_rfm"]
    cohort = outputs["cohort_retention"]
    month_one = cohort[cohort["months_since_first_order"].eq(1)]
    month_one_retention = (
        float(np.average(month_one["retention_rate"], weights=month_one["cohort_size"])) if not month_one.empty else 0.0
    )

    return {
        "net_revenue": round(float(orders["net_revenue"].sum()), 2),
        "gross_revenue": round(float(orders["gross_revenue"].sum()), 2),
        "gross_profit": round(float(orders["gross_profit"].sum()), 2),
        "gross_margin_rate": round(float(orders["gross_profit"].sum() / max(orders["net_revenue"].sum(), 1)), 4),
        "orders": int(len(orders)),
        "completed_orders": int(len(completed)),
        "purchasing_customers": int(purchasers.nunique()),
        "sessions": int(len(sessions)),
        "aov": round(float(completed["net_revenue"].mean()), 2),
        "conversion_rate": round(float(sessions["converted"].mean()), 4),
        "return_rate": round(float(orders["order_status"].eq("Returned").mean()), 4),
        "repeat_purchase_rate": round(float((customer_frequency > 1).mean()), 4),
        "churn_rate_90d": round(float(rfm["churned_90d"].mean()), 4),
        "month_1_retention_rate": round(month_one_retention, 4),
    }


def _build_recommendations(
    frames: dict[str, pd.DataFrame], outputs: dict[str, pd.DataFrame], kpis: dict
) -> list[dict[str, str]]:
    channel = outputs["channel_90d_value"].copy()
    best = channel.sort_values("revenue_90d_per_acquired_customer", ascending=False).iloc[0]
    weighted_avg = float(channel["revenue_90d"].sum() / channel["acquired_customers"].sum())
    premium = (best["revenue_90d_per_acquired_customer"] / weighted_avg - 1) if weighted_avg else 0

    funnel = outputs["funnel_by_channel"].copy()
    funnel["checkout_gap"] = 1 - funnel["checkout_to_order_rate"]
    leak = funnel.sort_values("checkout_gap", ascending=False).iloc[0]
    recoverable_orders = int(round(leak["checkouts"] * 0.02))
    recoverable_revenue = recoverable_orders * kpis["aov"]

    at_risk = outputs["customer_rfm"].query("rfm_segment == 'At Risk'")
    at_risk_value = float(at_risk["monetary_value"].sum())

    categories = outputs["category_summary"]
    risky_category = categories.sort_values("avg_unit_return_rate", ascending=False).iloc[0]

    region_orders = frames["orders"].copy()
    region_orders["order_date"] = pd.to_datetime(region_orders["order_date"])
    latest = region_orders[region_orders["order_date"].between("2025-10-01", "2025-12-31")].groupby("region")["net_revenue"].sum()
    prior = region_orders[region_orders["order_date"].between("2025-07-01", "2025-09-30")].groupby("region")["net_revenue"].sum()
    growth = ((latest - prior) / prior.replace(0, np.nan)).dropna().sort_values(ascending=False)
    growth_region = growth.index[0]
    growth_rate = float(growth.iloc[0])

    return [
        {
            "priority": "High",
            "decision": f"Increase controlled acquisition tests in {best['acquisition_channel']}",
            "evidence": (
                f"Matured customers acquired through {best['acquisition_channel']} generated EUR "
                f"{best['revenue_90d_per_acquired_customer']:.2f} per acquired customer in 90 days, "
                f"{premium:.1%} above the all-channel average."
            ),
            "action": "Reallocate 10% of marginal prospecting budget for a four-week incrementality test; guard on CAC payback and volume quality.",
            "owner": "Growth Marketing",
            "expected_impact": "Higher 90-day revenue per acquired customer",
        },
        {
            "priority": "High",
            "decision": f"Reduce checkout abandonment for {leak['channel']}",
            "evidence": (
                f"{leak['channel']} has the weakest checkout-to-order rate at {leak['checkout_to_order_rate']:.1%}. "
                f"A 2 percentage-point lift is worth about {recoverable_orders:,} orders / EUR {recoverable_revenue:,.0f} at current AOV."
            ),
            "action": "Test guest checkout, payment-message clarity, and mobile form simplification; measure incremental completed orders.",
            "owner": "Product & CRO",
            "expected_impact": f"Approximately EUR {recoverable_revenue:,.0f} revenue per observed period",
        },
        {
            "priority": "High",
            "decision": "Launch a value-based win-back program for at-risk customers",
            "evidence": f"{len(at_risk):,} at-risk customers represent EUR {at_risk_value:,.0f} in historical net revenue.",
            "action": "Prioritize high-monetary customers, personalize by last purchased category, and hold out 10% to measure incrementality.",
            "owner": "CRM & Retention",
            "expected_impact": "Improved 90-day retention without blanket discounting",
        },
        {
            "priority": "Medium",
            "decision": f"Address returns in {risky_category['category']}",
            "evidence": (
                f"{risky_category['category']} has the highest average product return rate at "
                f"{risky_category['avg_unit_return_rate']:.1%}, putting revenue and service costs at risk."
            ),
            "action": "Audit the top-returned SKUs, enrich product-detail content, and test fit/compatibility guidance before scaling promotions.",
            "owner": "Merchandising",
            "expected_impact": "Lower refunds and better contribution margin",
        },
        {
            "priority": "Medium",
            "decision": f"Protect momentum in the {growth_region} region",
            "evidence": f"Net revenue grew {growth_rate:.1%} in the latest quarter versus the prior quarter, the strongest regional trend.",
            "action": "Validate whether growth is repeatable by channel and category, then localize inventory and campaigns around the winning mix.",
            "owner": "Commercial Analytics",
            "expected_impact": "Sustained regional growth with inventory support",
        },
    ]


def _write_recommendations(recommendations: list[dict[str, str]], cfg: dict) -> None:
    lines = [
        "# Business Recommendations",
        "",
        f"**Company:** {cfg['company_name']}  ",
        f"**Analysis window:** {cfg['start_date']} to {cfg['end_date']}  ",
        f"**Snapshot date:** {cfg['snapshot_date']}  ",
        "",
        "Recommendations are decision hypotheses derived from the synthetic portfolio dataset. Each should be validated with a controlled test before broad rollout.",
        "",
    ]
    for i, rec in enumerate(recommendations, start=1):
        lines.extend(
            [
                f"## {i}. {rec['decision']}",
                "",
                f"- **Priority:** {rec['priority']}",
                f"- **Evidence:** {rec['evidence']}",
                f"- **Recommended action:** {rec['action']}",
                f"- **Owner:** {rec['owner']}",
                f"- **Expected impact:** {rec['expected_impact']}",
                "",
            ]
        )
    (REPORT_DIR / "business_recommendations.md").write_text("\n".join(lines), encoding="utf-8")


def _plot_dashboard(outputs: dict[str, pd.DataFrame], kpis: dict) -> None:
    navy, teal, cyan, orange, red = "#0B1F33", "#0F766E", "#0891B2", "#F59E0B", "#DC2626"
    background, panel, muted, border = "#F5F7FA", "#FFFFFF", "#52606D", "#D9E2EC"
    image = Image.new("RGB", (1600, 1000), background)
    draw = ImageDraw.Draw(image)

    def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        names = ["arialbd.ttf" if bold else "arial.ttf", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
        for name in names:
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                continue
        return ImageFont.load_default()

    def panel_box(box: tuple[int, int, int, int]) -> None:
        draw.rounded_rectangle(box, radius=14, fill=panel, outline=border, width=2)

    def bar_chart(
        box: tuple[int, int, int, int],
        labels: list[str],
        values: list[float],
        title: str,
        colors: list[str],
        money: bool = False,
    ) -> None:
        panel_box(box)
        x0, y0, x1, y1 = box
        draw.text((x0 + 22, y0 + 18), title, font=font(20, True), fill=navy)
        chart_left = x0 + 165
        chart_right = x1 - 25
        row_height = (y1 - y0 - 78) / max(len(labels), 1)
        max_value = max(values) if values else 1
        for i, (label, value, color) in enumerate(zip(labels, values, colors)):
            cy = y0 + 60 + i * row_height
            draw.text((x0 + 22, cy + 5), label[:22], font=font(14), fill=muted)
            width = int((chart_right - chart_left) * value / max_value)
            draw.rounded_rectangle(
                (chart_left, int(cy), chart_left + max(width, 3), int(cy + row_height * 0.58)),
                radius=5,
                fill=color,
            )
            value_label = (
                f"EUR {value / 1000:.0f}K"
                if money and value >= 1000
                else f"EUR {value:.0f}"
                if money
                else f"{value / 1000:.1f}K"
            )
            draw.text((chart_left + max(width, 3) + 8, cy + 3), value_label, font=font(12), fill=muted)

    draw.text((55, 38), "Nordstern Commerce | Executive Analytics Dashboard", font=font(30, True), fill=navy)
    draw.text((55, 82), "2024-2025 synthetic portfolio data | EUR | Snapshot 2026-01-01", font=font(16), fill=muted)

    cards = [
        ("NET REVENUE", f"EUR {kpis['net_revenue'] / 1_000:.0f}K", teal),
        ("COMPLETED ORDERS", f"{kpis['completed_orders']:,}", navy),
        ("AOV", f"EUR {kpis['aov']:.0f}", cyan),
        ("CONVERSION", f"{kpis['conversion_rate']:.1%}", orange),
        ("REPEAT PURCHASE", f"{kpis['repeat_purchase_rate']:.1%}", teal),
        ("90-DAY CHURN", f"{kpis['churn_rate_90d']:.1%}", red),
    ]
    card_width, gap = 235, 18
    for i, (label, value, color) in enumerate(cards):
        x = 55 + i * (card_width + gap)
        panel_box((x, 125, x + card_width, 245))
        draw.text((x + 18, 146), label, font=font(13, True), fill=muted)
        draw.text((x + 18, 184), value, font=font(26, True), fill=color)

    monthly = outputs["monthly_kpis"].copy()
    line_box = (55, 275, 965, 590)
    panel_box(line_box)
    draw.text((78, 294), "Monthly net revenue", font=font(20, True), fill=navy)
    px0, py0, px1, py1 = 92, 350, 936, 550
    monthly_values = monthly["net_revenue"].astype(float).tolist()
    vmin, vmax = min(monthly_values) * 0.92, max(monthly_values) * 1.05
    points = []
    for i, value in enumerate(monthly_values):
        x = px0 + i * (px1 - px0) / max(len(monthly_values) - 1, 1)
        y = py1 - (value - vmin) / max(vmax - vmin, 1) * (py1 - py0)
        points.append((int(x), int(y)))
    for level in range(4):
        y = int(py0 + level * (py1 - py0) / 3)
        draw.line((px0, y, px1, y), fill="#E8EEF3", width=1)
    draw.line(points, fill=teal, width=5, joint="curve")
    for i, point in enumerate(points):
        if i % 3 == 0 or i == len(points) - 1:
            draw.ellipse((point[0] - 5, point[1] - 5, point[0] + 5, point[1] + 5), fill=panel, outline=teal, width=3)
            draw.text((point[0] - 18, 558), monthly.iloc[i]["month"], font=font(10), fill=muted)

    channel = outputs["channel_90d_value"].sort_values("revenue_90d_per_acquired_customer", ascending=False)
    bar_chart(
        (990, 275, 1545, 590),
        channel["acquisition_channel"].tolist(),
        channel["revenue_90d_per_acquired_customer"].astype(float).tolist(),
        "90-day revenue / acquired customer",
        [teal] + [cyan] * (len(channel) - 1),
        money=True,
    )

    funnel = outputs["funnel_by_channel"]
    funnel_labels = ["Sessions", "Product views", "Add to carts", "Checkouts", "Orders"]
    funnel_values = [
        float(funnel["sessions"].sum()),
        float(funnel["product_views"].sum()),
        float(funnel["add_to_carts"].sum()),
        float(funnel["checkouts"].sum()),
        float(funnel["conversions"].sum()),
    ]
    bar_chart(
        (55, 620, 765, 950),
        funnel_labels,
        funnel_values,
        "Commerce funnel",
        [teal, "#149B91", cyan, "#58B7CC", "#A7D8E4"],
    )

    segments = outputs["segment_summary"].sort_values("net_revenue", ascending=False).head(6)
    segment_colors = [red if s == "At Risk" else teal if s == "Champions" else cyan for s in segments["rfm_segment"]]
    bar_chart(
        (790, 620, 1545, 950),
        segments["rfm_segment"].tolist(),
        segments["net_revenue"].astype(float).tolist(),
        "Revenue by customer segment",
        segment_colors,
        money=True,
    )

    image.save(FIGURE_DIR / "executive_dashboard.png", format="PNG", optimize=True)


def _write_excel_payload(outputs: dict[str, pd.DataFrame], kpis: dict, recommendations: list[dict[str, str]], cfg: dict) -> None:
    def clean_records(frame: pd.DataFrame) -> list[dict]:
        return json.loads(frame.replace({np.nan: None}).to_json(orient="records"))

    payload = {
        "metadata": {
            "company": cfg["company_name"],
            "analysis_period": f"{cfg['start_date']} to {cfg['end_date']}",
            "snapshot_date": cfg["snapshot_date"],
            "currency": cfg["currency"],
            "dataset_note": "Synthetic, reproducible portfolio dataset (seed 42)",
        },
        "kpis": kpis,
        "monthly": clean_records(outputs["monthly_kpis"]),
        "funnel": clean_records(outputs["funnel_by_channel"]),
        "channel_value": clean_records(outputs["channel_90d_value"]),
        "segments": clean_records(outputs["segment_summary"]),
        "cohorts": clean_records(outputs["cohort_retention"]),
        "products": clean_records(outputs["product_performance"].head(20)),
        "categories": clean_records(outputs["category_summary"]),
        "regions": clean_records(outputs["regional_performance"]),
        "recommendations": recommendations,
    }
    (ARTIFACT_DIR / "excel_payload.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_pipeline(force_generate: bool = False) -> None:
    ensure_project_dirs()
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    required_raw = [RAW_DIR / f"{name}.csv" for name in ("customers", "products", "sessions", "orders", "order_items")]
    if force_generate or not all(path.exists() for path in required_raw):
        generate(CONFIG_PATH)

    frames = _load_raw()
    quality = validate_data(**frames)
    quality.to_csv(REPORT_DIR / "data_quality_report.csv", index=False)
    database_path = _create_warehouse(frames)
    outputs = _derive_outputs(database_path, cfg)
    for name, frame in outputs.items():
        frame.to_csv(PROCESSED_DIR / f"{name}.csv", index=False)

    kpis = _overall_kpis(frames, outputs)
    (REPORT_DIR / "kpi_summary.json").write_text(json.dumps(kpis, indent=2), encoding="utf-8")
    recommendations = _build_recommendations(frames, outputs, kpis)
    _write_recommendations(recommendations, cfg)
    _plot_dashboard(outputs, kpis)
    _write_excel_payload(outputs, kpis, recommendations, cfg)

    summary = {
        "database": str(database_path.relative_to(PROJECT_ROOT)),
        "quality_checks_passed": f"{quality['passed'].sum()}/{len(quality)}",
        "kpis": kpis,
        "processed_outputs": sorted(path.name for path in PROCESSED_DIR.glob("*.csv")),
    }
    print(json.dumps(summary, indent=2))
