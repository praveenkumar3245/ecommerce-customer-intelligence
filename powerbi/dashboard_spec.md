# Interactive Dashboard Specification

Canvas: 16:9. Use the supplied theme. Every page receives Date, Channel, Region, and Device slicers; enable cross-highlighting and a Reset Filters bookmark.

## Page 1 — Executive Overview

- KPI cards: Net Revenue, Completed Orders, AOV, Conversion Rate, Gross Margin %, Revenue MoM %.
- Line chart: Month vs Net Revenue with Revenue YoY % in the tooltip.
- Funnel: Sessions → Product Views → Add To Carts → Checkout Starts → Conversions.
- Horizontal bar: 90-day revenue per acquired customer from `channel_90d_value.csv`.
- Smart narrative/text box: paste the three current high-priority recommendations from `reports/business_recommendations.md`.

## Page 2 — Customer Intelligence

- RFM segment bar: Net Revenue by segment, colored by churn rate.
- Scatter: Frequency vs Monetary Value, size by customer AOV, legend by RFM segment.
- Cohort heatmap: Cohort Month × Months Since First Order, value Retention Rate.
- Decomposition tree: Net Revenue → Acquisition Channel → Region → RFM Segment.
- Drill-through table for at-risk customer IDs, last order date, recency, frequency, and value.

## Page 3 — Product & Region

- Ranked bar: Net Revenue by Product; tooltip adds Units Sold, Gross Margin %, Return Rate.
- Matrix: Category → Subcategory with Net Revenue, Gross Profit, Gross Margin %, Return Rate.
- Bubble chart: Region (details), AOV (x), Net Revenue (y), Orders (size), Gross Margin % (color).
- Drill-through product page for monthly revenue, units, and returns.

## Page 4 — Channel & Funnel

- Channel comparison matrix with Sessions, Conversion Rate, AOV, Net Revenue, 90-day Revenue / Acquired Customer.
- Small multiples: monthly conversion trend by channel.
- Funnel-stage conversion bars by channel.
- Campaign table with conditional formatting on Conversion Rate and Net Revenue.

## Interaction acceptance criteria

- All slicers filter visuals on the page.
- Channel selection cross-highlights the funnel and revenue trend.
- Tooltip pages explain metric definitions.
- At-risk and product drill-through pages preserve filter context.
- Reset bookmark clears slicers.
- Numeric formats use EUR, whole counts, and one decimal for percentages.

