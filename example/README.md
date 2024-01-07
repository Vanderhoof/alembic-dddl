# Example project

This is a fully working example project that features a sample SQLite database. The [tutorial](../docs/tutorial.md) describes the creation of the project step by step.

* The tables are defined in [app/models.py](https://github.com/Vanderhoof/alembic-dddl/blob/master/example/app/models.py) and the DDL scripts are defined in [app/ddl.py](https://github.com/Vanderhoof/alembic-dddl/blob/master/example/app/ddl.py).
* The DDL scripts are registered in [migrations/env.py](https://github.com/Vanderhoof/alembic-dddl/blob/master/example/migrations/env.py) using the `register_ddl` function.
* Every revision script in [migrations/versions](https://github.com/Vanderhoof/alembic-dddl/tree/master/example/migrations/versions) is created automatically using `alembic revision --autogenerate` command.
