# Power BI Build Guide

## Import layer

Load the five raw tables using `power_query_raw_tables.pq`. Also import these processed marts as ordinary CSV queries from `data/processed`:

- `customer_rfm.csv` → `Customer RFM`
- `cohort_retention.csv` → `Cohort Retention`
- `channel_90d_value.csv` → `Channel 90d Value`

The processed marts are deliberate: they expose SQL-derived customer scoring and cohort logic to Power BI while keeping the measures in `measures.dax` auditable against raw facts.

## Model layer

1. Rename query/table names to match `model_relationships.md`.
2. Create the Date calculated table shown at the bottom of `measures.dax`.
3. Mark it as a date table.
4. Create the relationships in `model_relationships.md`.
5. Add the measures to a dedicated `_Measures` table and organize display folders: Revenue, Funnel, Customer, Product.
6. Format currency measures as EUR, rates as one-decimal percentages, and counts as whole numbers.

## Report layer

Use `dashboard_spec.md`. Keep KPI definitions accessible through an info tooltip. Use synced slicers for Date, Channel, Region, and Device. Add a drill-through page for at-risk customers and another for product performance.

## Validation checklist

- Net Revenue equals `reports/kpi_summary.json`.
- Completed Orders, AOV, and Conversion Rate match the Excel dashboard.
- Session → View → Cart → Checkout → Order counts never increase between stages.
- No many-to-many relationships appear in the core star schema.
- Selecting a region filters orders and sessions consistently.
- The report contains no unsupported custom visuals.

Microsoft documents PBIP/PBIR as source-control-friendly project formats and TMDL as the semantic-model metadata format. Reference: https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview

