# Setting up Logging

Alembic Dumb DDL shows some useful log messages when the autogenerate command is running. To enable logging, update your `alembic.ini`:

```ini
[loggers]
# add alembic_dddl to the `keys` option:
keys = root,sqlalchemy,alembic,alembic_dddl

# add the `logger_alembic_dddl` section:
[logger_alembic_dddl]
level = INFO
handlers =
qualname = alembic_dddl
```
