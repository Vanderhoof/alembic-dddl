import logging
import os
from datetime import datetime
from typing import Union

import sqlparse
from alembic.autogenerate import renderers
from alembic.operations import MigrateOperation, Operations

from dddl.src.config import load_config
from dddl.src.models import RevisionedScript, DDL

logger = logging.getLogger(f"alembic.{__name__}")


@Operations.register_operation("run_ddl_script")
class RunDDLScriptOp(MigrateOperation):
    def __init__(self, script_name: str):
        self.script_name = script_name

    def __repr__(self) -> str:
        return f"CreateCustomDDL({self.script_name!r})"

    @classmethod
    def run_ddl_script(cls, operations, script_name, **kw):
        op = RunDDLScriptOp(script_name=script_name, **kw)
        return operations.invoke(op)


Script = Union[DDL, RevisionedScript, str]


class SyncDDLOp(MigrateOperation):
    def __init__(self, up_script: Script, down_script: Script, time: datetime):
        self.time = time
        self.up_script = up_script
        self.down_script = down_script

    def reverse(self):
        return SyncDDLOp(
            up_script=self.down_script, down_script=self.up_script, time=self.time
        )


def ensure_dir(dir: str) -> None:
    if not os.path.isdir(dir):
        os.mkdir(dir)


def gen_revisioned_script_name(
    name: str, revision: str, time: datetime, use_timestamps: bool
) -> str:
    time_part = f"{int(time.timestamp())}" if use_timestamps else time.strftime('%Y_%m_%d_%H%M')
    return time_part + f"_{name}_{revision}.sql"


@Operations.implementation_for(RunDDLScriptOp)
def run_ddl_script(operations, operation) -> None:
    ddl_dir = os.path.join(operations.get_context().opts["script"].versions, "ddl")
    with open(os.path.join(ddl_dir, operation.script_name)) as f:
        source = f.read()

    for statement in sqlparse.split(source):
        operations.execute(statement)


@renderers.dispatch_for(SyncDDLOp)
def render_create_ddl(autogen_context, op: SyncDDLOp):
    if isinstance(op.up_script, RevisionedScript):
        return f"op.run_ddl_script('{op.up_script.script_name}')"
    elif isinstance(op.up_script, DDL):
        config = load_config(autogen_context.opts["template_args"]["config"])
        ensure_dir(config.scripts_location)
        revision = (
            autogen_context.opts["revision_context"].generated_revisions[0].rev_id
        )
        out_filename = gen_revisioned_script_name(
            op.up_script.name, revision, op.time, config.use_timestamps
        )
        out_path = os.path.join(config.scripts_location, out_filename)
        with open(out_path, "w") as f:
            f.write(op.up_script.sql)

        return f"op.run_ddl_script('{out_filename}')"
    elif isinstance(op.up_script, str):
        return "\n".join(f"op.execute('{s}')" for s in sqlparse.split(op.up_script))

    raise ValueError(f"Unsupported up_script: {op.up_script!r}")
