from datetime import datetime
from uuid import UUID

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


def test_add_default_recommendation(refresh_tables, engine):
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
    execution = Execution(
        strategy=StrategyType.POPULARITY, strategy_recommendation_type=StrategyRecommendationType.DEFAULT_AKA_NO_SOURCE
    )
    recommendation = Recommendation(execution=execution, target_article=article, score=0.8)

    with Session(engine) as session:
        session.add(recommendation)
        session.commit()

        assert len(article.recommendations_where_this_is_source) == 0
        assert len(article.recommendations_where_this_is_target) == 1
        assert article.recommendations_where_this_is_target[0] is recommendation

        assert len(execution.recommendations) == 1
        assert execution.recommendations[0] is recommendation

        assert isinstance(recommendation.id, UUID)
        assert isinstance(recommendation.db_created_at, datetime)
        assert recommendation.execution_id == execution.id
        assert recommendation.source_article_id is None
        assert recommendation.target_article_id == article.page_id
        assert recommendation.score == 0.8
        assert recommendation.execution is execution
        assert recommendation.source_article is None
        assert recommendation.target_article is article


def test_add_default_recommendation_with_nonnull_source_id(refresh_tables, engine):
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
    execution = Execution(
        strategy=StrategyType.POPULARITY, strategy_recommendation_type=StrategyRecommendationType.DEFAULT_AKA_NO_SOURCE
    )
    recommendation = Recommendation(execution=execution, source_article=article, target_article=article, score=1)

    with Session(engine) as session:
        session.add(recommendation)

        with pytest.raises(
            AssertionError,
            match=r"Source article ID must be empty when execution strategy's recommendation type is default",
        ):
            session.commit()

        # Check that nothing is written
        session.rollback()
        num_recommendations = session.exec(select(func.count(Recommendation.id))).one()
        assert num_recommendations == 0


def test_add_recommendation_source_target_interchangeable(refresh_tables, engine):
    page1 = Page(
        id=UUID(int=1),  # smaller ID
        url="https://dallasfreepress.com/example-article-1/",
        article_exclude_reason=None,
    )
    page2 = Page(
        id=UUID(int=2),  # larger ID
        url="https://dallasfreepress.com/example-article-2/",
        article_exclude_reason=None,
    )

    article1 = Article(
        site=DALLAS_FREE_PRESS.name,
        id_in_site="1234",
        title="Example Article",
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

    # Article 1 has a lower ID than article 2, so this is correct
    recommendation = Recommendation(execution=execution, source_article=article1, target_article=article2, score=0.9)

    with Session(engine) as session:
        session.add(recommendation)
        session.commit()

        assert len(article1.recommendations_where_this_is_source) == 1
        assert article1.recommendations_where_this_is_source[0] is recommendation
        assert len(article1.recommendations_where_this_is_target) == 0

        assert len(article2.recommendations_where_this_is_source) == 0
        assert len(article2.recommendations_where_this_is_target) == 1
        assert article2.recommendations_where_this_is_target[0] is recommendation

        assert len(execution.recommendations) == 1
        assert execution.recommendations[0] is recommendation

        assert isinstance(recommendation.id, UUID)
        assert isinstance(recommendation.db_created_at, datetime)
        assert recommendation.execution_id == execution.id
        assert recommendation.source_article_id == article1.page_id
        assert recommendation.target_article_id == article2.page_id
        assert recommendation.score == 0.9
        assert recommendation.execution is execution
        assert recommendation.source_article is article1
        assert recommendation.target_article is article2

        # Check that recommendation is not recorded twice in the table
        assert session.query(func.count("*")).select_from(Recommendation).scalar() == 1


def test_add_recommendation_source_target_interchangeable_no_source(refresh_tables, engine):
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

    execution = Execution(
        strategy=StrategyType.SEMANTIC_SIMILARITY,
        strategy_recommendation_type=StrategyRecommendationType.SOURCE_TARGET_INTERCHANGEABLE,
    )
    recommendation = Recommendation(execution=execution, target_article=article, score=0.9)

    with Session(engine) as session:
        session.add(recommendation)

        with pytest.raises(
            AssertionError,
            match=r"Source article ID must be non-null when source and target are interchangeable.",
        ):
            session.commit()

        # Check that nothing is written
        session.rollback()
        num_recommendations = session.exec(select(func.count(Recommendation.id))).one()
        assert num_recommendations == 0


def test_add_recommendation_source_target_interchangeable_wrong_order_recommendation_side(refresh_tables, engine):
    page1 = Page(
        id=UUID(int=1),  # smaller ID
        url="https://dallasfreepress.com/example-article-1/",
        article_exclude_reason=None,
    )
    page2 = Page(
        id=UUID(int=2),  # larger ID
        url="https://dallasfreepress.com/example-article-2/",
        article_exclude_reason=None,
    )

    article1 = Article(
        site=DALLAS_FREE_PRESS.name,
        id_in_site="1234",
        title="Example Article",
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
    # Article 2 has a larger ID than article 1, so this is incorrect
    recommendation = Recommendation(execution=execution, source_article=article2, target_article=article1, score=0.9)

    with Session(engine) as session:
        session.add(recommendation)

        with pytest.raises(
            AssertionError,
            match=r"Source article ID must be lower than target article ID when source and target are interchangeable.",
        ):
            session.commit()

        # Check that nothing is written
        session.rollback()
        num_recommendations = session.exec(select(func.count(Recommendation.id))).one()
        assert num_recommendations == 0


def test_add_recommendation_source_target_interchangeable_wrong_order_article_side(refresh_tables, engine):
    page1 = Page(
        id=UUID(int=1),  # smaller ID
        url="https://dallasfreepress.com/example-article-1/",
        article_exclude_reason=None,
    )
    page2 = Page(
        id=UUID(int=2),  # larger ID
        url="https://dallasfreepress.com/example-article-2/",
        article_exclude_reason=None,
    )

    article1 = Article(
        site=DALLAS_FREE_PRESS.name,
        id_in_site="1234",
        title="Example Article",
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
    recommendation = Recommendation(execution=execution, score=0.9)
    # Article 2 has a larger ID than article 1, so this is incorrect
    article1.recommendations_where_this_is_target.append(recommendation)
    article2.recommendations_where_this_is_source.append(recommendation)

    with Session(engine) as session:
        session.add(recommendation)

        with pytest.raises(
            AssertionError,
            match=r"Source article ID must be lower than target article ID when source and target are interchangeable.",
        ):
            session.commit()

        # Check that nothing is written
        session.rollback()
        num_recommendations = session.exec(select(func.count(Recommendation.id))).one()
        assert num_recommendations == 0


def test_add_recommendation_invalid_score(refresh_tables, engine):
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
    execution = Execution(
        strategy=StrategyType.POPULARITY, strategy_recommendation_type=StrategyRecommendationType.DEFAULT_AKA_NO_SOURCE
    )
    recommendation = Recommendation(execution=execution, target_article=article, score=1.1)

    with Session(engine) as session:
        session.add(recommendation)

        with pytest.raises(IntegrityError, match=r"violates check constraint \"score_between_0_and_1\""):
            session.commit()

        # Check that nothing is written
        session.rollback()
        num_recommendations = session.exec(select(func.count(Recommendation.id))).one()
        assert num_recommendations == 0


def test_add_recommendations_duplicate(refresh_tables, engine):
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
    execution = Execution(
        strategy=StrategyType.POPULARITY,
        strategy_recommendation_type=StrategyRecommendationType.DEFAULT_AKA_NO_SOURCE,
    )
    recommendation1 = Recommendation(execution=execution, target_article=article, score=0.8)
    recommendation2 = Recommendation(execution=execution, target_article=article, score=0.8)

    with Session(engine) as session:
        session.add(recommendation1)
        session.add(recommendation2)

        # Since the combination of execution and target_article is unique, adding a recommendation with an already existing execution and target_article must fail
        with pytest.raises(
            IntegrityError,
            match=r"duplicate key value violates unique constraint \"recommendation_execution_target_unique\"",
        ):
            session.commit()

        # Check that only recommendation 1 is written
        session.rollback()
        num_recommendations = session.exec(select(func.count(Recommendation.id))).one()
        assert num_recommendations == 0


def test_delete_recommendation(refresh_tables, engine):
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
        assert len(article1.recommendations_where_this_is_source) == 1
        assert len(article2.recommendations_where_this_is_target) == 1

        # Now delete Recommendation 1
        recommendation_id = recommendation.id
        recommendation = session.exec(select(Recommendation).where(Recommendation.id == recommendation_id)).one()
        session.delete(recommendation)
        session.commit()

        # Check pages
        assert session.exec(select(func.count(Page.id))).one() == 2

        # Check articles
        assert session.exec(select(func.count(Article.page_id))).one() == 2
        assert article1.recommendations_where_this_is_source == []
        assert article2.recommendations_where_this_is_target == []

        # Check executions
        assert session.exec(select(func.count(Execution.id))).one() == 1

        # Check embeddings
        assert session.exec(select(func.count(Embedding.id))).one() == 2

        # Check recommendations
        assert session.exec(select(func.count(Recommendation.id))).one() == 0
