from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from alembic_dddl import RevisionedScript, SyncDDLOp, DDL
from alembic_dddl.src.ops import run_ddl_script, RunDDLScriptOp, render_create_ddl

DDL_DIR = Path(__file__).parent / "ddl"


def test_sync_ddl_op(sample_ddl1: DDL, rev_script: RevisionedScript) -> None:
    time = datetime.now()
    op = SyncDDLOp(up_script=sample_ddl1, down_script=rev_script, time=time)
    op2 = SyncDDLOp(up_script=rev_script, down_script=sample_ddl1, time=time)

    rev_op = op.reverse()

    assert rev_op.time == time
    assert rev_op.up_script == op.down_script
    assert rev_op.down_script == op.up_script

    rev_op2 = op2.reverse()
    assert rev_op2.time == time
    assert rev_op2.up_script == op2.down_script
    assert rev_op2.down_script == op2.up_script


@pytest.fixture
def mock_revision_script_renderer() -> Mock:
    with patch("alembic_dddl.src.ops.RevisionedScriptRenderer") as mock_renderer:
        yield mock_renderer


@pytest.fixture
def mock_ddl_renderer() -> Mock:
    with patch("alembic_dddl.src.ops.DDLRenderer") as mock_renderer:
        yield mock_renderer


@pytest.fixture
def mock_sql_renderer() -> Mock:
    with patch("alembic_dddl.src.ops.SQLRenderer") as mock_renderer:
        yield mock_renderer


class TestRenderCreateDDL:
    @staticmethod
    def test_revisioned_script(
        mock_revision_script_renderer: Mock,
        mock_ddl_renderer: Mock,
        mock_sql_renderer: Mock,
        sample_ddl1: DDL,
        rev_script: RevisionedScript,
    ) -> None:
        op = SyncDDLOp(
            up_script=rev_script, down_script=sample_ddl1, time=datetime.now()
        )

        render_create_ddl(autogen_context=MagicMock(), op=op)
        assert mock_revision_script_renderer.called is True
        assert mock_ddl_renderer.called is False
        assert mock_sql_renderer.called is False

    @staticmethod
    def test_ddl(
        mock_revision_script_renderer: Mock,
        mock_ddl_renderer: Mock,
        mock_sql_renderer: Mock,
        sample_ddl1: DDL,
        rev_script: RevisionedScript,
    ) -> None:
        op = SyncDDLOp(
            up_script=sample_ddl1, down_script=rev_script, time=datetime.now()
        )

        render_create_ddl(autogen_context=MagicMock(), op=op)
        assert mock_revision_script_renderer.called is False
        assert mock_ddl_renderer.called is True
        assert mock_sql_renderer.called is False

    @staticmethod
    def test_sql(
        mock_revision_script_renderer: Mock,
        mock_ddl_renderer: Mock,
        mock_sql_renderer: Mock,
        sample_ddl1: DDL,
    ) -> None:
        op = SyncDDLOp(
            up_script=sample_ddl1.down_sql, down_script=sample_ddl1, time=datetime.now()
        )

        render_create_ddl(autogen_context=MagicMock(), op=op)
        assert mock_revision_script_renderer.called is False
        assert mock_ddl_renderer.called is False
        assert mock_sql_renderer.called is True

    @staticmethod
    def test_unsupported(
        mock_revision_script_renderer: Mock,
        mock_ddl_renderer: Mock,
        mock_sql_renderer: Mock,
        sample_ddl1: DDL,
    ) -> None:
        op = SyncDDLOp(up_script=13, down_script=sample_ddl1, time=datetime.now())
        with pytest.raises(ValueError):
            render_create_ddl(autogen_context=MagicMock(), op=op)
        assert mock_revision_script_renderer.called is False
        assert mock_ddl_renderer.called is False
        assert mock_sql_renderer.called is False


@pytest.fixture
def mock_operations() -> Mock:
    mock_config = Mock(
        get_section=Mock(return_value={"scripts_location": str(DDL_DIR)})
    )
    operations = Mock(get_context=Mock(return_value=Mock(config=mock_config)))
    return operations


def test_run_ddl_script_op(mock_operations) -> None:
    RunDDLScriptOp.run_ddl_script(operations=mock_operations, script_name='script_name')
    assert mock_operations.invoke.called is True


class TestRunDDLScript:
    @staticmethod
    def test_one_statement(mock_operations: Mock) -> None:
        op = RunDDLScriptOp(script_name="sample_script_one_stmt.sql")
        run_ddl_script(operations=mock_operations, operation=op)

        assert mock_operations.execute.call_count == 1

    @staticmethod
    def test_two_statements(mock_operations: Mock) -> None:
        op = RunDDLScriptOp(script_name="sample_script_two_stmts.sql")
        run_ddl_script(operations=mock_operations, operation=op)

        assert mock_operations.execute.call_count == 2
