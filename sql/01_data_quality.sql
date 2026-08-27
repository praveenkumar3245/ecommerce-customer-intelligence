-- A compact SQL audit that can be run independently after loading the CSVs.
SELECT 'orphan_order_customers' AS check_name, COUNT(*) AS failures
FROM orders o
LEFT JOIN customers c ON c.customer_id = o.customer_id
WHERE o.customer_id IS NOT NULL AND c.customer_id IS NULL

UNION ALL

SELECT 'orphan_order_items', COUNT(*)
FROM order_items oi
LEFT JOIN orders o ON o.order_id = oi.order_id
WHERE o.order_id IS NULL

UNION ALL

SELECT 'invalid_funnel_sequence', COUNT(*)
FROM sessions
WHERE added_to_cart > viewed_product
   OR checkout_started > added_to_cart
   OR converted > checkout_started

UNION ALL

SELECT 'net_revenue_mismatch', COUNT(*)
FROM orders
WHERE ABS(net_revenue - (gross_revenue - discount_amount + shipping_revenue - refund_amount)) > 0.01;

