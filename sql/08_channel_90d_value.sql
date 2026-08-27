WITH matured_customers AS (
    SELECT *
    FROM customers
    WHERE signup_date <= DATE('2026-01-01', '-90 day')
),
customer_90d AS (
    SELECT
        c.customer_id,
        c.acquisition_channel,
        SUM(
            CASE
                WHEN o.order_status = 'Completed'
                 AND julianday(o.order_date) - julianday(c.signup_date) BETWEEN 0 AND 90
                THEN o.net_revenue ELSE 0
            END
        ) AS revenue_90d,
        COUNT(DISTINCT CASE
            WHEN o.order_status = 'Completed'
             AND julianday(o.order_date) - julianday(c.signup_date) BETWEEN 0 AND 90
            THEN o.order_id END
        ) AS orders_90d
    FROM matured_customers c
    LEFT JOIN orders o ON o.customer_id = c.customer_id
    GROUP BY c.customer_id, c.acquisition_channel
)
SELECT
    acquisition_channel,
    COUNT(*) AS acquired_customers,
    SUM(CASE WHEN orders_90d > 0 THEN 1 ELSE 0 END) AS purchasing_customers_90d,
    ROUND(SUM(revenue_90d), 2) AS revenue_90d,
    ROUND(AVG(revenue_90d), 2) AS revenue_90d_per_acquired_customer,
    ROUND(AVG(CASE WHEN orders_90d > 0 THEN revenue_90d END), 2) AS revenue_90d_per_purchaser,
    ROUND(1.0 * SUM(CASE WHEN orders_90d > 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS purchaser_rate_90d
FROM customer_90d
GROUP BY acquisition_channel
ORDER BY revenue_90d_per_acquired_customer DESC;

