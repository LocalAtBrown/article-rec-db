import pytest
from sqlalchemy import create_engine, text

from article_rec_db.db.controller import (
    initialize_tables,
    post_table_initialization,
    pre_table_initialization,
)
from article_rec_db.db.database import get_conn_string
from article_rec_db.db.helpers import (
    Component,
    Extension,
    Grant,
    Privilege,
    RowLevelSecurityPolicy,
    Stage,
)
from article_rec_db.models import SQLModel
from article_rec_db.sites import AFRO_LA, DALLAS_FREE_PRESS


@pytest.fixture
def components() -> list[Component]:
    training_job = Component(
        name="training_job",
        grants=[
            Grant(
                privileges=[Privilege.SELECT, Privilege.INSERT, Privilege.UPDATE, Privilege.DELETE],
                tables=["page", "article", "embedding", "execution"],
            )
        ],
        policies=[
            RowLevelSecurityPolicy(table="article", user_column="site"),
        ],
    )
    return [training_job]


@pytest.fixture
def site_names() -> list[str]:
    return [AFRO_LA.name_snakecase, DALLAS_FREE_PRESS.name_snakecase]


@pytest.fixture
def stage() -> Stage:
    return Stage.DEV


@pytest.fixture
def extensions() -> list[Extension]:
    return [Extension(name="vector")]


@pytest.mark.order(1)
def test_pre_table_initialization(components, site_names, stage, extensions):
    # run function
    pre_table_initialization(stage=stage, components=components, site_names=site_names, extensions=extensions)

    engine = create_engine(get_conn_string(db_name="postgres"))
    with engine.connect() as conn:
        # make sure db exists
        statement = text("SELECT 1 AS result FROM pg_database WHERE datname=:db_name")
        result = conn.execute(statement, {"db_name": stage})
        result_data = result.fetchone()
        assert result_data[0] == 1

        # check if roles exist
        role_name_literals = [f"'{stage}_{component.name}'" for component in components]
        formatted_role_names = ", ".join(role_name_literals)
        statement = text(f"SELECT COUNT(*) AS result FROM pg_authid WHERE rolname IN ({formatted_role_names})")
        result = conn.execute(statement)
        result_data = result.fetchone()
        assert result_data[0] == len(components)

        # check if users exist
        username_literals = []
        for component in components:
            names_to_add = [f"'{stage}_{component.name}_{site_name}'" for site_name in site_names]
            username_literals.extend(names_to_add)
        formatted_usernames = ", ".join(username_literals)
        statement = text(f"SELECT COUNT(*) AS result FROM pg_authid WHERE rolname IN ({formatted_usernames})")
        result = conn.execute(statement)
        result_data = result.fetchone()
        assert result_data[0] == len(components) * len(site_names)

        # check if users are in correct roles
        for component in components:
            statement = text(
                f"WITH t AS (SELECT pg_auth_members.member from pg_authid "
                f"JOIN pg_auth_members ON pg_authid.oid = pg_auth_members.roleid "
                f"WHERE rolname = :role_name) "
                f"SELECT rolname FROM t JOIN pg_authid ON member = oid"
            )
            result = conn.execute(statement, {"role_name": f"{stage}_{component.name}"})
            result_data = result.fetchall()
            assert len(result_data) == len(site_names)
            expected_usernames = [f"{stage}_{component.name}_{site_name}" for site_name in site_names]
            assert sorted([row[0] for row in result_data]) == sorted(expected_usernames)

    engine_stage = create_engine(get_conn_string(db_name=stage))
    with engine_stage.connect() as conn:
        # make sure extensions are installed
        for extension in extensions:
            statement = text("SELECT EXISTS(SELECT FROM pg_extension WHERE extname=:name) AS result")
            result = conn.execute(statement, {"name": extension.name})
            result_data = result.fetchone()
            assert result_data[0] is True


@pytest.mark.order(2)
def test_initialize_tables(stage):
    # needs pre_table_init to have run
    initialize_tables(stage, SQLModel)
    # check to see if expected tables exist
    engine = create_engine(get_conn_string(db_name=stage))
    with engine.connect() as conn:
        statement = text(
            "SELECT tablename FROM pg_catalog.pg_tables "
            "WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema'"
        )
        result = conn.execute(statement)
        result_data = result.fetchall()
        assert sorted([row[0] for row in result_data]) == sorted(list(SQLModel.metadata.tables))


@pytest.mark.order(3)
def test_post_table_initialization(components, site_names, stage):
    # needs pre_table_init and table creation to have run
    post_table_initialization(stage=stage, components=components)

    engine = create_engine(get_conn_string(db_name=stage))
    with engine.connect() as conn:
        # check for correct privileges
        for component in components:
            for grant in component.grants:
                for table in grant.tables:
                    statement = text(
                        "SELECT privilege_type FROM information_schema.role_table_grants "
                        "WHERE table_name=:table_name AND grantee=:role_name"
                    )
                    result = conn.execute(statement, {"table_name": table, "role_name": f"{stage}_{component.name}"})
                    result_data = result.fetchall()
                    for row in result_data:
                        assert row[0] in grant.privileges

        # check row level security enabled
        tables_to_check = []
        for component in components:
            for policy in component.policies:
                tables_to_check.append(policy.table)

        # dedupe
        tables_to_check = set(tables_to_check)
        formatted_tables = ", ".join([f"'{table}'" for table in tables_to_check])

        statement = text("SELECT rowsecurity FROM pg_catalog.pg_tables " f"WHERE tablename IN ({formatted_tables})")
        result = conn.execute(statement)
        result_data = result.fetchall()
        assert len(result_data) == len(tables_to_check)
