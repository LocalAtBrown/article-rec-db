from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from article_rec_db.models import Article, Embedding, Execution, Page, Recommendation
from article_rec_db.models.embedding import MAX_EMBEDDING_DIMENSIONS
from article_rec_db.models.execution import StrategyRecommendationType, StrategyType


def test_add_page_not_article(refresh_tables, engine):
    page = Page(
        url="https://afrolanews.org/",  # Home page, so not an article
    )
    with Session(engine) as session:
        session.add(page)
        session.commit()

        assert isinstance(page.id, UUID)
        assert isinstance(page.db_created_at, datetime)
        assert page.db_updated_at is None
        assert page.url == "https://afrolanews.org/"
        assert page.article is None


def test_add_pages_duplicate_url(refresh_tables, engine):
    page1 = Page(
        url="https://dallasfreepress.com/example-article/",
    )
    page2 = Page(
        url="https://dallasfreepress.com/example-article/",
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


def test_update_page(refresh_tables, engine):
    page = Page(
        url="https://dallasfreepress.com/example-article/",
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


def test_delete_page(site_name, refresh_tables, engine):
    page_id1 = UUID(int=1)
    page_id2 = UUID(int=2)
    page1 = Page(
        id=page_id1,
        url="https://dallasfreepress.com/example-article-1/",
    )
    page2 = Page(
        id=page_id2,
        url="https://dallasfreepress.com/example-article-2/",
    )
    article1 = Article(
        site=site_name,
        id_in_site="1234",
        title="Example Article 1",
        content="<p>Content</p>",
        site_published_at=datetime.utcnow(),
        page=page1,
    )
    article2 = Article(
        site=site_name,
        id_in_site="2345",
        title="Example Article 2",
        content="<p>Content</p>",
        site_published_at=datetime.utcnow(),
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

        # Now delete Page 1
        page1 = session.exec(select(Page).where(Page.id == page_id1)).one()
        session.delete(page1)
        session.commit()

        # Check pages
        assert session.exec(select(func.count(Page.id))).one() == 1
        session.exec(select(Page).where(Page.id == page_id1)).one_or_none() is None

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
