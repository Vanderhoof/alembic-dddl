import logging
import os
from datetime import datetime
from typing import Union

import sqlparse
from alembic.autogenerate import renderers
from alembic.operations import MigrateOperation, Operations

from alembic_dddl.src.config import load_config
from alembic_dddl.src.models import DDL, RevisionedScript
from alembic_dddl.src.renderer import (
    BaseRenderer,
    DDLRenderer,
    RevisionedScriptRenderer,
    SQLRenderer,
)

logger = logging.getLogger(f"alembic.{__name__}")


@Operations.register_operation("run_ddl_script")
class RunDDLScriptOp(MigrateOperation):
    def __init__(self, script_name: str):
        self.script_name = script_name

    @classmethod
    def run_ddl_script(cls, operations, script_name, **kw):
        op = RunDDLScriptOp(script_name=script_name, **kw)
        return operations.invoke(op)


Script = Union[DDL, RevisionedScript, str]


class SyncDDLOp(MigrateOperation):
    """
    Autogenerate operation which renders the code for updating/downgrading changed DDLs in the
    revision script. It's called by the main comparator.
    """

    def __init__(self, up_script: Script, down_script: Script, time: datetime):
        self.time = time
        self.up_script = up_script
        self.down_script = down_script

    def reverse(self) -> "SyncDDLOp":
        return SyncDDLOp(up_script=self.down_script, down_script=self.up_script, time=self.time)


@Operations.implementation_for(RunDDLScriptOp)
def run_ddl_script(operations: Operations, operation: RunDDLScriptOp) -> None:
    """
    Load the revisioned script source code by name and eexecute each statement from it against the
    database one by one.
    """

    config = load_config(operations.get_context().config)
    with open(os.path.join(config.scripts_location, operation.script_name)) as f:
        source = f.read()

    for statement in sqlparse.split(source):
        operations.execute(statement)


@renderers.dispatch_for(SyncDDLOp)
def render_create_ddl(autogen_context, op: SyncDDLOp):
    """
    Render the code of upgrade/downgrade operations for the migration script for the given `op`.
    """

    renderer: BaseRenderer

    if isinstance(op.up_script, RevisionedScript):
        renderer = RevisionedScriptRenderer(script=op.up_script)
    elif isinstance(op.up_script, DDL):
        config = load_config(autogen_context.opts["template_args"]["config"])
        revision = autogen_context.opts["revision_context"].generated_revisions[0].rev_id
        renderer = DDLRenderer(
            ddl=op.up_script,
            scripts_location=config.scripts_location,
            revision_id=revision,
            time=op.time,
            use_timestamps=config.use_timestamps,
        )
    elif isinstance(op.up_script, str):
        renderer = SQLRenderer(sql=op.up_script)
    else:
        raise ValueError(f"Unsupported up_script: {op.up_script!r}")
    return renderer.render()
