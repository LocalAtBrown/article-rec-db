from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func

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
    execution = Execution(strategy=StrategyType.POPULARITY, recommendation_source_target_interchangeable=True)
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


def test_add_recommendation_source_target_interchangeable(create_and_drop_tables, engine):
    page1 = Page(
        id=UUID(int=1),
        url="https://dallasfreepress.com/example-article-1/",
        article_exclude_reason=None,
    )
    page2 = Page(
        id=UUID(int=2),
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

    # # If source and target are interchangeable, then the source article ID must be lower than the target article ID
    # # no matter which argument among (execution, source_article, target_article) is passed last
    # error_message = r"Source article ID must be lower than target article ID when source and target are interchangeable."
    # with pytest.raises(AssertionError, match=error_message):
    #     recommendation = Recommendation(execution=execution, source_article=article2, target_article=article1, score=0.9)

    # with pytest.raises(AssertionError, match=error_message):
    #     recommendation = Recommendation(target_article=article1, execution=execution, source_article=article2, score=0.9)

    # with pytest.raises(AssertionError, match=error_message):
    #     recommendation = Recommendation(source_article=article2, target_article=article1, execution=execution, score=0.9)

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
    execution = Execution(strategy=StrategyType.SEMANTIC_SIMILARITY, recommendation_source_target_interchangeable=True)
    recommendation = Recommendation(execution=execution, target_article=article, score=1.1)

    with Session(engine) as session:
        session.add(recommendation)
        with pytest.raises(IntegrityError, match=r"violates check constraint \"score_between_0_and_1\""):
            session.commit()


# Cross-table checks:
# - execution strategy is popularity if and only if source_article is None
# - when execution strategy has source-target interchangability, source_article_id < target_article_id


def test_add_recommendations_duplicate(create_and_drop_tables, engine):
    pass
