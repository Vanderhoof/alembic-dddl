from pathlib import Path

from alembic_dddl import DDL

SCRIPTS = Path(__file__).parent / "scripts"


def load_sql(filename: str) -> str:
    return (SCRIPTS / filename).read_text()


scripts = [
    DDL(
        name="last_month_orders",
        sql=load_sql("last_month_orders.sql"),
        down_sql="DROP VIEW IF EXISTS last_month_orders;",
    ),
    DDL(
        name="order_details",
        sql=load_sql("order_details.sql"),
        down_sql="DROP VIEW IF EXISTS order_details;",
    ),
    DDL(
        name="best_customer",
        sql=load_sql("best_customer.sql"),
        down_sql="DROP VIEW IF EXISTS best_customer;",
    ),
    DDL(
        name="customer_details",
        sql=load_sql("customer_details.sql"),
        down_sql="DROP VIEW IF EXISTS customer_details;",
    ),
]
