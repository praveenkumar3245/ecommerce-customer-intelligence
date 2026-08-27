# Power BI Build Package

This folder is the source-controlled handoff for the interactive Power BI report. It contains the data-model map, import queries, DAX measures, a theme, and a page-by-page visual specification. The binary `.pbix` format is intentionally not fabricated: Power BI Desktop must create that proprietary file after validating local data paths and the installed Desktop version.

## Fast build

1. Run `python scripts/run_pipeline.py --regenerate` from the repository root.
2. Open Power BI Desktop and create a blank report.
3. In Power Query, create a text parameter named `DataRoot` pointing to the absolute `data/raw` folder.
4. Use `power_query_raw_tables.pq` to import the five raw tables. Create a second parameter named `ProcessedRoot` for `data/processed` and import the curated marts listed in `BUILD_GUIDE.md`.
5. Create relationships using `model_relationships.md`.
6. Add the measures in `measures.dax`.
7. Import `nordstern_theme.json` through **View → Themes → Browse for themes**.
8. Build the four report pages from `dashboard_spec.md`, add the listed slicers, and save as `Ecommerce_Customer_Intelligence.pbix` or a source-control-friendly `.pbip` project.

The report design uses only native Power BI visuals, so no marketplace visual installation is required.

