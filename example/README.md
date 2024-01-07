# Example project

In this example project we have an SQLite database with the tables defined in [app/models.py](https://github.com/Vanderhoof/alembic-dddl/blob/master/example/app/models.py) and DDL scripts defined in [app/ddl.py](https://github.com/Vanderhoof/alembic-dddl/blob/master/example/app/ddl.py).

We then registered these DDL scripts in [migrations/env.py](https://github.com/Vanderhoof/alembic-dddl/blob/master/example/migrations/env.py). Every migration script in [migrations/versions](https://github.com/Vanderhoof/alembic-dddl/tree/master/example/migrations/versions) is created using `alembic revision --autogenerate` command.
