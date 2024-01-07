# Configuration

Alembic DDDL has several configuration options. To set them, add `[alembic_dddl]` section to `alembic.ini`.

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
