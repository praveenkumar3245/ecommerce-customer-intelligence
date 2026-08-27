WITH monthly_sessions AS (
    SELECT
        SUBSTR(session_date, 1, 7) AS month,
        COUNT(*) AS sessions,
        SUM(converted) AS converted_sessions
    FROM sessions
    GROUP BY 1
),
monthly_orders AS (
    SELECT
        SUBSTR(order_date, 1, 7) AS month,
        COUNT(*) AS orders,
        SUM(CASE WHEN order_status = 'Completed' THEN 1 ELSE 0 END) AS completed_orders,
        SUM(gross_revenue) AS gross_revenue,
        SUM(discount_amount) AS discount_amount,
        SUM(refund_amount) AS refund_amount,
        SUM(net_revenue) AS net_revenue,
        SUM(gross_profit) AS gross_profit,
        COUNT(DISTINCT CASE WHEN order_status = 'Completed' THEN customer_id END) AS active_customers,
        SUM(CASE WHEN order_status = 'Returned' THEN 1 ELSE 0 END) AS returned_orders
    FROM orders
    GROUP BY 1
)
SELECT
    s.month,
    s.sessions,
    s.converted_sessions,
    COALESCE(o.orders, 0) AS orders,
    COALESCE(o.completed_orders, 0) AS completed_orders,
    ROUND(COALESCE(o.gross_revenue, 0), 2) AS gross_revenue,
    ROUND(COALESCE(o.discount_amount, 0), 2) AS discount_amount,
    ROUND(COALESCE(o.refund_amount, 0), 2) AS refund_amount,
    ROUND(COALESCE(o.net_revenue, 0), 2) AS net_revenue,
    ROUND(COALESCE(o.gross_profit, 0), 2) AS gross_profit,
    COALESCE(o.active_customers, 0) AS active_customers,
    COALESCE(o.returned_orders, 0) AS returned_orders,
    ROUND(1.0 * s.converted_sessions / NULLIF(s.sessions, 0), 4) AS conversion_rate,
    ROUND(1.0 * o.net_revenue / NULLIF(o.completed_orders, 0), 2) AS aov,
    ROUND(1.0 * o.gross_profit / NULLIF(o.net_revenue, 0), 4) AS gross_margin_rate,
    ROUND(1.0 * o.returned_orders / NULLIF(o.orders, 0), 4) AS return_rate
FROM monthly_sessions s
LEFT JOIN monthly_orders o USING (month)
ORDER BY s.month;

