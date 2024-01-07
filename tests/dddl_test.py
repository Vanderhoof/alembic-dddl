from unittest.mock import patch, Mock, MagicMock

from alembic_dddl import DDL, RevisionedScript
from alembic_dddl.dddl import DDLRegistry, ddl_registry, register_ddl, compare_custom_ddl


class TestDDLRegistry:
    @staticmethod
    def test_ddl(sample_ddl1: DDL) -> None:
        ddl_registry = DDLRegistry()
        ddl_registry.register(sample_ddl1)
        assert ddl_registry.ddls == [sample_ddl1]

    @staticmethod
    def test_list(sample_ddl1: DDL, sample_ddl2: DDL, sample_ddl3: DDL) -> None:
        ddl_registry = DDLRegistry()
        ddl_registry.ddls = [sample_ddl1]
        ddl_registry.register([sample_ddl2, sample_ddl3])
        assert ddl_registry.ddls == [sample_ddl1, sample_ddl2, sample_ddl3]


def test_register_ddl(sample_ddl1: DDL) -> None:
    register_ddl(sample_ddl1)
    assert ddl_registry.ddls == [sample_ddl1]


def test_compare_custom_ddl(
    sample_ddl1: DDL, sample_ddl2: DDL, sample_ddl3: DDL, rev_script: RevisionedScript
) -> None:
    changed_ddls = [(sample_ddl1, rev_script), (sample_ddl2, None), (sample_ddl3, None)]
    get_changed_ddls_mock = Mock(return_value=changed_ddls)
    upgrade_ops = Mock(ops=[])
    with patch(
        "alembic_dddl.dddl.CustomDDLComparator",
        Mock(return_value=Mock(get_changed_ddls=get_changed_ddls_mock)),
    ):
        compare_custom_ddl(autogen_context=MagicMock(), upgrade_ops=upgrade_ops, _=None)
    assert len(upgrade_ops.ops) == 3
    assert upgrade_ops.ops[0].up_script == sample_ddl1
    assert upgrade_ops.ops[0].down_script == rev_script

    assert upgrade_ops.ops[1].up_script == sample_ddl2
    assert upgrade_ops.ops[1].down_script == sample_ddl2.down_sql

    assert upgrade_ops.ops[2].up_script == sample_ddl3
    assert upgrade_ops.ops[2].down_script == sample_ddl3.down_sql

    assert upgrade_ops.ops[0].time == upgrade_ops.ops[1].time == upgrade_ops.ops[2].time
