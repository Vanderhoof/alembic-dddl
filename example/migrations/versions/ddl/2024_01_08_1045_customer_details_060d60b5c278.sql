DROP VIEW IF EXISTS customer_details;


CREATE VIEW customer_details AS
SELECT
    c.customer_id,
    c.customer_name,
    ci.customer_address,
    ci.customer_phone,
    ci.customer_email
FROM
    customers c
JOIN
    customer_info ci ON c.customer_id = ci.customer_info_id;
