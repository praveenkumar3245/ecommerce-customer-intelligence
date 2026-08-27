SELECT
    region,
    COUNT(DISTINCT order_id) AS orders,
    COUNT(DISTINCT customer_id) AS customers,
    ROUND(SUM(net_revenue), 2) AS net_revenue,
    ROUND(AVG(CASE WHEN order_status = 'Completed' THEN net_revenue END), 2) AS aov,
    ROUND(SUM(gross_profit), 2) AS gross_profit,
    ROUND(1.0 * SUM(gross_profit) / NULLIF(SUM(net_revenue), 0), 4) AS gross_margin_rate,
    ROUND(1.0 * SUM(CASE WHEN order_status = 'Returned' THEN 1 ELSE 0 END) / COUNT(*), 4) AS return_rate
FROM orders
GROUP BY region
ORDER BY net_revenue DESC;

