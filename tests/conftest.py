from textwrap import dedent

import pytest

from alembic_dddl import RevisionedScript, DDL


@pytest.fixture
def rev_script() -> RevisionedScript:
    return RevisionedScript(
        filepath="/path/to/2023_10_06_1522_sample_ddl_4b550063ade3.sql",
        name="sample_ddl",
        revision="4b550063ade3",
    )


@pytest.fixture
def sample_ddl1() -> DDL:
    return DDL(
        name="sample_ddl1",
        sql=dedent("""\
            DROP VIEW IF EXISTS sample_ddl1;
            
            CREATE VIEW sample_ddl1 AS SELECT customer_name, age from customers;
        """),
        down_sql="DROP VIEW sample_ddl1;"
    )


@pytest.fixture
def sample_ddl2() -> DDL:
    return DDL(
        name="sample_ddl2",
        sql=dedent("""\
            DROP VIEW IF EXISTS sample_ddl2;
            
            CREATE VIEW sample_ddl2 AS SELECT order_number, total from orders;
        """),
        down_sql="DROP VIEW sample_ddl2;"
    )


@pytest.fixture
def sample_ddl3() -> DDL:
    return DDL(
        name="sample_ddl3",
        sql=dedent("""\
            DROP VIEW IF EXISTS sample_ddl3;
            
            CREATE VIEW sample_ddl3 AS SELECT product_name, price from products;
        """),
        down_sql="DROP VIEW sample_ddl3;"
    )
