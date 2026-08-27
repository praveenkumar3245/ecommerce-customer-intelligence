from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"

st.set_page_config(page_title="Nordstern Commerce Analytics", page_icon="📊", layout="wide")


@st.cache_data
def load_data() -> dict[str, pd.DataFrame]:
    return {
        "monthly": pd.read_csv(PROCESSED / "monthly_kpis.csv"),
        "funnel": pd.read_csv(PROCESSED / "funnel_by_channel.csv"),
        "segments": pd.read_csv(PROCESSED / "segment_summary.csv"),
        "products": pd.read_csv(PROCESSED / "product_performance.csv"),
        "regions": pd.read_csv(PROCESSED / "regional_performance.csv"),
        "channel_value": pd.read_csv(PROCESSED / "channel_90d_value.csv"),
        "cohorts": pd.read_csv(PROCESSED / "cohort_retention.csv"),
    }


data = load_data()
teal = "#0F766E"
cyan = "#0891B2"

st.title("Nordstern Commerce — E-Commerce Analytics")
st.caption("Interactive portfolio dashboard · synthetic 2024–2025 German e-commerce data · EUR")

monthly = data["monthly"]
selected_months = st.sidebar.slider("Months shown", 6, len(monthly), len(monthly))
selected_channels = st.sidebar.multiselect(
    "Channels", data["funnel"]["channel"].tolist(), default=data["funnel"]["channel"].tolist()
)
months = monthly.tail(selected_months)
funnel = data["funnel"].query("channel in @selected_channels")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Net revenue", f"€{monthly['net_revenue'].sum():,.0f}")
k2.metric("Completed orders", f"{monthly['completed_orders'].sum():,.0f}")
k3.metric("AOV", f"€{monthly['net_revenue'].sum() / monthly['completed_orders'].sum():,.2f}")
k4.metric("Conversion", f"{monthly['converted_sessions'].sum() / monthly['sessions'].sum():.1%}")
k5.metric("Gross margin", f"{monthly['gross_profit'].sum() / monthly['net_revenue'].sum():.1%}")

overview, customer, product = st.tabs(["Executive overview", "Customer intelligence", "Product & region"])

with overview:
    left, right = st.columns([1.45, 1])
    with left:
        revenue_fig = px.line(months, x="month", y="net_revenue", markers=True, title="Monthly net revenue")
        revenue_fig.update_traces(line_color=teal, line_width=3)
        revenue_fig.update_layout(yaxis_tickprefix="€", yaxis_tickformat=",.0f", xaxis_title="", yaxis_title="")
        st.plotly_chart(revenue_fig, width="stretch")
    with right:
        stages = ["Sessions", "Product views", "Add to carts", "Checkouts", "Orders"]
        values = [
            funnel["sessions"].sum(), funnel["product_views"].sum(), funnel["add_to_carts"].sum(),
            funnel["checkouts"].sum(), funnel["conversions"].sum(),
        ]
        funnel_fig = go.Figure(go.Funnel(y=stages, x=values, marker={"color": ["#A7D8E4", "#58B7CC", cyan, "#149B91", teal]}))
        funnel_fig.update_layout(title="Selected-channel funnel")
        st.plotly_chart(funnel_fig, width="stretch")

    value_fig = px.bar(
        data["channel_value"].sort_values("revenue_90d_per_acquired_customer"),
        x="revenue_90d_per_acquired_customer",
        y="acquisition_channel",
        orientation="h",
        title="90-day revenue per acquired customer",
        color_discrete_sequence=[cyan],
    )
    value_fig.update_layout(xaxis_tickprefix="€", xaxis_title="", yaxis_title="")
    st.plotly_chart(value_fig, width="stretch")

with customer:
    left, right = st.columns(2)
    with left:
        segment_fig = px.bar(
            data["segments"].sort_values("net_revenue"),
            x="net_revenue", y="rfm_segment", orientation="h", color="churn_rate",
            color_continuous_scale=["#0F766E", "#F59E0B", "#DC2626"], title="Customer segments: revenue and churn risk",
        )
        segment_fig.update_layout(xaxis_tickprefix="€", xaxis_title="", yaxis_title="")
        st.plotly_chart(segment_fig, width="stretch")
    with right:
        cohort = data["cohorts"].pivot(index="cohort_month", columns="months_since_first_order", values="retention_rate")
        heatmap = px.imshow(cohort, aspect="auto", color_continuous_scale="Teal", title="Cohort retention heatmap", labels={"color": "Retention"})
        heatmap.update_coloraxes(colorbar_tickformat=".0%")
        st.plotly_chart(heatmap, width="stretch")
    st.dataframe(data["segments"], width="stretch", hide_index=True)

with product:
    left, right = st.columns(2)
    with left:
        top_products = data["products"].nlargest(12, "net_revenue").sort_values("net_revenue")
        product_fig = px.bar(top_products, x="net_revenue", y="product_name", orientation="h", color="gross_margin_rate", title="Top products by net revenue")
        product_fig.update_layout(xaxis_tickprefix="€", xaxis_title="", yaxis_title="")
        st.plotly_chart(product_fig, width="stretch")
    with right:
        region_fig = px.scatter(
            data["regions"], x="aov", y="net_revenue", size="orders", color="gross_margin_rate", text="region",
            title="Regional performance", color_continuous_scale="Teal",
        )
        region_fig.update_traces(textposition="top center")
        region_fig.update_layout(xaxis_tickprefix="€", yaxis_tickprefix="€", xaxis_title="AOV", yaxis_title="Net revenue")
        st.plotly_chart(region_fig, width="stretch")

st.info("Portfolio dataset: synthetic and reproducible. See the repository README for metric definitions and business recommendations.")
