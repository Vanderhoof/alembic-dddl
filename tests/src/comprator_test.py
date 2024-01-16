import os
from collections import namedtuple
from pathlib import Path
from textwrap import dedent
from typing import Dict, List, Union
from unittest.mock import Mock, patch

import pytest

from alembic_dddl import DDL
from alembic_dddl.src.comparator import (
    CustomDDLComparator,
    DDLVersions,
    RevisionManager,
)
from alembic_dddl.src.models import RevisionedScript

MockScript = namedtuple("MockScript", "revision down_revision")

DDL_DIR = Path(__file__).parent / "ddl"


@pytest.fixture
def rev_tree_simple() -> List[MockScript]:
    return [
        MockScript("a8f2b6e146a3", "181ce9418692"),
        MockScript("181ce9418692", "4b550063ade3"),
        MockScript("4b550063ade3", "a4d24c99c672"),
        MockScript("a4d24c99c672", None),
    ]


@pytest.fixture
def rev_tree_complex() -> List[MockScript]:
    return [
        MockScript("fa60c3c43112", "d07f839a619e"),
        MockScript("d07f839a619e", ("1e1166bc4bfb", "02d083a6d802")),
        MockScript("1e1166bc4bfb", "4203cf736fe7"),
        MockScript("4203cf736fe7", "a8f2b6e146a3"),
        MockScript("02d083a6d802", "a6043c53a101"),
        MockScript("a6043c53a101", "a8f2b6e146a3"),
        MockScript("a8f2b6e146a3", "181ce9418692"),
        MockScript("181ce9418692", "4b550063ade3"),
        MockScript("4b550063ade3", "a4d24c99c672"),
        MockScript("a4d24c99c672", None),
    ]


def gen_autogen_context(rev_tree: List[MockScript], head: Union[str, None] = None) -> Mock:
    heads = [rev_tree[0].revision]
    cur_head = head if head else "head"
    result = Mock(
        opts={
            "script": Mock(
                walk_revisions=Mock(return_value=rev_tree),
                get_heads=Mock(return_value=heads),
            ),
            "revision_context": Mock(generated_revisions=[Mock(head=cur_head)]),
        }
    )
    return result


class TestRevisionManager:
    @staticmethod
    def test_init(rev_tree_simple: List[MockScript]) -> None:
        autogen_context = gen_autogen_context(rev_tree_simple)
        rev_man = RevisionManager(autogen_context=autogen_context)

        assert rev_man.revisions == rev_tree_simple
        assert rev_man.heads == [rev_tree_simple[0].revision]
        assert rev_man.cur_head == "head"

    @staticmethod
    def test_get_ordered_revisions_simple(rev_tree_simple: List[MockScript]) -> None:
        autogen_context = gen_autogen_context(rev_tree_simple)
        rev_man = RevisionManager(autogen_context=autogen_context)

        expected = ["a8f2b6e146a3", "181ce9418692", "4b550063ade3", "a4d24c99c672"]
        assert rev_man.get_ordered_revisions() == expected

    @staticmethod
    def test_get_ordered_revisions_complex(rev_tree_complex: List[MockScript]) -> None:
        autogen_context = gen_autogen_context(rev_tree_complex)
        rev_man = RevisionManager(autogen_context=autogen_context)

        expected = [
            "fa60c3c43112",
            "d07f839a619e",
            "1e1166bc4bfb",
            "4203cf736fe7",
            "02d083a6d802",
            "a6043c53a101",
            "a8f2b6e146a3",
            "181ce9418692",
            "4b550063ade3",
            "a4d24c99c672",
        ]
        assert rev_man.get_ordered_revisions() == expected

    @staticmethod
    def test_get_ordered_revisions_start_on_a_branch(rev_tree_complex: List[MockScript]) -> None:
        autogen_context = gen_autogen_context(rev_tree_complex, head="1e1166bc4bfb")
        rev_man = RevisionManager(autogen_context=autogen_context)

        expected = [
            "1e1166bc4bfb",
            "4203cf736fe7",
            # "02d083a6d802" is on another branch
            # "a6043c53a101" is on another branch
            "a8f2b6e146a3",
            "181ce9418692",
            "4b550063ade3",
            "a4d24c99c672",
        ]
        assert rev_man.get_ordered_revisions() == expected


@pytest.fixture
def ddl_versions() -> DDLVersions:
    return DDLVersions(os.path.split(__file__)[0])


class TestDDLVersions:
    @staticmethod
    def test_get_all_scripts(ddl_versions: DDLVersions) -> None:
        scripts = {
            "/2023_01_01_0915_calculate_totals_02d083a6d802.sql",
            "/2023_02_02_0915_calculate_totals_a6043c53a101.sql",
            "/2023_02_02_0915_summary_view_a6043c53a101.sql",
            "/1699860266_check_tax_id_a8f2b6e146a3.sql",
            "/1703860266_report_a6043c53a101.sql",
        }
        not_scripts = {"wrong_script_format.sql", "not_a_script.sql", "skipped.sql"}
        with patch(
            "alembic_dddl.src.comparator.glob", Mock(return_value=[*not_scripts, *scripts])
        ):
            result = ddl_versions._get_all_scripts()

        assert set(r.filepath for r in result) == scripts

    @staticmethod
    def test_group_by_revision(ddl_versions: DDLVersions) -> None:
        script1 = RevisionedScript(
            filepath="/2023_01_01_0915_calculate_totals_02d083a6d802.sql",
            name="calculate_totals",
            revision="02d083a6d802",
        )
        script2 = RevisionedScript(
            filepath="/2023_02_02_0915_calculate_totals_a6043c53a101.sql",
            name="calculate_totals",
            revision="a6043c53a101",
        )
        script3 = RevisionedScript(
            filepath="/2023_02_02_0915_summary_view_a6043c53a101.sql",
            name="summary_view",
            revision="a6043c53a101",
        )
        script4 = RevisionedScript(
            filepath="/1699860266_check_tax_id_a8f2b6e146a3.sql",
            name="check_tax_id",
            revision="a8f2b6e146a3",
        )
        script5 = RevisionedScript(
            filepath="/1703860266_report_a6043c53a101.sql", name="report", revision="a6043c53a101"
        )
        scripts = [script1, script2, script3, script4, script5]

        expected = {
            "02d083a6d802": [script1],
            "a6043c53a101": [script2, script3, script5],
            "a8f2b6e146a3": [script4],
        }

        result = ddl_versions._group_by_revision(scripts)

        assert result == expected


class TestDDLVersionsGetLatestDDLRevisions:
    @staticmethod
    def test_one_script_per_revision(ddl_versions: DDLVersions) -> None:
        rev_order = ["rev3", "rev2", "rev1"]
        scripts = {
            "/1700000000_script1_rev1.sql",
            "/1700000000_script2_rev2.sql",
            "/1700000000_script3_rev3.sql",
        }

        expected = {
            "script1": RevisionedScript(
                filepath="/1700000000_script1_rev1.sql", name="script1", revision="rev1"
            ),
            "script2": RevisionedScript(
                filepath="/1700000000_script2_rev2.sql", name="script2", revision="rev2"
            ),
            "script3": RevisionedScript(
                filepath="/1700000000_script3_rev3.sql", name="script3", revision="rev3"
            ),
        }

        with patch("alembic_dddl.src.comparator.glob", Mock(return_value=scripts)):
            result = ddl_versions.get_latest_ddl_revisions(rev_order=rev_order)
        assert result == expected

    @staticmethod
    def test_several_scripts_per_revision(ddl_versions: DDLVersions) -> None:
        rev_order = ["rev3", "rev2", "rev1"]
        scripts = {
            "/1700000000_script1_rev1.sql",
            "/1700000000_script1_rev2.sql",
            "/1700000000_script2_rev2.sql",
            "/1700000000_script2_rev3.sql",
            "/1700000000_script3_rev3.sql",
        }

        expected = {
            "script1": RevisionedScript(
                filepath="/1700000000_script1_rev2.sql", name="script1", revision="rev2"
            ),
            "script2": RevisionedScript(
                filepath="/1700000000_script2_rev3.sql", name="script2", revision="rev3"
            ),
            "script3": RevisionedScript(
                filepath="/1700000000_script3_rev3.sql", name="script3", revision="rev3"
            ),
        }

        with patch("alembic_dddl.src.comparator.glob", Mock(return_value=scripts)):
            result = ddl_versions.get_latest_ddl_revisions(rev_order=rev_order)
        assert result == expected

    @staticmethod
    def test_outside_scope(ddl_versions: DDLVersions) -> None:
        rev_order = ["rev2", "rev1"]
        scripts = {
            "/1700000000_script0_rev0.sql",
            "/1700000000_script1_rev1.sql",
            "/1700000000_script2_rev2.sql",
            "/1700000000_script3_rev3.sql",
        }

        expected = {
            "script1": RevisionedScript(
                filepath="/1700000000_script1_rev1.sql", name="script1", revision="rev1"
            ),
            "script2": RevisionedScript(
                filepath="/1700000000_script2_rev2.sql", name="script2", revision="rev2"
            ),
        }

        with patch("alembic_dddl.src.comparator.glob", Mock(return_value=scripts)):
            result = ddl_versions.get_latest_ddl_revisions(rev_order=rev_order)
        assert result == expected


@pytest.fixture
def mock_autogen_context(rev_tree_simple: List[MockScript]) -> Mock:
    return gen_autogen_context(rev_tree_simple)


@pytest.fixture
def empty_comparator(mock_autogen_context) -> CustomDDLComparator:
    return CustomDDLComparator(
        ddl_dir=Path(__file__).parent,
        ddls=[],
        autogen_context=mock_autogen_context,
        ignore_comments=False,
    )


class TestComparatorScriptsDiffer:
    @staticmethod
    def test_same_script(empty_comparator: CustomDDLComparator) -> None:
        script = "SELECT * FROM Customers WHERE customer_name LIKE 'John%';"
        assert empty_comparator._scripts_differ(one=script, two=script) is False

    @staticmethod
    def test_different_script(empty_comparator: CustomDDLComparator) -> None:
        script1 = "SELECT * FROM Customers WHERE customer_name LIKE 'John%';"
        script2 = "SELECT * FROM Orders WHERE paid = False;"
        assert empty_comparator._scripts_differ(one=script1, two=script2) is True

    @staticmethod
    def test_reformatted_script(empty_comparator: CustomDDLComparator) -> None:
        script1 = "SELECT * FROM Customers WHERE customer_name LIKE 'John%';"
        script2 = dedent(
            """
            SELECT *
            FROM Customers
            WHERE customer_name LIKE 'John%';"""
        )
        assert empty_comparator._scripts_differ(one=script1, two=script2) is False

    @staticmethod
    def test_changed_case_script(empty_comparator: CustomDDLComparator) -> None:
        script1 = "SELECT * FROM Customers WHERE customer_name LIKE 'John%';"
        script2 = "select * fRoM CuStOmErS WHERE CUSTOMER_NAME LIKE 'John%';"
        assert empty_comparator._scripts_differ(one=script1, two=script2) is False

    @staticmethod
    def test_comments_ignored(empty_comparator: CustomDDLComparator) -> None:
        empty_comparator.ignore_comments = True
        script1 = "SELECT * FROM Customers WHERE customer_name LIKE 'John%';"
        script2 = dedent(
            """
            SELECT *
            FROM Customers -- table containing customers
            WHERE customer_name LIKE 'John%';"""
        )
        assert empty_comparator._scripts_differ(one=script1, two=script2) is False

    @staticmethod
    def test_comments_not_ignored(empty_comparator: CustomDDLComparator) -> None:
        empty_comparator.ignore_comments = False
        script1 = "SELECT * FROM Customers WHERE customer_name LIKE 'John%';"
        script2 = dedent(
            """
            SELECT *
            FROM Customers -- table containing customers
            WHERE customer_name LIKE 'John%';"""
        )
        assert empty_comparator._scripts_differ(one=script1, two=script2) is True


@pytest.fixture
def rev_script1() -> RevisionedScript:
    return RevisionedScript(
        filepath=str(DDL_DIR / "2023_10_06_1522_sample_ddl1_4b550063ade3.sql"),
        name="sample_ddl1",
        revision="4b550063ade3",
    )


@pytest.fixture
def rev_script2_old() -> RevisionedScript:
    return RevisionedScript(
        filepath=str(DDL_DIR / "2023_10_06_1522_sample_ddl2_4b550063ade3.sql"),
        name="sample_ddl2",
        revision="4b550063ade3",
    )


@pytest.fixture
def rev_script2_new() -> RevisionedScript:
    return RevisionedScript(
        filepath=str(DDL_DIR / "2023_10_26_1028_sample_ddl2_181ce9418692.sql"),
        name="sample_ddl2",
        revision="181ce9418692",
    )


@pytest.fixture
def rev_script4() -> RevisionedScript:
    return RevisionedScript(
        filepath=str(DDL_DIR / "2023_10_26_1028_sample_ddl4_181ce9418692.sql"),
        name="sample_ddl4",
        revision="181ce9418692",
    )


@pytest.fixture
def latest_revisions(
    rev_script1: RevisionedScript,
    rev_script2_new: RevisionedScript,
    rev_script4: RevisionedScript,
) -> Dict[str, RevisionedScript]:
    return {r.name: r for r in [rev_script1, rev_script2_new, rev_script4]}


@pytest.fixture
def sample_ddls(
    sample_ddl1: DDL,  #
    sample_ddl2: DDL,  # has two revisions
    sample_ddl3: DDL,  # does not exist in revisions
) -> Dict[str, DDL]:
    return {d.name: d for d in [sample_ddl1, sample_ddl2, sample_ddl3]}


class TestComparatorGetChangedDDLs:
    def test_changed_missing_and_new(
        self,
        empty_comparator: CustomDDLComparator,
        latest_revisions: Dict[str, RevisionedScript],
        sample_ddls: Dict[str, DDL],
    ) -> None:
        empty_comparator.latest_revisions = latest_revisions
        empty_comparator.ddls = sample_ddls
        result = empty_comparator.get_changed_ddls()
        assert len(result) == 3
        assert result[0][1].filepath == str(  # type: ignore
            DDL_DIR / "2023_10_06_1522_sample_ddl1_4b550063ade3.sql"
        )
        assert result[1][1].filepath == str(  # type: ignore
            DDL_DIR / "2023_10_26_1028_sample_ddl2_181ce9418692.sql"
        )
        assert result[2][1] is None


class TestComparatorGetLatestRevisions:
    def test_ok(
        self,
        rev_tree_simple: List[MockScript],
        latest_revisions: Dict[str, RevisionedScript],
        empty_comparator: CustomDDLComparator,
    ) -> None:
        autogen_context = gen_autogen_context(rev_tree_simple)
        result = empty_comparator._get_latest_revisions(
            ddl_dir=DDL_DIR, autogen_context=autogen_context
        )

        assert result == latest_revisions
