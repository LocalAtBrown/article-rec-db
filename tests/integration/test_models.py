from collections.abc import Generator
from datetime import datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future.engine import Engine
from sqlmodel import Session, create_engine, func, select

from article_rec_db.models import Article, ArticleExcludeReason, Page, SQLModel
from article_rec_db.sites import DALLAS_FREE_PRESS


@pytest.fixture(scope="module")
def engine() -> Engine:
    return create_engine("postgresql://postgres:postgres@localhost:5432/postgres")


# scope="function" ensures that the tables are dropped after each test and recreated before each test
# make sure to increment the order number for each test to make sure there aren't any two tests running concurrently
@pytest.fixture(scope="function")
def create_and_drop_tables(engine) -> Generator[None, None, None]:
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.mark.order(4)
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
        assert len(page.article) == 0


@pytest.mark.order(5)
def test_add_page_is_article(create_and_drop_tables, engine):
    # This is how we would add a page that is also an article
    page = Page(
        url="https://dallasfreepress.com/example-article/",
        article_exclude_reason=None,
    )
    article_published_at = datetime.now()
    article = Article(
        site=DALLAS_FREE_PRESS.name,
        id_in_site="1234",
        title="Example Article",
        published_at=article_published_at,
        page=page,
    )

    with Session(engine) as session:
        session.add(article)
        session.commit()
        session.refresh(article)
        session.refresh(page)

        assert isinstance(page.id, UUID)
        assert isinstance(page.db_created_at, datetime)
        assert page.db_updated_at is None
        assert page.url == "https://dallasfreepress.com/example-article/"
        assert page.article_exclude_reason is None
        assert len(page.article) == 1
        assert page.article[0] is article

        assert isinstance(article.db_created_at, datetime)
        assert article.db_updated_at is None
        assert article.page_id == page.id
        assert article.site == DALLAS_FREE_PRESS.name
        assert article.id_in_site == "1234"
        assert article.title == "Example Article"
        assert article.published_at == article_published_at
        assert article.page is page


@pytest.mark.order(6)
def test_add_pages_duplicate_url(create_and_drop_tables, engine):
    page1 = Page(
        url="https://dallasfreepress.com/example-article/",
        article_exclude_reason=None,
    )
    page2 = Page(
        url="https://dallasfreepress.com/example-article/",
        article_exclude_reason=None,
    )
    with Session(engine) as session:
        session.add(page1)
        session.commit()

        session.add(page2)
        # Since the URL is unique, adding a page with an already existing URL must fail
        with pytest.raises(
            IntegrityError,
            match=r"duplicate key value violates unique constraint \"page_url_key\"",
        ):
            session.commit()


@pytest.mark.order(7)
def test_add_article_without_page(create_and_drop_tables, engine):
    article = Article(
        page_id=uuid4(),
        site=DALLAS_FREE_PRESS.name,
        id_in_site="2345",
        title="Example Article",
        published_at=datetime.now(),
    )

    with Session(engine) as session:
        session.add(article)

        # Since there's no page to refer to, adding an standalone article must fail
        with pytest.raises(
            IntegrityError,
            match=r"insert or update on table \"article\" violates foreign key constraint \"article_page_id_fkey\"",
        ):
            session.commit()

        # Check that nothing is written
        session.rollback()
        num_articles = session.exec(select(func.count(Article.page_id))).one()
        assert num_articles == 0


# @pytest.mark.order(8)
# def test_add_article_excluded(create_and_drop_tables, engine):
#     page = Page(
#         url="https://afrolanews.org/",
#         article_exclude_reason=ArticleExcludeReason.NOT_ARTICLE,
#     )
#     with Session(engine) as session, pytest.raises(
#         ArticleValidationError,
#         match=r"cannot be added to the article table because it's excluded as specified in the page table",
#     ):
#         article = Article(
#             session=session,
#             site=AFRO_LA.name,
#             id_in_site="1111",
#             title="Home page and definitely not an article",
#             published_at=datetime.now(),
#             page=page,
#         )
