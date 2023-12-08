import os
from collections.abc import Generator
from enum import StrEnum

import pytest
from sqlalchemy.engine import Engine, create_engine
from sqlmodel import text

import alembic.command
import alembic.config
from article_rec_db.models import SQLModel


@pytest.fixture(scope="session")
def engine() -> Engine:
    return create_engine("postgresql://postgres:postgres@localhost:5432/postgres")


@pytest.fixture(scope="session")
def site_name() -> str:
    return "example-site"


class TestType(StrEnum):
    # Test models in a mock DB initialized with SQLModel.metadata.create_all(engine). Good for development
    SQLMODEL = "sqlmodel"
    # Test models in a mock DB initialized with Alembic migrations. Good for final testing of anything to be deployed, after a new Alembic revision has ben created
    ALEMBIC = "alembic"


@pytest.fixture(scope="session")
def test_type() -> TestType:
    return TestType(os.getenv("TYPE", TestType.SQLMODEL))


@pytest.fixture(scope="session")
def initialize_db(engine: Engine, test_type: TestType) -> Generator[None, None, None]:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    if test_type == TestType.SQLMODEL:
        SQLModel.metadata.create_all(engine)
        yield
        SQLModel.metadata.drop_all(engine)
    elif test_type == TestType.ALEMBIC:
        alembic_config = alembic.config.Config("alembic.ini")
        alembic_config.set_main_option("sqlalchemy.url", str(engine.url))
        alembic.command.upgrade(alembic_config, "head")
        yield
        alembic.command.downgrade(alembic_config, "base")


# scope="function" ensures that the records are dropped after each test
@pytest.fixture(scope="function")
def refresh_tables(engine, initialize_db) -> Generator[None, None, None]:
    yield
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE page CASCADE"))
        conn.execute(text("TRUNCATE TABLE article CASCADE"))
        conn.execute(text("TRUNCATE TABLE execution CASCADE"))
        conn.execute(text("TRUNCATE TABLE embedding CASCADE"))
        conn.execute(text("TRUNCATE TABLE recommendation CASCADE"))
        conn.commit()
