import collections.abc
import logging
from datetime import datetime
from typing import Union, Sequence

from alembic.autogenerate import comparators
from alembic.autogenerate.api import AutogenContext

from alembic_dddl.src.comparator import CustomDDLComparator
from alembic_dddl.src.config import load_config
from alembic_dddl.src.models import DDL
from alembic_dddl.src.ops import SyncDDLOp

logger = logging.getLogger(__name__)


class DDLRegistry:
    """The registry keeps track of all DDL scripts"""

    def __init__(self) -> None:
        self.ddls = []

    def register(self, dddl: Union[DDL, Sequence[DDL]]) -> None:
        """Add one or more DDLs to the registry."""
        if isinstance(dddl, collections.abc.Sequence):
            self.ddls.extend(dddl)
        else:
            self.ddls.append(dddl)


ddl_registry = DDLRegistry()


def register_ddl(dddl: Union[DDL, Sequence[DDL]]) -> None:
    """Register one or more DDLs in the global registry object."""
    ddl_registry.register(dddl)


@comparators.dispatch_for("schema")
def compare_custom_ddl(autogen_context: AutogenContext, upgrade_ops, _) -> None:
    """
    Autogenerate comparator, detects changes in registered DDL scripts and initiates sync
    operations for the changed ones.
    """

    config = load_config(autogen_context.opts["template_args"]["config"])
    logger.info(f"Loaded scripts location from config: {config.scripts_location}")

    comparator = CustomDDLComparator(
        ddl_dir=config.scripts_location,
        ddls=ddl_registry.ddls,
        autogen_context=autogen_context,
        ignore_comments=config.ignore_comments,
    )

    changed = comparator.get_changed_ddls()

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
