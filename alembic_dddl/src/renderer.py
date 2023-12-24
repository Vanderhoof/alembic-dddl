import os
from abc import ABC, abstractmethod
from datetime import datetime

import sqlparse

from alembic_dddl.src.file_format import DateTimeFileFormat, TimestampedFileFormat
from alembic_dddl.src.models import RevisionedScript, DDL
from alembic_dddl.src.config import DDDLConfig
from alembic_dddl.src.utils import ensure_dir


class BaseRenderer(ABC):
    @abstractmethod
    def render(self) -> str:
        ...


class RevisionedScriptRenderer(BaseRenderer):
    def __init__(self, script: RevisionedScript) -> None:
        self.script = script

    def render(self) -> str:
        return f"op.run_ddl_script('{self.script.script_name}')"


class SQLRenderer(BaseRenderer):
    def __init__(self, sql: str) -> None:
        self.sql = sql

    def render(self) -> str:
        statements = []
        for script in sqlparse.split(self.sql):
            quotes = "'''" if "\n" in script else "'"
            statements.append(f"op.execute({quotes}{script}{quotes})")
        return "\n".join(statements)


class DDLRenderer(BaseRenderer):
    def __init__(
        self, ddl: DDL, config: DDDLConfig, revision_id: str, time: datetime
    ) -> None:
        self.config = config
        self.ddl = ddl
        self.revision_id = revision_id
        self.time = time
        self.file_formatter = (
            TimestampedFileFormat if config.use_timestamps else DateTimeFileFormat
        )

    def render(self) -> str:
        ensure_dir(self.config.scripts_location)
        out_filename = self.file_formatter.generate_filename(
            name=self.ddl.name, revision=self.revision_id, time=self.time
        )
        out_path = os.path.join(self.config.scripts_location, out_filename)
        with open(out_path, "w") as f:
            f.write(self.ddl.sql)

        return f"op.run_ddl_script('{out_filename}')"
