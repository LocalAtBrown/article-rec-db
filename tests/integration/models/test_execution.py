from datetime import datetime
from uuid import UUID

from sqlmodel import Session, func, select

from article_rec_db.models import Article, Embedding, Execution, Page, Recommendation
from article_rec_db.models.embedding import MAX_EMBEDDING_DIMENSIONS
from article_rec_db.models.execution import StrategyRecommendationType, StrategyType
from article_rec_db.sites import DALLAS_FREE_PRESS


def test_add_execution(refresh_tables, engine):
    execution = Execution(
        strategy=StrategyType.SEMANTIC_SIMILARITY,
        strategy_recommendation_type=StrategyRecommendationType.SOURCE_TARGET_INTERCHANGEABLE,
    )

    with Session(engine) as session:
        session.add(execution)
        session.commit()

        assert isinstance(execution.id, UUID)
        assert execution.strategy == StrategyType.SEMANTIC_SIMILARITY
        assert isinstance(execution.db_created_at, datetime)
        assert len(execution.embeddings) == 0
        assert len(execution.recommendations) == 0


def test_delete_execution(refresh_tables, engine):
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
        assert len(article1.embeddings) == 1
        assert len(article2.embeddings) == 1
        assert len(article1.recommendations_where_this_is_source) == 1
        assert len(article2.recommendations_where_this_is_target) == 1

        # Now delete execution
        execution_id = execution.id
        execution = session.exec(select(Execution).where(Execution.id == execution_id)).one()
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
        assert session.exec(select(func.count(Execution.id))).one() == 0

        # Check embeddings
        assert session.exec(select(func.count(Embedding.id))).one() == 0

        # Check recommendations
        assert session.exec(select(func.count(Recommendation.id))).one() == 0
