PRAGMA foreign_keys = ON;

CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_sessions_customer ON sessions(customer_id);
CREATE INDEX IF NOT EXISTS idx_sessions_channel ON sessions(channel);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_channel ON orders(channel);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);

DROP VIEW IF EXISTS completed_orders;
CREATE VIEW completed_orders AS
SELECT *
FROM orders
WHERE order_status = 'Completed';

DROP VIEW IF EXISTS order_item_performance;
CREATE VIEW order_item_performance AS
SELECT
    oi.order_item_id,
    oi.order_id,
    oi.product_id,
    o.order_date,
    o.channel,
    o.region,
    o.order_status,
    oi.quantity,
    oi.line_gross_revenue,
    oi.line_cost,
    CASE
        WHEN o.order_status = 'Completed'
        THEN ROUND(oi.line_gross_revenue * (1.0 - o.discount_amount / NULLIF(o.gross_revenue, 0)), 2)
        ELSE 0
    END AS allocated_net_revenue,
    CASE
        WHEN o.order_status = 'Completed'
        THEN ROUND(
            oi.line_gross_revenue * (1.0 - o.discount_amount / NULLIF(o.gross_revenue, 0)) - oi.line_cost,
            2
        )
        ELSE 0
    END AS allocated_gross_profit
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id;

