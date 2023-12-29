import os
from glob import glob
from pathlib import Path
from typing import Union, List, Dict, Tuple, Sequence

import sqlparse
from alembic.autogenerate.api import AutogenContext

from alembic_dddl.src.file_format import TimestampedFileFormat, DateTimeFileFormat
from alembic_dddl.src.models import RevisionedScript, DDL


class RevisionManager:
    def __init__(self, autogen_context: AutogenContext) -> None:
        self.revisions = autogen_context.opts["script"].walk_revisions()
        self.heads = autogen_context.opts["script"].get_heads()
        self.cur_head = autogen_context.opts["revision_context"].generated_revisions[0].head

    def get_ordered_revisions(self) -> List[str]:
        """
        Get the list of revisions ordered from head to base.

        We would normally just accept the order of revisions which `walk_revisions` offers us,
        except the situation when we are currently on a branch. In this case we want to filter
        out all revisions from the parallel branches.
        """

        if self.cur_head in ("head", "heads", None):
            next_ = set(self.heads)
        else:
            next_ = {self.cur_head}
        result = []
        for rev in self.revisions:
            if rev.revision in next_:
                result.append(rev.revision)
                next_.discard(rev.revision)
                if isinstance(rev.down_revision, tuple):
                    next_.update(rev.down_revision)
                else:
                    next_.add(rev.down_revision)
        return result


class DDLVersions:
    def __init__(self, ddl_dir: Union[Path, str]) -> None:
        self.ddl_dir = ddl_dir

    def _get_all_scripts(self) -> List[RevisionedScript]:
        """
        Find all .sql files in the ddl_dir and convert them into RevisionedScript objects
        if they match the supported filename formats.
        """

        result = []
        file_formats = [TimestampedFileFormat, DateTimeFileFormat]
        for file in glob(os.path.join(self.ddl_dir, "*.sql")):
            for format in file_formats:
                script = format.get_script_if_matches(file)
                if script:
                    result.append(script)
                    break
        return result

    def _group_by_revision(self, scripts: List[RevisionedScript]) -> Dict[str, List[RevisionedScript]]:
        """Group a list of RevisionedScripts into a dictionary by revisions."""
        result = {}

        for script in scripts:
            result.setdefault(script.revision, []).append(script)

        return result

    def get_latest_ddl_revisions(self, rev_order: List[str]) -> Dict[str, RevisionedScript]:
        """
        Use the list of revisions ordered from head to base in `rev_order` parameter to create a
        dictionary of the latest versions of each script in ddl dir by name.

        Args:
            rev_order: list of revision strings, ordered from current head to base.

        Returns:
            A dictionary of the most recent scripts for the current head where key is script name
            and value is RevisionedScript object,
        """

        scripts = self._get_all_scripts()
        ddl_by_revision = self._group_by_revision(scripts)
        return {
            s.name: s
            for r in reversed(rev_order)
            if r in ddl_by_revision
            for s in ddl_by_revision[r]
        }


class CustomDDLComparator:
    def __init__(
        self,
        ddl_dir: Union[Path, str],
        ddls: Sequence[DDL],
        autogen_context: AutogenContext,
    ) -> None:
        self.ddls = {d.name: d for d in ddls}
        self.rev_manager = RevisionManager(autogen_context=autogen_context)
        self.versions = DDLVersions(ddl_dir=ddl_dir)

    def get_changed_ddls(self) -> List[Tuple[DDL, RevisionedScript]]:
        rev_order = self.rev_manager.get_ordered_revisions()
        latest_revisions = self.versions.get_latest_ddl_revisions(rev_order)
        return self._compare(latest_revisions)

    def _compare(
        self, latest_revisions: Dict[str, RevisionedScript]
    ) -> List[Tuple[DDL, RevisionedScript]]:
        result = []
        for name, ddl in self.ddls.items():
            if name in latest_revisions:
                if self._scripts_differ(ddl, latest_revisions[name]):
                    result.append((ddl, latest_revisions[name]))
            else:
                result.append((ddl, None))
        return result

    def _scripts_differ(self, dddl: DDL, rev_script: RevisionedScript) -> bool:
        one = sqlparse.format(dddl.sql.strip(), reindent_aligned=True)
        two = sqlparse.format(rev_script.read().strip(), reindent_aligned=True)

        return one != two
