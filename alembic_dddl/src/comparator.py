import os
from glob import glob
from pathlib import Path
from typing import Union, List, Dict, Tuple, Sequence

import sqlparse
from alembic.script.revision import Revision

from alembic_dddl.src.models import RevisionedScript, DDL
from alembic_dddl.src.file_format import TimestampedFileFormat, DateTimeFileFormat


class DDLVersions:
    def __init__(
        self,
        ddl_dir: Union[Path, str],
    ) -> None:
        self.ddl_dir = ddl_dir

        self._ddl_by_revision = self._group_by_revision()

    def _get_all_scripts(self) -> List[RevisionedScript]:
        result = []
        file_formats = [TimestampedFileFormat, DateTimeFileFormat]
        for file in glob(os.path.join(self.ddl_dir, "*.sql")):
            for format in file_formats:
                script = format.get_script_if_matches(file)
                if script:
                    result.append(script)
                    break
        return result

    def _group_by_revision(self) -> Dict[str, List[RevisionedScript]]:
        result = {}
        scripts = self._get_all_scripts()

        for script in scripts:
            result.setdefault(script.revision, []).append(script)

        return result

    def get_latest_revisions(self, rev_order: List[str]) -> Dict[str, RevisionedScript]:
        return {
            s.name: s
            for r in reversed(rev_order)
            if r in self._ddl_by_revision
            for s in self._ddl_by_revision[r]
        }


class CustomDDLComparator:
    def __init__(
        self,
        ddl_dir: Union[Path, str],
        dddls: Sequence[DDL],
    ) -> None:
        self.ddls = {d.name: d for d in dddls}
        self.versions = DDLVersions(ddl_dir=ddl_dir)

    def get_changed_ddl(
        self, revisions: List[Revision], heads: List[str], cur_head: str
    ) -> List[Tuple[DDL, RevisionedScript]]:
        revisions_o = self._order_revisions(
            revisions=revisions, head=cur_head, heads=heads
        )
        latest_revisions = self.versions.get_latest_revisions(revisions_o)
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

    def _order_revisions(
        self, revisions: List[Revision], head: str, heads: List[str]
    ) -> List[str]:
        if head in ("head", "heads", None):
            next_ = heads[:]
        else:
            next_ = [head]
        result = []
        for rev in revisions:
            if rev.revision in next_:
                result.append(next_.pop(next_.index(rev.revision)))
                if isinstance(rev.down_revision, tuple):
                    next_ += rev.down_revision
                else:
                    next_.append(rev.down_revision)
        return result
