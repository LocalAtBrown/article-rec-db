from datetime import datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from article_rec_db.models import (
    MAX_EMBEDDING_DIMENSIONS,
    Article,
    Embedding,
    Execution,
    Page,
    Recommendation,
    StrategyRecommendationType,
    StrategyType,
)
from article_rec_db.sites import DALLAS_FREE_PRESS


def test_add_article_with_page(refresh_tables, engine):
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


def test_add_article_without_page(refresh_tables, engine):
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


def test_add_articles_duplicate_site_and_id_in_site(refresh_tables, engine):
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
        session.commit()

        session.add(article2)
        # Since the combination of site and id_in_site is unique, adding an article with an already existing site and id_in_site must fail
        with pytest.raises(
            IntegrityError,
            match=r"duplicate key value violates unique constraint \"article_site_idinsite_unique\"",
        ):
            session.commit()

        # Check that only 1 article is written
        session.rollback()
        num_articles = session.exec(select(func.count(Article.page_id))).one()
        assert num_articles == 1


def test_update_article(refresh_tables, engine):
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


def test_delete_article(refresh_tables, engine):
    page_id1 = UUID(int=1)
    page_id2 = UUID(int=2)
    page1 = Page(
        id=page_id1,
        url="https://dallasfreepress.com/example-article-1/",
        article_exclude_reason=None,
    )
    page2 = Page(
        id=page_id2,
        url="https://dallasfreepress.com/example-article-2/",
        article_exclude_reason=None,
    )
    article1 = Article(
        site=DALLAS_FREE_PRESS.name,
        id_in_site="1234",
        title="Example Article 1",
        published_at=datetime.utcnow(),
        page=page1,
    )
    article2 = Article(
        site=DALLAS_FREE_PRESS.name,
        id_in_site="2345",
        title="Example Article 2",
        published_at=datetime.utcnow(),
        page=page2,
    )

    execution = Execution(
        strategy=StrategyType.SEMANTIC_SIMILARITY,
        strategy_recommendation_type=StrategyRecommendationType.SOURCE_TARGET_INTERCHANGEABLE,
    )
    embedding1 = Embedding(article=article1, execution=execution, vector=[0.1] * MAX_EMBEDDING_DIMENSIONS)
    embedding2 = Embedding(article=article2, execution=execution, vector=[0.4] * MAX_EMBEDDING_DIMENSIONS)
    recommendation = Recommendation(execution=execution, source_article=article1, target_article=article2, score=0.9)

    with Session(engine) as session:
        session.add(embedding1)
        session.add(embedding2)
        session.add(recommendation)
        session.commit()

        # Check that everything is written
        assert session.exec(select(func.count(Page.id))).one() == 2
        assert session.exec(select(func.count(Article.page_id))).one() == 2
        assert session.exec(select(func.count(Execution.id))).one() == 1
        assert session.exec(select(func.count(Embedding.id))).one() == 2
        assert session.exec(select(func.count(Recommendation.id))).one() == 1
        assert len(article2.recommendations_where_this_is_target) == 1

        # Now delete Article 1
        article1 = session.exec(select(Article).where(Article.page_id == page_id1)).unique().one()
        session.delete(article1)
        session.commit()

        # Check pages
        assert session.exec(select(func.count(Page.id))).one() == 2
        page1 = session.exec(select(Page).where(Page.id == page_id1)).one()
        assert page1.article == []

        # Check articles
        assert session.exec(select(Article).where(Article.page_id == page_id1)).one_or_none() is None
        article2 = session.exec(select(Article).where(Article.page_id == page_id2)).unique().one()
        assert article2.recommendations_where_this_is_target == []

        # Check executions
        assert session.exec(select(func.count(Execution.id))).one() == 1

        # Check embeddings
        assert session.exec(select(func.count(Embedding.id))).one() == 1
        assert session.exec(select(Embedding).where(Embedding.article_id == page_id1)).one_or_none() is None

        # Check recommendations
        assert session.exec(select(func.count(Recommendation.id))).one() == 0
