from datetime import datetime
from uuid import UUID

import pytest
from sqlmodel import Session

from article_rec_db.models import Execution, StrategyType


@pytest.mark.order(10)
def test_add_execution(create_and_drop_tables, engine):
    execution = Execution(strategy=StrategyType.SEMANTIC_SIMILARITY)

    with Session(engine) as session:
        session.add(execution)
        session.commit()
        session.refresh(execution)

        assert isinstance(execution.id, UUID)
        assert execution.strategy == StrategyType.SEMANTIC_SIMILARITY
        assert isinstance(execution.db_created_at, datetime)
        assert len(execution.embeddings) == 0
