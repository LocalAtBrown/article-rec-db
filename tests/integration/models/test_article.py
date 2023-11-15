from datetime import datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from article_rec_db.models import Article, ArticleExcludeReason, Page
from article_rec_db.sites import AFRO_LA, DALLAS_FREE_PRESS


def test_add_article_with_page(create_and_drop_tables, engine):
    # This is how we would add a page that is also an article
    page = Page(
        url="https://dallasfreepress.com/example-article/",
        article_exclude_reason=None,
    )
    article_published_at = datetime.utcnow()
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
        assert len(article.embeddings) == 0
        assert len(article.recommendations_where_this_is_source) == 0
        assert len(article.recommendations_where_this_is_target) == 0


def test_add_article_without_page(create_and_drop_tables, engine):
    article = Article(
        page_id=uuid4(),
        site=DALLAS_FREE_PRESS.name,
        id_in_site="2345",
        title="Example Article",
        published_at=datetime.utcnow(),
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


def test_add_article_excluded_from_page_side(create_and_drop_tables, engine):
    article = Article(
        site=AFRO_LA.name,
        id_in_site="1234",
        title="Actually a Home Page and Not an Article",
        published_at=datetime.utcnow(),
    )

    with pytest.raises(
        AssertionError, match=r"Page has a non-null article_exclude_reason, so it cannot be added as an article"
    ):
        Page(
            id=uuid4(),
            url="https://afrolanews.org/",
            article_exclude_reason=ArticleExcludeReason.NOT_ARTICLE,
            article=[article],
        )


def test_add_article_excluded_from_article_side(create_and_drop_tables, engine):
    page = Page(
        url="https://afrolanews.org/",
        article_exclude_reason=ArticleExcludeReason.NOT_ARTICLE,
    )

    with pytest.raises(
        AssertionError,
        match=r"Page has a non-null article_exclude_reason, so it cannot be added as an article",
    ):
        Article(
            site=AFRO_LA.name,
            id_in_site="1234",
            title="Actually a Home Page and Not an Article",
            published_at=datetime.utcnow(),
            page=page,
        )


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
        published_at=datetime.utcnow(),
        page=page1,
    )
    article2 = Article(
        site=DALLAS_FREE_PRESS.name,
        id_in_site=id_in_site,
        title="Example Article 2",
        published_at=datetime.utcnow(),
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


def test_update_article(create_and_drop_tables, engine):
    page = Page(
        url="https://dallasfreepress.com/example-article/",
        article_exclude_reason=None,
    )
    article = Article(
        site=DALLAS_FREE_PRESS.name,
        id_in_site="1234",
        title="Example Article",
        published_at=datetime.utcnow(),
        page=page,
    )

    with Session(engine) as session:
        session.add(article)
        session.commit()

        # Upon creation, db_updated_at should be None
        assert article.db_updated_at is None

        article.title = "Example Article with Title Updated"
        session.commit()

        # Upon update, db_updated_at should be set
        assert isinstance(article.db_updated_at, datetime)
