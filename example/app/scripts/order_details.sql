DROP VIEW IF EXISTS order_details;

CREATE VIEW order_details AS
SELECT 
    o.order_id,
    c.customer_name,
    ci.customer_phone,
    GROUP_CONCAT(p.product_name) AS product_names,
    SUM(po.price) AS order_sum
FROM
    orders o
JOIN
    customers c ON o.customer_id = c.customer_id
JOIN
    customer_info ci on c.customer_info_id = ci.customer_info_id
JOIN
    products_orders po ON o.order_id = po.order_id
JOIN
    products p ON po.product_id = p.product_id
GROUP BY
    o.order_id;
