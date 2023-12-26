import collections.abc
import logging
from datetime import datetime
from typing import Union, Sequence

from alembic.autogenerate import comparators
from alembic.autogenerate.api import AutogenContext

from dddl.src.comparator import CustomDDLComparator
from dddl.src.config import load_config
from dddl.src.models import DDL
from dddl.src.ops import SyncDDLOp

logger = logging.getLogger(__name__)


class DDLRegistry:
    def __init__(self) -> None:
        self.ddls = []

    def register(self, dddl: Union[DDL, Sequence[DDL]]) -> None:
        if isinstance(dddl, collections.abc.Sequence):
            self.ddls.extend(dddl)
        else:
            self.ddls.append(dddl)


ddl_registry = DDLRegistry()


def register_ddl(dddl: Union[DDL, Sequence[DDL]]) -> None:
    ddl_registry.register(dddl)


@comparators.dispatch_for("schema")
def compare_custom_ddl(autogen_context: AutogenContext, upgrade_ops, _) -> None:
    config = load_config(autogen_context.opts["template_args"]["config"])
    logger.info(f"Loaded scripts location from config: {config.scripts_location}")

    comparator = CustomDDLComparator(
        ddl_dir=config.scripts_location,
        dddls=ddl_registry.ddls,
    )

    revisions = list(autogen_context.opts["script"].walk_revisions())
    heads = autogen_context.opts["script"].get_heads()
    cur_head = autogen_context.opts["revision_context"].generated_revisions[0].head
    changed = comparator.get_changed_ddl(
        revisions=revisions, heads=heads, cur_head=cur_head
    )

    time = datetime.now()
    for dddl, rev_script in changed:
        if rev_script:
            logger.info(f'Detected change in DDL "{dddl.name}"')
            down_script = rev_script
        else:
            logger.info(f'Detected new DDL "{dddl.name}"')
            down_script = dddl.down_sql
        upgrade_ops.ops.append(
            SyncDDLOp(up_script=dddl, down_script=down_script, time=time)
        )
