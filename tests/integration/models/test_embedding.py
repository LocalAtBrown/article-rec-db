from datetime import datetime

import numpy as np
import pytest
from sqlmodel import Session

from article_rec_db.models import (
    MAX_EMBEDDING_DIMENSIONS,
    Article,
    Embedding,
    Execution,
    Page,
    StrategyType,
)
from article_rec_db.sites import DALLAS_FREE_PRESS


@pytest.mark.order(11)
def test_add_embedding(create_and_drop_tables, engine):
    page = Page(
        url="https://dallasfreepress.com/example-article/",
        article_exclude_reason=None,
    )
    article = Article(
        site=DALLAS_FREE_PRESS.name,
        id_in_site="1234",
        title="Example Article",
        published_at=datetime.now(),
        page=page,
    )
    execution = Execution(strategy=StrategyType.COLLABORATIVE_FILTERING_ITEM_BASED)
    embedding_vector = np.random.rand(MAX_EMBEDDING_DIMENSIONS).tolist()
    embedding = Embedding(
        article=article,
        execution=execution,
        vector=embedding_vector,
    )

    with Session(engine) as session:
        session.add(embedding)
        session.commit()
        session.refresh(embedding)

        assert len(article.embeddings) == 1
        assert article.embeddings[0] is embedding

        assert len(execution.embeddings) == 1
        assert execution.embeddings[0] is embedding

        assert isinstance(embedding.db_created_at, datetime)
        assert embedding.article_id == article.page_id
        assert embedding.execution_id == execution.id
        assert np.isclose(embedding.vector, embedding_vector).all()
        assert embedding.article is article
        assert embedding.execution is execution
