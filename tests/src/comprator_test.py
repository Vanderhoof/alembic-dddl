import os
from collections import namedtuple
from typing import Generator, Union, Tuple, List, Dict
from unittest.mock import Mock, patch

import pytest

from alembic_dddl import RevisionedScript
from alembic_dddl.src.comparator import RevisionManager, DDLVersions

MockScript = namedtuple("MockScript", "revision down_revision")


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
        MockScript("fa60c3c43112", "d07f839a619e"),                    #  |
        MockScript("d07f839a619e", ("1e1166bc4bfb", "02d083a6d802")),  #  ^
        MockScript("1e1166bc4bfb", "4203cf736fe7"),                    #   |
        MockScript("4203cf736fe7", "a8f2b6e146a3"),                    #   |
        MockScript("02d083a6d802", "a6043c53a101"),                    # |
        MockScript("a6043c53a101", "a8f2b6e146a3"),                    # |
        MockScript("a8f2b6e146a3", "181ce9418692"),                    #  V
        MockScript("181ce9418692", "4b550063ade3"),                    #  |
        MockScript("4b550063ade3", "a4d24c99c672"),                    #  |
        MockScript("a4d24c99c672", None),                              #  |
    ]


def gen_autogen_context(rev_tree: List[Mock], head: Union[str, None] = None) -> Mock:
    heads = [rev_tree[0].revision]
    cur_head = head if head else heads[0]
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
    def test_init(rev_tree_simple: List[Mock]) -> None:
        autogen_context = gen_autogen_context(rev_tree_simple)
        rev_man = RevisionManager(autogen_context=autogen_context)

        assert rev_man.revisions == rev_tree_simple
        assert rev_man.heads == [rev_tree_simple[0].revision]
        assert rev_man.cur_head == rev_tree_simple[0].revision

    @staticmethod
    def test_get_ordered_revisions_simple(rev_tree_simple: List[Mock]) -> None:
        autogen_context = gen_autogen_context(rev_tree_simple)
        rev_man = RevisionManager(autogen_context=autogen_context)

        expected = ["a8f2b6e146a3", "181ce9418692", "4b550063ade3", "a4d24c99c672"]
        assert rev_man.get_ordered_revisions() == expected

    @staticmethod
    def test_get_ordered_revisions_complex(rev_tree_complex: List[Mock]) -> None:
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
    def test_get_ordered_revisions_start_on_a_branch(rev_tree_complex: List[Mock]) -> None:
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
            '/2023_01_01_0915_calculate_totals_02d083a6d802.sql',
            '/2023_02_02_0915_calculate_totals_a6043c53a101.sql',
            '/2023_02_02_0915_summary_view_a6043c53a101.sql',
            '/1699860266_check_tax_id_a8f2b6e146a3.sql',
            '/1703860266_report_a6043c53a101.sql',
        }
        not_scripts = {
            'wrong_script_format.sql',
            'not_a_script.sql',
            'skipped.sql'
        }
        with patch('alembic_dddl.src.comparator.glob', Mock(return_value=[*not_scripts, *scripts])) as mock_glob:
            result = ddl_versions._get_all_scripts()

        assert set(r.filepath for r in result) == scripts

    @staticmethod
    def test_get_all_scripts(ddl_versions: DDLVersions) -> None:
        scripts = {
            '/2023_01_01_0915_calculate_totals_02d083a6d802.sql',
            '/2023_02_02_0915_calculate_totals_a6043c53a101.sql',
            '/2023_02_02_0915_summary_view_a6043c53a101.sql',
            '/1699860266_check_tax_id_a8f2b6e146a3.sql',
            '/1703860266_report_a6043c53a101.sql',
        }
        not_scripts = {
            'wrong_script_format.sql',
            'not_a_script.sql',
            'skipped.sql'
        }
        with patch('alembic_dddl.src.comparator.glob', Mock(return_value=[*not_scripts, *scripts])) as mock_glob:
            result = ddl_versions._get_all_scripts()

        assert set(r.filepath for r in result) == scripts

    @staticmethod
    def test_group_by_revision(ddl_versions: DDLVersions) -> None:

        script1 = RevisionedScript(
            filepath='/2023_01_01_0915_calculate_totals_02d083a6d802.sql',
            name='calculate_totals',
            revision='02d083a6d802'
        )
        script2 = RevisionedScript(
            filepath='/2023_02_02_0915_calculate_totals_a6043c53a101.sql',
            name='calculate_totals',
            revision='a6043c53a101'
        )
        script3 = RevisionedScript(
            filepath='/2023_02_02_0915_summary_view_a6043c53a101.sql',
            name='summary_view',
            revision='a6043c53a101'
        )
        script4 = RevisionedScript(
            filepath='/1699860266_check_tax_id_a8f2b6e146a3.sql',
            name='check_tax_id',
            revision='a8f2b6e146a3'
        )
        script5 = RevisionedScript(
            filepath='/1703860266_report_a6043c53a101.sql',
            name='report',
            revision='a6043c53a101'
        )
        scripts = [script1, script2, script3, script4, script5]

        expected = {
            '02d083a6d802': [script1],
            'a6043c53a101': [script2, script3, script5],
            'a8f2b6e146a3': [script4]
        }

        result = ddl_versions._group_by_revision(scripts)

        assert result == expected


class TestDDLVersionsGetLatestDDLRevisions:
    @staticmethod
    def test_one_script_per_revision(ddl_versions: DDLVersions) -> None:
        rev_order = ['rev3', 'rev2', 'rev1']
        scripts = {
            '/1700000000_script1_rev1.sql',
            '/1700000000_script2_rev2.sql',
            '/1700000000_script3_rev3.sql',
        }

        expected = {
            'script1': RevisionedScript(
                filepath='/1700000000_script1_rev1.sql',
                name='script1',
                revision='rev1'
            ),
            'script2': RevisionedScript(
                filepath='/1700000000_script2_rev2.sql',
                name='script2',
                revision='rev2'
            ),
            'script3': RevisionedScript(
                filepath='/1700000000_script3_rev3.sql',
                name='script3',
                revision='rev3'
            ),
        }

        with patch('alembic_dddl.src.comparator.glob', Mock(return_value=scripts)):
            result = ddl_versions.get_latest_ddl_revisions(rev_order=rev_order)
        assert result == expected

    @staticmethod
    def test_several_scripts_per_revision(ddl_versions: DDLVersions) -> None:
        rev_order = ['rev3', 'rev2', 'rev1']
        scripts = {
            '/1700000000_script1_rev1.sql',
            '/1700000000_script1_rev2.sql',
            '/1700000000_script2_rev2.sql',
            '/1700000000_script2_rev3.sql',
            '/1700000000_script3_rev3.sql',
        }

        expected = {
            'script1': RevisionedScript(
                filepath='/1700000000_script1_rev2.sql',
                name='script1',
                revision='rev2'
            ),
            'script2': RevisionedScript(
                filepath='/1700000000_script2_rev3.sql',
                name='script2',
                revision='rev3'
            ),
            'script3': RevisionedScript(
                filepath='/1700000000_script3_rev3.sql',
                name='script3',
                revision='rev3'
            ),
        }

        with patch('alembic_dddl.src.comparator.glob', Mock(return_value=scripts)):
            result = ddl_versions.get_latest_ddl_revisions(rev_order=rev_order)
        assert result == expected

    @staticmethod
    def test_outside_scope(ddl_versions: DDLVersions) -> None:
        rev_order = ['rev2', 'rev1']
        scripts = {
            '/1700000000_script0_rev0.sql',
            '/1700000000_script1_rev1.sql',
            '/1700000000_script2_rev2.sql',
            '/1700000000_script3_rev3.sql',
        }

        expected = {
            'script1': RevisionedScript(
                filepath='/1700000000_script1_rev1.sql',
                name='script1',
                revision='rev1'
            ),
            'script2': RevisionedScript(
                filepath='/1700000000_script2_rev2.sql',
                name='script2',
                revision='rev2'
            ),
        }

        with patch('alembic_dddl.src.comparator.glob', Mock(return_value=scripts)):
            result = ddl_versions.get_latest_ddl_revisions(rev_order=rev_order)
        assert result == expected
