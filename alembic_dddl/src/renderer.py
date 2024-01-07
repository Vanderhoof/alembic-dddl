import os
from abc import ABC, abstractmethod
from datetime import datetime

import sqlparse

from alembic_dddl.src.file_format import DateTimeFileFormat, TimestampedFileFormat
from alembic_dddl.src.models import RevisionedScript, DDL
from alembic_dddl.src.utils import ensure_dir, escape_quotes


class BaseRenderer(ABC):
    """Renderers generate code for alembic revision script"""

    @abstractmethod
    def render(self) -> str:
        '''Generate the code for the migration script'''


class RevisionedScriptRenderer(BaseRenderer):
    """Renderer for RevisionedScript. This will be used to generate downgrade commands."""

    def __init__(self, script: RevisionedScript) -> None:
        self.script = script

    def render(self) -> str:
        """Generate code to run the revisioned script"""
        script_name = os.path.split(self.script.filepath)[-1]
        return f"op.run_ddl_script('{script_name}')"


class SQLRenderer(BaseRenderer):
    """
    Renderer for raw SQL queries. This will be used to generate drop commands (downgrading first
    revision of the script)
    """

    def __init__(self, sql: str) -> None:
        self.sql = sql

    def render(self) -> str:
        """
        Generate code to run raw SQL script. Since op.execute only supports one statement,
        if the script contains multiple statements — it will be split into multiple op.execute
        operations.
        """

        statements = []
        for script in sqlparse.split(self.sql):
            if "\n" in script:
                quoted_script = f"'''{script}'''"
            else:
                quoted_script = f"'{escape_quotes(script)}'"
            statements.append(f"op.execute({quoted_script})")
        return "\n".join(statements)


class DDLRenderer(BaseRenderer):
    """
    Renderer for DDL objects. This will be used to generate upgrade commands. This renderer is
    also responsible for creating revisioned script files.
    """

    def __init__(
        self, ddl: DDL, scripts_location: str, revision_id: str, time: datetime, use_timestamps: bool
    ) -> None:
        self.scripts_location = scripts_location
        self.ddl = ddl
        self.revision_id = revision_id
        self.time = time
        self.file_formatter = (
            TimestampedFileFormat if use_timestamps else DateTimeFileFormat
        )

    def render(self) -> str:
        """
        Create a script file for this revision of DDL and save it in the scripts location. Return
        the `run_ddl_script` operation for the created script file.
        """

        ensure_dir(self.scripts_location)
        out_filename = self.file_formatter.generate_filename(
            name=self.ddl.name, revision=self.revision_id, time=self.time
        )
        out_path = os.path.join(self.scripts_location, out_filename)
        with open(out_path, "w") as f:
            f.write(self.ddl.sql)

        return f"op.run_ddl_script('{out_filename}')"
