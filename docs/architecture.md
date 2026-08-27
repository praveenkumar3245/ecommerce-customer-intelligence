# Solution Architecture

```mermaid
flowchart LR
    A[Reproducible Python generator] --> B[Raw CSV layer]
    B --> C[Python quality controls]
    C --> D[(SQLite analytical warehouse)]
    D --> E[SQL KPI and customer queries]
    E --> F[Pandas analysis layer]
    F --> G[Processed CSV marts]
    F --> H[Business recommendations]
    G --> I[Excel dashboard]
    G --> J[Power BI build package]
    G --> K[Streamlit dashboard]
    C --> L[CI test suite]
```

## Design choices

- **Raw → warehouse → marts:** preserves source data, keeps transformations auditable, and mirrors a practical analytics workflow.
- **SQLite:** makes the project runnable without infrastructure while demonstrating portable SQL patterns: CTEs, window functions, conditional aggregation, date arithmetic, and views.
- **Processed marts:** give Excel, Power BI, and Streamlit consistent metric inputs.
- **Metric contract:** definitions are centralized in `docs/metric_definitions.md` and mirrored in SQL/DAX.
- **Reproducibility:** seed 42 plus automated tests produces deterministic results on every run.

