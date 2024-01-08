# Alembic Dumb DDL

A plugin for [Alembic](https://alembic.sqlalchemy.org/en/latest/) DB migration tool which add support for arbitrary DDL scripts in autogenerate command.

## Why is it dumb?

Because it doesn't try to be smart. It's really hard to compare arbitrary DDL scripts in the database with their sources in the project folder, because the scripts can contain multiple DDL statements, they may use version-specific features of a DBMS and they can be written for different DBMSs.

**Alembic Dumb DDL doesn't check the state of the objects in the database, it only checks if the source code of the script has changed, comparing to the previous revision.** And that's why Alembic Dumb DDL supports all databases and any kind of DDL scripts.

## Quick start

Step 1: save your DDL script in a file, and make sure that it overwrites the entities, instead of just creating them (e.g. starts with `DROP ... IF EXISTS` or similar construct for your DBMS).

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
    # DDL script SQL code, will be used in upgrade command
    sql=load_sql("last_month_orders.sql"),
    # Cleanup SQL code, will be used in the first downgrade command
    down_sql="DROP VIEW IF EXISTS last_month_orders;",
)
```

Step 3: Register your ddl in alembic's `env.py`:

```python
# migrations/env.py

from myapp.models import my_ddl
from alembic_dddl import register_ddl

register_ddl(my_ddl)

# ...
# the rest of the env.py file
```

That's it, from now on the alembic autogenerate command will keep track of `last_month_orders.sql`, and if it changes — automatically add update code to your migration scripts to update your entities.

The first run of the autogenerate command:

```shell
$ alembic revision --autogenerate -m "last_month_orders"
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic_dddl.dddl] Loaded scripts location from config: migrations/versions/ddl
INFO  [alembic_dddl.dddl] Detected new DDL "last_month_orders"
  Generating /Users/user/Projects/Python/alembic_custom_ddl/example/migrations/versions/2024_01_08_0955-0c897e9399a9_last_month_orders.py ...  done
```

For more detailed example see [Example Project](https://github.com/Vanderhoof/alembic-dddl/tree/master/example/).

## Installation

You can install Alembic Dumb DDL from pip:

```shell
pip install alembic_dddl
```

## How does it work

Take a look at [the example project](https://github.com/Vanderhoof/alembic-dddl/tree/master/example/).

Alembic Dumb DDL stores revisions of your DDL scripts in a folder inside `versions` directory (by default the folder is called `versions/ddl`). When you run `alembic revision --autogenerate` command Alembic Dumb DDL checks if any new DDL scripts were added, or if any of the existing ones are changed. For each such changed script its copy will be saved in the `versions/ddl` folder. This is the state against which the new changes in DDL scripts will be detected.

Along with creating the revisioned copy of the changed or added DDL scripts, Alembic Dumb DDL will also add upgrade and downgrade commands into the migration script itself.

**The upgrade command** will look like this:

```python
def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.run_ddl_script('2024_01_08_1045_order_details_060d60b5c278.sql')
```

`run_ddl_script` is an operation added to alembic by Alembic Dumb DDL. All it does is executes each statement in the script against the database.

There are two variations of **the downgrade command**.

For the new DDL scripts (without existing revisions) it will be copied from the `DDL.down_sql`, as you defined it:

```python
def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('DROP VIEW IF EXISTS order_details;')
```

If DDL script already existed and was changed in this revision, the downgrade command will look similar to the upgrade command, but for previous version of the script:

```python
def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.run_ddl_script('2024_01_08_1016_order_details_af80846764cd.sql')
```

> Because each DDL script is used for both upgrade and downgrade commands, it's important that the script is *overwriting* entities, not just creating them. i.e. it should start with `DROP ... IF EXISTS` or similar construct for your DBMS.

## Configuration

Alembic Dumb DDL has several configuration options. To set them, add `[alembic_dddl]` section to `alembic.ini`.

Here are the options and their default values:

```ini
[alembic_dddl]
# where the revisioned copies of DDL scripts will be stored
scripts_location = migrations/versions/ddl
# use timestamps instead of datetime in revisioned scripts file format
use_timestamps = False
# whether the comments should be ignored when comparing DDL scripts
ignore_comments = False
```

## Setting up Logging

Alembic Dumb DDL shows some useful log messages when the autogenerate command is running. To enable logging, add the following to your `alembic.ini`:

```ini
[loggers]
# add alembic_dddl to the `keys` option:
keys = root,sqlalchemy,alembic,alembic_dddl

# add the `logger_alembic` section:
[logger_alembic]
level = INFO
handlers =
qualname = alembic
```
