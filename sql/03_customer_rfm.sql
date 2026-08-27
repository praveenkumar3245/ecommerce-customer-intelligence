WITH customer_metrics AS (
    SELECT
        c.customer_id,
        c.acquisition_channel,
        c.region,
        CAST(julianday('2026-01-01') - julianday(MAX(o.order_date)) AS INTEGER) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        ROUND(SUM(o.net_revenue), 2) AS monetary_value,
        ROUND(AVG(o.net_revenue), 2) AS customer_aov,
        MIN(o.order_date) AS first_order_date,
        MAX(o.order_date) AS last_order_date
    FROM customers c
    JOIN completed_orders o ON o.customer_id = c.customer_id
    GROUP BY c.customer_id, c.acquisition_channel, c.region
),
scored AS (
    SELECT
        *,
        6 - NTILE(5) OVER (ORDER BY recency_days ASC) AS recency_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS frequency_score,
        NTILE(5) OVER (ORDER BY monetary_value ASC) AS monetary_score
    FROM customer_metrics
)
SELECT
    *,
    CASE
        WHEN recency_score >= 4 AND frequency_score >= 4 THEN 'Champions'
        WHEN recency_score <= 2 AND frequency_score >= 3 THEN 'At Risk'
        WHEN frequency_score >= 4 THEN 'Loyal Customers'
        WHEN recency_score >= 4 AND frequency_score BETWEEN 2 AND 3 THEN 'Potential Loyalists'
        WHEN recency_score = 5 AND frequency = 1 THEN 'New Customers'
        WHEN recency_score <= 2 AND frequency_score <= 2 THEN 'Hibernating'
        ELSE 'Need Attention'
    END AS rfm_segment,
    CASE WHEN recency_days > 90 THEN 1 ELSE 0 END AS churned_90d
FROM scored
ORDER BY monetary_value DESC;
