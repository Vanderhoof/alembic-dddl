import os
from glob import glob
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

import sqlparse
from alembic.autogenerate.api import AutogenContext

from alembic_dddl.src.file_format import DateTimeFileFormat, TimestampedFileFormat
from alembic_dddl.src.models import DDL, RevisionedScript


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

    def _group_by_revision(
        self, scripts: List[RevisionedScript]
    ) -> Dict[str, List[RevisionedScript]]:
        """Group a list of RevisionedScripts into a dictionary by revisions."""
        result: Dict[str, List[RevisionedScript]] = {}

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
        ignore_comments: bool,
    ) -> None:
        self.ddls = {d.name: d for d in ddls}
        self.latest_revisions = self._get_latest_revisions(ddl_dir, autogen_context)

        self.ignore_comments = ignore_comments

    def _get_latest_revisions(
        self, ddl_dir: Union[Path, str], autogen_context: AutogenContext
    ) -> Dict[str, RevisionedScript]:
        """
        Generate a collection of RevisionedScript, representing the latest revisions of every
        DDL for current head in the revision history.

        Args:
            ddl_dir: a directory containing autogenerated revisions of DDL scripts.
            autogen_context: current alembic's AutogenContext instance

        Returns:
            A dictionary with the latest revisions of the DDls where key is s script name, value is
            a RevisionedScript instance.
        """

        rev_manager = RevisionManager(autogen_context=autogen_context)
        rev_order = rev_manager.get_ordered_revisions()

        versions = DDLVersions(ddl_dir=ddl_dir)
        return versions.get_latest_ddl_revisions(rev_order)

    def get_changed_ddls(self) -> List[Tuple[DDL, Optional[RevisionedScript]]]:
        """
        Compare current DDL sources with the latest revisions of these DDls. If the source has
        changed or does not have a revision yet, this DDL will be returned, along with the
        revisioned script for it (if it's present, othewise second element will be None).

        Returns:
            List of pairs DDL - latest RevisionedScript for the changed DDLs.
        """

        result: List[Tuple[DDL, Optional[RevisionedScript]]] = []
        for name, ddl in self.ddls.items():
            latest_ddl_revision = self.latest_revisions.get(name)
            if latest_ddl_revision is not None:
                if self._scripts_differ(one=ddl.sql, two=latest_ddl_revision.read()):
                    result.append((ddl, latest_ddl_revision))
            else:
                result.append((ddl, None))
        return result

    def _scripts_differ(self, one: str, two: str) -> bool:
        """
        Compare two scripts, ignoring formatting and optionally ignoring comments.

        Args:
            one: the first script source code
            two: the second script source code

        Returns:
            True if the scripts differ, False if the scripts are the same
        """
        kwargs = {
            "reindent_aligned": True,
            "strip_comments": self.ignore_comments,
            "keyword_case": "upper",
            "identifier_case": "lower",
            "use_space_around_operators": True,
        }
        one_norm = sqlparse.format(one.strip(), **kwargs)
        two_norm = sqlparse.format(two.strip(), **kwargs)

        return one_norm != two_norm
