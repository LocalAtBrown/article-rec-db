import pytest
from sqlalchemy import create_engine, text

from article_rec_db.db.controller import pre_table_initialization
from article_rec_db.db.database import get_conn_string
from article_rec_db.db.helpers import Component, Stage
from article_rec_db.sites import AFRO_LA, DALLAS_FREE_PRESS


@pytest.fixture
def components() -> list[Component]:
    training_job = Component(
        name="training_job",
        grants=[],
        policies=[],
    )
    return [training_job]


@pytest.fixture
def site_names() -> list[str]:
    return [AFRO_LA.name_snakecase, DALLAS_FREE_PRESS.name_snakecase]


@pytest.fixture
def stage() -> Stage:
    return Stage.DEV


@pytest.mark.order(1)
def test_pre_table_initialization(components, site_names, stage):
    # run function
    pre_table_initialization(stage=stage, components=components, site_names=site_names)

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
