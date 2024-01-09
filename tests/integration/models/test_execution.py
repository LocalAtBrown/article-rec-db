from datetime import datetime
from uuid import UUID

from sqlmodel import Session, func, select

from article_rec_db.models import Article, Embedding, Execution, Page, Recommendation
from article_rec_db.models.embedding import MAX_EMBEDDING_DIMENSIONS
from article_rec_db.models.execution import RecommendationType


def test_add_execution(refresh_tables, engine):
    execution = Execution(
        task_name="create_recommendations",
        success=True,
        recommendation_type=RecommendationType.SOURCE_TARGET_INTERCHANGEABLE,
    )

    with Session(engine) as session:
        session.add(execution)
        session.commit()

        assert isinstance(execution.id, UUID)
        assert execution.task_name == "create_recommendations"
        assert execution.success is True
        assert execution.recommendation_type == RecommendationType.SOURCE_TARGET_INTERCHANGEABLE
        assert isinstance(execution.db_created_at, datetime)
        assert len(execution.pages) == 0
        assert len(execution.articles) == 0
        assert len(execution.embeddings) == 0
        assert len(execution.recommendations) == 0


def test_update_execution(refresh_tables, engine):
    execution = Execution(
        task_name="create_recommendations",
        success=True,
        recommendation_type=RecommendationType.SOURCE_TARGET_INTERCHANGEABLE,
    )

    with Session(engine) as session:
        session.add(execution)
        session.commit()

        # Update status
        execution.success = False
        session.commit()

    with Session(engine) as session:
        execution = session.exec(select(Execution)).one()
        assert execution.success is False


def test_delete_execution(site_name, refresh_tables, engine):
    # Add pages and articles
    execution_create_pages = Execution(task_name="create_pages", success=False)
    page_id1 = UUID(int=1)
    page_id2 = UUID(int=2)
    page1 = Page(
        id=page_id1,
        url="https://example.com/example-article-1/",
        execution=execution_create_pages,
    )
    page2 = Page(
        id=page_id2,
        url="https://example.com/example-article-2/",
        execution=execution_create_pages,
    )
    article1 = Article(
        site=site_name,
        id_in_site="1234",
        title="Example Article 1",
        content="<p>Content</p>",
        site_published_at=datetime.utcnow(),
        page=page1,
        execution_last_updated=execution_create_pages,
    )
    article2 = Article(
        site=site_name,
        id_in_site="2345",
        title="Example Article 2",
        content="<p>Content</p>",
        site_published_at=datetime.utcnow(),
        page=page2,
        execution_last_updated=execution_create_pages,
    )
    with Session(engine) as session:
        session.add(article1)
        session.add(article2)
        session.commit()

        execution_create_pages.success = True
        session.commit()

    execution_create_recommendations = Execution(
        task_name="create_recommendations",
        success=False,
        recommendation_type=RecommendationType.SOURCE_TARGET_INTERCHANGEABLE,
    )
    embedding1 = Embedding(
        article=article1, execution=execution_create_recommendations, vector=[0.1] * MAX_EMBEDDING_DIMENSIONS
    )
    embedding2 = Embedding(
        article=article2, execution=execution_create_recommendations, vector=[0.4] * MAX_EMBEDDING_DIMENSIONS
    )
    recommendation = Recommendation(
        execution=execution_create_recommendations, source_article=article1, target_article=article2, score=0.9
    )
    with Session(engine) as session:
        session.add(embedding1)
        session.add(embedding2)
        session.add(recommendation)
        session.commit()

        execution_create_recommendations.success = True
        session.commit()

        # Check that everything is written
        assert session.exec(select(func.count(Page.id))).one() == 2
        assert session.exec(select(func.count(Article.page_id))).one() == 2
        assert session.exec(select(func.count(Execution.id))).one() == 2
        assert session.exec(select(func.count(Embedding.id))).one() == 2
        assert session.exec(select(func.count(Recommendation.id))).one() == 1
        assert len(article1.embeddings) == 1
        assert len(article2.embeddings) == 1
        assert len(article1.recommendations_where_this_is_source) == 1
        assert len(article2.recommendations_where_this_is_target) == 1

        execution_id_to_delete = execution_create_recommendations.id

    # Now, delete second execution
    with Session(engine) as session:
        execution = session.exec(select(Execution).where(Execution.id == execution_id_to_delete)).one()
        session.delete(execution)
        session.commit()

        # Check pages
        assert session.exec(select(func.count(Page.id))).one() == 2

        # Check articles
        article1 = session.exec(select(Article).where(Article.page_id == page_id1)).unique().one()
        article2 = session.exec(select(Article).where(Article.page_id == page_id2)).unique().one()
        assert article1.embeddings == []
        assert article2.embeddings == []
        assert article1.recommendations_where_this_is_source == []
        assert article2.recommendations_where_this_is_target == []

        # Check executions
        assert session.exec(select(func.count(Execution.id))).one() == 1

        # Check embeddings
        assert session.exec(select(func.count(Embedding.id))).one() == 0

        # Check recommendations
        assert session.exec(select(func.count(Recommendation.id))).one() == 0
