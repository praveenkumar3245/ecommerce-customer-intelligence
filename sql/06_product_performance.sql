SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.subcategory,
    SUM(op.quantity) AS units_sold,
    COUNT(DISTINCT op.order_id) AS orders,
    ROUND(SUM(op.allocated_net_revenue), 2) AS net_revenue,
    ROUND(SUM(op.allocated_gross_profit), 2) AS gross_profit,
    ROUND(1.0 * SUM(op.allocated_gross_profit) / NULLIF(SUM(op.allocated_net_revenue), 0), 4) AS gross_margin_rate,
    ROUND(AVG(p.unit_price), 2) AS list_price,
    ROUND(1.0 * SUM(CASE WHEN op.order_status = 'Returned' THEN op.quantity ELSE 0 END) / NULLIF(SUM(op.quantity), 0), 4) AS unit_return_rate
FROM products p
JOIN order_item_performance op ON op.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category, p.subcategory
ORDER BY net_revenue DESC;

