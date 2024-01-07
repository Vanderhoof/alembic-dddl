DROP VIEW IF EXISTS order_details;

CREATE VIEW order_details AS
SELECT
    o.order_id,
    c.customer_name,
    c.customer_phone,
    p.product_name
FROM
    orders o
JOIN
    customers c ON o.customer_id = c.customer_id
JOIN
    products_orders po ON o.order_id = po.order_id
JOIN
    products p ON po.product_id = p.product_id;
