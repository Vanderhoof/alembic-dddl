import logging
import os
from datetime import datetime
from typing import Union

import sqlparse
from alembic.autogenerate import renderers
from alembic.operations import MigrateOperation, Operations

from alembic_dddl.src.config import load_config
from alembic_dddl.src.models import RevisionedScript, DDL
from alembic_dddl.src.renderer import RevisionedScriptRenderer, DDLRenderer, SQLRenderer

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


def gen_revisioned_script_name(
    name: str, revision: str, time: datetime, use_timestamps: bool
) -> str:
    time_part = (
        f"{int(time.timestamp())}" if use_timestamps else time.strftime("%Y_%m_%d_%H%M")
    )
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
        renderer = RevisionedScriptRenderer(script=op.up_script)
    elif isinstance(op.up_script, DDL):
        config = load_config(autogen_context.opts["template_args"]["config"])
        revision = (
            autogen_context.opts["revision_context"].generated_revisions[0].rev_id
        )
        renderer = DDLRenderer(
            ddl=op.up_script, config=config, revision_id=revision, time=op.time
        )
    elif isinstance(op.up_script, str):
        renderer = SQLRenderer(sql=op.up_script)
    else:
        raise ValueError(f"Unsupported up_script: {op.up_script!r}")
    return renderer.render()
