DROP VIEW IF EXISTS best_customer;

CREATE VIEW best_customer AS
SELECT
    c.customer_name,
    COUNT(po.product_id) AS total_products_bought,
    SUM(po.price) AS total_money_spent
FROM
    customers c
JOIN
    orders o ON c.customer_id = o.customer_id
JOIN
    products_orders po ON o.order_id = po.order_id
GROUP BY
    c.customer_id
ORDER BY
    total_products_bought DESC, total_money_spent DESC
LIMIT 1;
