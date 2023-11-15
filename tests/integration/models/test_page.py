from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from article_rec_db.models import ArticleExcludeReason, Page


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

        # Check that only page 1 is written
        session.rollback()
        num_pages = session.exec(select(func.count(Page.id))).one()
        assert num_pages == 1


def test_update_page(create_and_drop_tables, engine):
    page = Page(
        url="https://dallasfreepress.com/example-article/",
        article_exclude_reason=None,
    )
    with Session(engine) as session:
        session.add(page)
        session.commit()

        # Upon creation, db_updated_at should be None
        assert page.db_updated_at is None

        page.url = "https://dallasfreepress.com/example-article-2/"
        session.add(page)
        session.commit()

        # After updating, db_updated_at should be a datetime
        assert isinstance(page.db_updated_at, datetime)
