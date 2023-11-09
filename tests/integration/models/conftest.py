from collections.abc import Generator

import pytest
from sqlalchemy.future.engine import Engine, create_engine

from article_rec_db.models import SQLModel


@pytest.fixture(scope="module")
def engine() -> Engine:
    return create_engine("postgresql://postgres:postgres@localhost:5432/dev")


# scope="function" ensures that the tables are dropped after each test and recreated before each test
# make sure to increment the order number for each test to make sure there aren't any two tests running concurrently
@pytest.fixture(scope="function")
def create_and_drop_tables(engine) -> Generator[None, None, None]:
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)
