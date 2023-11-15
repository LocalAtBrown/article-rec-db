from datetime import datetime
from uuid import UUID

from sqlmodel import Session

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
    execution = Execution(strategy=StrategyType.POPULARITY)
    recommendation = Recommendation(execution=execution, target_article=article)

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
        assert recommendation.execution is execution
        assert recommendation.source_article is None
        assert recommendation.target_article is article
