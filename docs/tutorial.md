# Tutorial

This tutorial describes the creation of an imaginary webshop database. For the sake of simplicity, we won't be implementing any of the application code but instead will focus on the database design and its changes through migrations.

The full source code of the app created in this tutorial is available in the [Example Project](https://github.com/Vanderhoof/alembic-dddl/tree/master/example/).

Table of Contents:

* [Preparation](#preparation)
  * [Defining the Tables](#defining-the-tables)
  * [Setting up Alembic](#seting-up-alembic)
  * [Running the first migration](#running-the-first-migration)
* [Creating some views](#creating-some-views)
* [Creading DDL objects](#creating-ddl-objects)
* [Generating the migration for the scripts](#generating-the-migration-for-the-scripts)
* [Changing the views](#changing-the-views)
* [Conclusion](#conclusion)


## Preparation

Start by creating a  virtual environment and installing the dependencies.

```shell
 $ virtualenv venv
 $ source venv/bin/activate
 (venv) $ pip3 install sqlalchemy alembic alembic-dddl
```

### Defining the Tables

Before writing any custom views, we need some tables that they could interact with.

Let's create a simplistic table structure for an imaginary webshop:

```python
# app/moddels.py

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, mapped_column


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"

    customer_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_name = mapped_column(String)
    customer_phone = mapped_column(String)


class Product(Base):
    __tablename__ = "products"

    product_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_name = mapped_column(String)


class Order(Base):
    __tablename__ = "orders"

    order_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_date = mapped_column(DateTime)
    customer_id = mapped_column(
        Integer,
        ForeignKey("customers.customer_id", ondelete="CASCADE"),
    )


class ProductOrder(Base):
    __tablename__ = "products_orders"

    product_order_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id = mapped_column(
        Integer,
        ForeignKey("orders.order_id", ondelete="CASCADE"),
    )
    product_id = mapped_column(
        Integer,
        ForeignKey("orders.order_id", ondelete="CASCADE"),
    )
```

### Seting up Alembic

Before we could migrations we first need to initialize the Alembic environment

```shell
(venv) $ alembic init migrations
```

Set the database connection string in `alembic.ini`. We will be using SQLite for this example:

```ini
# alembic.ini

sqlalchemy.url = sqlite:///example.db
```

Let's also [set up Alembic DDDL logger](logging.md) while we're at it:

```ini
# alembic.ini

[loggers]
# add alembic_dddl to the `keys` option:
keys = root,sqlalchemy,alembic,alembic_dddl

# add the `logger_alembic_dddl` section:
[logger_alembic_dddl]
level = INFO
handlers =
qualname = alembic_dddl
```

Define the metadata in `env.py`

```python
# migrations/env.py
from app.models import Base

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata
```

### Running the first migration

With the Alembic environment set up, we can create and apply the first migration.

```shell
(venv) $ alembic revision --autogenerate -m initial

INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added table 'customers'
INFO  [alembic.autogenerate.compare] Detected added table 'products'
INFO  [alembic.autogenerate.compare] Detected added table 'orders'
INFO  [alembic.autogenerate.compare] Detected added table 'products_orders'
  Generating /shop/migrations/versions/ff6eabe64148_initial.py ...  done
```

```shell
(venv) alembic upgrade head

INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> ff6eabe64148, initial
```

The database is created and ready for our DDL experiments.

## Creating some views

SQLite doesn't support user-defined functions and stored procedures, but with the current table structure, we still can have some fun creating a few views.

For example these three:

**best_customer**: show the customer who ordered the most products

```sql
-- app/scripts/best_customer.sql

DROP VIEW IF EXISTS best_customer;

CREATE VIEW best_customer AS
SELECT
    c.customer_name,
    COUNT(po.product_id) AS total_products_bought
FROM
    customers c
JOIN
    orders o ON c.customer_id = o.customer_id
JOIN
    products_orders po ON o.order_id = po.order_id
GROUP BY
    c.customer_id
ORDER BY
    total_products_bought DESC
LIMIT 1;
```

**last_month_orders**: show only the orders that were created in the latest 30 days

```sql
-- app/scripts/last_month_orders.sql

DROP VIEW IF EXISTS last_month_orders;

CREATE VIEW last_month_orders AS
    SELECT *
    FROM orders
    WHERE order_date > date('now', '-30 days');
```

**order_details**: show info on the product and the customer for each order

```sql
-- app/scripts/order_details.sql

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

```

Notice that we start each script with `DROP VIEW IF EXISTS`. This is important: these DDL scripts will be used for both upgrade and downgrade operations, so they should be idempotent (i.e. overwrite existing entities).

## Creating DDL objects

For Alembic DDDL to be able to work with our scripts, we need to present them as `DDL` objects.

DDL is a dataclass with three fields:

* **name** will be used in the logs and to generate the revisioned script filename.
* **sql** is the source code of your script. We will just load it from the `.sql` file.
* **down_sql** is the source code of the script that removes the entity. It will be used just once in the downgrade operation of first migration where the DDL will be introduced.

Let's create a `DDL` object for each of the three scripts and group them in a `scripts` list:

```python
# app/ddl.py

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
]
```

And the final step before we see the magic of Alembic DDDL in action. We need to register these DDL scripts in `env.py`:

```python
# migrations/env.py

from alembic_dddl import register_ddl
from app.ddl import scripts

register_ddl(scripts)
```

## Generating the migration for the scripts

Now everything is ready to create our first migration with the custom DDL scripts.

```shell
(venv) $ alembic revision --autogenerate -m views

INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic_dddl.dddl] Detected new DDL "last_month_orders"
INFO  [alembic_dddl.dddl] Detected new DDL "order_details"
INFO  [alembic_dddl.dddl] Detected new DDL "best_customer"
INFO  [alembic_dddl.src.utils] DDL dir does not exist, creating: migrations/versions/ddl
  Generating /shop/migrations/versions/18cdfbc6a8fe_views.py ...  done
```

We already see in the logs that Alembic has noticed our DDL scripts, let's now take a look at the created migration

```python
# migrations/versions/18cdfbc6a8fe_views.py
...

def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.run_ddl_script('2024_01_09_1544_last_month_orders_18cdfbc6a8fe.sql')
    op.run_ddl_script('2024_01_09_1544_order_details_18cdfbc6a8fe.sql')
    op.run_ddl_script('2024_01_09_1544_best_customer_18cdfbc6a8fe.sql')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('DROP VIEW IF EXISTS best_customer;')
    op.execute('DROP VIEW IF EXISTS order_details;')
    op.execute('DROP VIEW IF EXISTS last_month_orders;')
    # ### end Alembic commands ###

```

We see three `op.run_ddl_script` commands, which will execute the scripts against the database. These are custom operations, added to Alembic by Alembic DDDL plugin.

You can also see that the `migrations/versions/ddl` folder was created and is now containing three scripts, which currently are the exact copies of our DDL scripts defined in `app/scripts`. These will be used in the future to detect the changes in the DDL scripts.

Time to apply the revision:

```shell
(venv) $ alembic upgrade head

INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade ff6eabe64148 -> 18cdfbc6a8fe, views
```

You can now connect to the database and check that the views were indeed created.

## Changing the views

Let's now add some changes to our views to see how Alembic DDDL deals with them.

There's one improvement we can introduce right away: we forgot to add the information about the prices of the products. Let's add the `price` field to the `ProductOrder` table.

```diff
# app/models.py

class ProductOrder(Base):
    __tablename__ = "products_orders"

    product_order_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id = mapped_column(
        Integer,
        ForeignKey("orders.order_id", ondelete="CASCADE"),
    )
    product_id = mapped_column(
        Integer,
        ForeignKey("orders.order_id", ondelete="CASCADE"),
    )
+    price = mapped_column(Integer)
```

Now we need to update the `order_details` view to feature this new field. Let's also group the details by order and show the order sum.

```diff
# app/scripts/order_details.sql

DROP VIEW IF EXISTS order_details;

CREATE VIEW order_details AS
SELECT
    o.order_id,
    c.customer_name,
    c.customer_phone,
-    p.product_name
+    GROUP_CONCAT(p.product_name) AS product_names,
+    SUM(po.price) AS order_sum
FROM
    orders o
JOIN
    customers c ON o.customer_id = c.customer_id
JOIN
    products_orders po ON o.order_id = po.order_id
JOIN
    products p ON po.product_id = p.product_id
+GROUP BY
+    o.order_id;
```

We will also change the `best_customer` view to show the total amount they spent:

```diff
# app/scripts/best_customer.sql

DROP VIEW IF EXISTS best_customer;

CREATE VIEW best_customer AS
SELECT
    c.customer_name,
    COUNT(po.product_id) AS total_products_bought,
+    SUM(po.price) AS total_money_spent
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
```

We've changed the table structure and the two views, now let's see if Alembic will notice these changes.

```shell
(venv) $ alembic revision --autogenerate -m product_prices

INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added column 'products_orders.price'
INFO  [alembic_dddl.dddl] Detected change in DDL "order_details"
INFO  [alembic_dddl.dddl] Detected change in DDL "best_customer"
  Generating /shop/migrations/versions/e09ef406f546_product_prices.py ...  done
```

Logs suggest that it did! But what's in the revision script?

```python
# migrations/versions/e09ef406f546_product_prices.py

...

def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products_orders', sa.Column('price', sa.Integer(), nullable=True))
    op.run_ddl_script('2024_01_09_1608_order_details_e09ef406f546.sql')
    op.run_ddl_script('2024_01_09_1608_best_customer_e09ef406f546.sql')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.run_ddl_script('2024_01_09_1544_best_customer_18cdfbc6a8fe.sql')
    op.run_ddl_script('2024_01_09_1544_order_details_18cdfbc6a8fe.sql')
    op.drop_column('products_orders', 'price')
    # ### end Alembic commands ###
```

The upgrade section looks similar to the previous migration. But since both `best_customer` and `order_details` views did exist in the database, the downgrade section now runs the previous revisions of the DDL scripts, stored in `migrations/versions/ddl`, instead of calling `DROP VIEW` directly.

This allows us to seamlessly upgrade and downgrade the database:

```shell
(venv) $ alembic upgrade head
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 18cdfbc6a8fe -> e09ef406f546, product_prices
(venv) $ alembic downgrade -1
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running downgrade e09ef406f546 -> 18cdfbc6a8fe, product_prices
(venv) $ alembic upgrade head
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 18cdfbc6a8fe -> e09ef406f546, product_prices
```

## Conclusion

Now you know how to use Alembic DDDL to maintain your custom DDL scripts. We've practiced creating and changing the views in the database.

Explore the [Example Project](https://github.com/Vanderhoof/alembic-dddl/tree/master/example/), which shows the final state of the app that we've created today. It also contains a bonus migration, which features a mixed creation of a new DDL script and an update of the existing one.
