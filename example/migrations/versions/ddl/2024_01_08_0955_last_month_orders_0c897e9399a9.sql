DROP VIEW IF EXISTS last_month_orders;

CREATE VIEW last_month_orders AS
    SELECT *
    FROM orders
    WHERE order_date > date('now', '-30 days');
