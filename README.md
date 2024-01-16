# Alembic Dumb DDL

[![](https://img.shields.io/pypi/v/alembic-dddl.svg)](https://pypi.org/project/alembic-dddl/) [![](https://img.shields.io/github/v/tag/Vanderhoof/alembic-dddl.svg?label=GitHub)](https://github.com/Vanderhoof/alembic-dddl) ![tests](https://github.com/Vanderhoof/alembic-dddl/actions/workflows/tests.yml/badge.svg) [![codecov](https://codecov.io/gh/Vanderhoof/alembic-dddl/graph/badge.svg?token=BQJBA9PXPN)](https://codecov.io/gh/Vanderhoof/alembic-dddl)

A plugin for [Alembic](https://alembic.sqlalchemy.org/en/latest/) DB migration tool that adds support for arbitrary user-defined objects like views, functions, triggers, etc. in autogenerate command.

Alembic DDDL _does not_ compare the objects in the code with their state in the database. Instead, it **only tracks if the source code of the script has changed**, compared to the previous revision.

## Installation

You can install Alembic Dumb DDL from pip:

```shell
pip install alembic-dddl
```

## Quick start

Step 1: save your DDL script in a file, and make sure that it overwrites the entities, not just creates them (e.g. start with `DROP ... IF EXISTS` or a similar construct for your DBMS).

```sql
-- myapp/scripts/last_month_orders.sql

DROP VIEW IF EXISTS last_month_orders;

CREATE VIEW last_month_orders AS
    SELECT *
    FROM orders
    WHERE order_date > current_date - interval '30 days';
```

Step 2: Wrap your script in a `DDL` class:

```python
# myapp/models.py

from alembic_dddl import DDL
from pathlib import Path

SCRIPTS = Path(__file__).parent / "scripts"


def load_sql(filename: str) -> str:
    """Helper function to load the contents of a file from a `scripts` directory"""
    return (SCRIPTS / filename).read_text()


my_ddl = DDL(
    # will be used in revision filename
    name="last_month_orders",
    # DDL script SQL code, will be used in the upgrade command
    sql=load_sql("last_month_orders.sql"),
    # Cleanup SQL code, will be used in the first downgrade command
    down_sql="DROP VIEW IF EXISTS last_month_orders;",
)
```

Step 3: Register your script in alembic's `env.py`:

```python
# migrations/env.py

from myapp.models import my_ddl
from alembic_dddl import register_ddl

register_ddl(my_ddl)  # also supports a list

# ...
# the rest of the env.py file
```

From now on the alembic autogenerate command will keep track of `last_month_orders.sql`, and if it changes — automatically add update code to your migration scripts to update your entities.

Run the migration:

```shell
$ alembic revision --autogenerate -m "last_month_orders"
...
INFO  [alembic_dddl.dddl] Detected new DDL "last_month_orders"
  Generating myapp/migrations/versions/2024_01_08_0955-0c897e9399a9_last_month_orders.py ...  done
```

The generated revision script:

```python
# migrations/versions/2024_01_08_0955-0c897e9399a9_last_month_orders.py
...

def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.run_ddl_script("2024_01_08_0955_last_month_orders_0c897e9399a9.sql")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("DROP VIEW IF EXISTS last_month_orders;")
    # ### end Alembic commands ###

```

For more info see [tutorial](docs/tutorial.md) or take a look at the [Example Project](https://github.com/Vanderhoof/alembic-dddl/tree/master/example/).

## Why do it this way?

Managing your custom entities with Alembic DDDL has several benefits:

1. The DDL scripts are defined in one place in the source code, any change to them is reflected in git history through direct diffs.
2. Any kind of SQL script and any DBMS is supported because the plugin does not interact with the database.
3. The migrations for your DDL scripts are fully autogenerated, they are also clean and concise.

# Further reading

* [Tutorial](docs/tutorial.md)
* [How it Works](docs/how_it_works.md)
* [Configuration](docs/configuration.md)
* [Setting up Logging](docs/logging.md)
