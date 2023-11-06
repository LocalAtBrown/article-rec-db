from collections.abc import Generator
from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy.future.engine import Engine
from sqlmodel import Session, create_engine

from article_rec_db.models import ArticleExcludeReason, Page, SQLModel


@pytest.fixture(scope="module")
def create_and_drop_tables(engine: Engine) -> Generator[None, None, None]:
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="module")
def engine() -> Engine:
    return create_engine("postgresql://postgres:postgres@localhost:5432/postgres")


@pytest.mark.order(4)
def test_create_tables(engine):
    # if it runs and no errors pop up, congrats, the tables were made without error
    SQLModel.metadata.create_all(engine)


@pytest.mark.order(5)
def test_add_page_not_article(create_and_drop_tables, engine):
    page = Page(
        url="https://afrolanews.org/",
        article_exclude_reason=ArticleExcludeReason.NOT_ARTICLE,
    )
    with Session(engine) as session:
        session.add(page)
        session.commit()
        session.refresh(page)  # Effectively a SELECT query for the page we just added

        assert isinstance(page.id, UUID)
        assert isinstance(page.db_created_at, datetime)
        assert page.db_updated_at is None
        assert page.url == "https://afrolanews.org/"
        assert page.article_exclude_reason == ArticleExcludeReason.NOT_ARTICLE
