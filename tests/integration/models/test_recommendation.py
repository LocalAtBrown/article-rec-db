from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from article_rec_db.models import Article, Execution, Page, Recommendation, StrategyType
from article_rec_db.sites import DALLAS_FREE_PRESS


def test_add_default_recommendation(create_and_drop_tables, engine):
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
    execution = Execution(strategy=StrategyType.POPULARITY, recommendation_source_target_interchangeable=False)
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


def test_add_default_recommendation_with_nonnull_source_id(create_and_drop_tables, engine):
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
    execution = Execution(strategy=StrategyType.POPULARITY, recommendation_source_target_interchangeable=False)
    recommendation = Recommendation(execution=execution, source_article=article, target_article=article, score=1)

    with Session(engine) as session:
        session.add(recommendation)

        with pytest.raises(
            AssertionError,
            match=r"Source article ID must be empty when execution strategy is in the list of default strategies",
        ):
            session.commit()

        # Check that nothing is written
        session.rollback()
        num_recommendations = session.exec(select(func.count(Recommendation.id))).one()
        assert num_recommendations == 0


def test_add_recommendation_source_target_interchangeable(create_and_drop_tables, engine):
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

    execution = Execution(strategy=StrategyType.SEMANTIC_SIMILARITY, recommendation_source_target_interchangeable=True)

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


def test_add_recommendation_source_target_interchangeable_no_source(create_and_drop_tables, engine):
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

    execution = Execution(strategy=StrategyType.SEMANTIC_SIMILARITY, recommendation_source_target_interchangeable=True)
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


def test_add_recommendation_source_target_interchangeable_wrong_order_recommendation_side(create_and_drop_tables, engine):
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

    execution = Execution(strategy=StrategyType.SEMANTIC_SIMILARITY, recommendation_source_target_interchangeable=True)
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


def test_add_recommendation_source_target_interchangeable_wrong_order_article_side(create_and_drop_tables, engine):
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

    execution = Execution(strategy=StrategyType.SEMANTIC_SIMILARITY, recommendation_source_target_interchangeable=True)
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


def test_add_recommendation_invalid_score(create_and_drop_tables, engine):
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
    execution = Execution(strategy=StrategyType.POPULARITY, recommendation_source_target_interchangeable=False)
    recommendation = Recommendation(execution=execution, target_article=article, score=1.1)

    with Session(engine) as session:
        session.add(recommendation)

        with pytest.raises(IntegrityError, match=r"violates check constraint \"score_between_0_and_1\""):
            session.commit()

        # Check that nothing is written
        session.rollback()
        num_recommendations = session.exec(select(func.count(Recommendation.id))).one()
        assert num_recommendations == 0


def test_add_recommendations_duplicate(create_and_drop_tables, engine):
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
    execution = Execution(strategy=StrategyType.POPULARITY, recommendation_source_target_interchangeable=False)
    recommendation1 = Recommendation(execution=execution, target_article=article, score=0.8)
    recommendation2 = Recommendation(execution=execution, target_article=article, score=0.8)

    with Session(engine) as session:
        session.add(recommendation1)
        session.add(recommendation2)

        # Since the combination of execution and target_article is unique, adding a recommendation with an already existing execution and target_article must fail
        with pytest.raises(
            IntegrityError,
            match=r"duplicate key value violates unique constraint \"recommendation_execution_id_target_article_id_key\"",
        ):
            session.commit()

        # Check that only recommendation 1 is written
        session.rollback()
        num_recommendations = session.exec(select(func.count(Recommendation.id))).one()
        assert num_recommendations == 0
