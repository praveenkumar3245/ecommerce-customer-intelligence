WITH first_orders AS (
    SELECT
        customer_id,
        MIN(order_date) AS first_order_date,
        SUBSTR(MIN(order_date), 1, 7) AS cohort_month
    FROM completed_orders
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),
activity AS (
    SELECT DISTINCT
        o.customer_id,
        f.cohort_month,
        SUBSTR(o.order_date, 1, 7) AS activity_month,
        (
            (CAST(STRFTIME('%Y', o.order_date) AS INTEGER) - CAST(SUBSTR(f.cohort_month, 1, 4) AS INTEGER)) * 12
            + CAST(STRFTIME('%m', o.order_date) AS INTEGER) - CAST(SUBSTR(f.cohort_month, 6, 2) AS INTEGER)
        ) AS months_since_first_order
    FROM completed_orders o
    JOIN first_orders f ON f.customer_id = o.customer_id
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM first_orders
    GROUP BY cohort_month
)
SELECT
    a.cohort_month,
    a.months_since_first_order,
    c.cohort_size,
    COUNT(DISTINCT a.customer_id) AS retained_customers,
    ROUND(1.0 * COUNT(DISTINCT a.customer_id) / c.cohort_size, 4) AS retention_rate
FROM activity a
JOIN cohort_sizes c USING (cohort_month)
WHERE a.months_since_first_order BETWEEN 0 AND 12
GROUP BY a.cohort_month, a.months_since_first_order, c.cohort_size
ORDER BY a.cohort_month, a.months_since_first_order;

