SELECT
    channel,
    COUNT(*) AS sessions,
    SUM(viewed_product) AS product_views,
    SUM(added_to_cart) AS add_to_carts,
    SUM(checkout_started) AS checkouts,
    SUM(converted) AS conversions,
    ROUND(1.0 * SUM(viewed_product) / COUNT(*), 4) AS session_to_view_rate,
    ROUND(1.0 * SUM(added_to_cart) / NULLIF(SUM(viewed_product), 0), 4) AS view_to_cart_rate,
    ROUND(1.0 * SUM(checkout_started) / NULLIF(SUM(added_to_cart), 0), 4) AS cart_to_checkout_rate,
    ROUND(1.0 * SUM(converted) / NULLIF(SUM(checkout_started), 0), 4) AS checkout_to_order_rate,
    ROUND(1.0 * SUM(converted) / COUNT(*), 4) AS overall_conversion_rate
FROM sessions
GROUP BY channel
ORDER BY overall_conversion_rate DESC;

