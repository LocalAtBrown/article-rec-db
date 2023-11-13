from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from article_rec_db.models import Article, Page
from article_rec_db.sites import DALLAS_FREE_PRESS


@pytest.mark.order(4)
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


@pytest.mark.order(5)
def test_add_article_excluded(create_and_drop_tables, engine):
    # Would be nice to test that adding a non-article (whose page has a non-null article_exclude_reason)
    # to the article table fails, but doing so at the model level is messy, so for now passing the responsibility
    # to the instance creation method in whichever application that uses this library
    pass


@pytest.mark.order(6)
def test_add_articles_duplicate_site_and_id_in_site(create_and_drop_tables, engine):
    page1 = Page(
        url="https://dallasfreepress.com/example-article/",
        article_exclude_reason=None,
    )
    page2 = Page(
        url="https://dallasfreepress.com/example-article-2/",
        article_exclude_reason=None,
    )
    id_in_site = "1234"
    article1 = Article(
        site=DALLAS_FREE_PRESS.name,
        id_in_site=id_in_site,
        title="Example Article",
        published_at=datetime.now(),
        page=page1,
    )
    article2 = Article(
        site=DALLAS_FREE_PRESS.name,
        id_in_site=id_in_site,
        title="Example Article 2",
        published_at=datetime.now(),
        page=page2,
    )

    with Session(engine) as session:
        session.add(article1)
        session.add(article2)
        # Since the combination of site and id_in_site is unique, adding an article with an already existing site and id_in_site must fail
        with pytest.raises(
            IntegrityError,
            match=r"duplicate key value violates unique constraint \"article_site_id_in_site_key\"",
        ):
            session.commit()
