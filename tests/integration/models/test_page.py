from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from article_rec_db.models import Article, ArticleExcludeReason, Page
from article_rec_db.sites import DALLAS_FREE_PRESS


@pytest.mark.order(1)
def test_add_page_not_article(create_and_drop_tables, engine):
    page = Page(
        url="https://afrolanews.org/",
        article_exclude_reason=ArticleExcludeReason.NOT_ARTICLE,
    )
    with Session(engine) as session:
        session.add(page)
        session.commit()

        assert isinstance(page.id, UUID)
        assert isinstance(page.db_created_at, datetime)
        assert page.db_updated_at is None
        assert page.url == "https://afrolanews.org/"
        assert page.article_exclude_reason == ArticleExcludeReason.NOT_ARTICLE
        assert len(page.article) == 0


@pytest.mark.order(2)
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


@pytest.mark.order(3)
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
