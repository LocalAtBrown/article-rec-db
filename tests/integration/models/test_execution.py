from datetime import datetime
from uuid import UUID

from sqlmodel import Session

from article_rec_db.models import Execution, StrategyRecommendationType, StrategyType


def test_add_execution(create_and_drop_tables, engine):
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
