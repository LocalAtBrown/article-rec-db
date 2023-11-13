from datetime import datetime

import numpy as np
import pytest
from sqlmodel import Session, select

from article_rec_db.models import (
    MAX_EMBEDDING_DIMENSIONS,
    Article,
    Embedding,
    Execution,
    Page,
    StrategyType,
)
from article_rec_db.sites import DALLAS_FREE_PRESS


@pytest.fixture(scope="module")
def rng() -> np.random.Generator:
    return np.random.default_rng(42)


@pytest.mark.order(8)
def test_add_embedding(create_and_drop_tables, engine, rng):
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
    embedding_vector = rng.uniform(size=MAX_EMBEDDING_DIMENSIONS).tolist()
    embedding = Embedding(
        article=article,
        execution=execution,
        vector=embedding_vector,
    )

    with Session(engine) as session:
        session.add(embedding)
        session.commit()

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


@pytest.mark.order(9)
def test_select_embeddings_knn(create_and_drop_tables, engine, rng):
    page1 = Page(
        url="https://dallasfreepress.com/example-article/",
        article_exclude_reason=None,
    )
    page2 = Page(
        url="https://dallasfreepress.com/example-article-2/",
        article_exclude_reason=None,
    )
    page3 = Page(
        url="https://dallasfreepress.com/example-article-3/",
        article_exclude_reason=None,
    )
    article1 = Article(
        site=DALLAS_FREE_PRESS.name,
        id_in_site="1234",
        title="Example Article",
        published_at=datetime.now(),
        page=page1,
    )
    article2 = Article(
        site=DALLAS_FREE_PRESS.name,
        id_in_site="2345",
        title="Example Article 2",
        published_at=datetime.now(),
        page=page2,
    )
    article3 = Article(
        site=DALLAS_FREE_PRESS.name,
        id_in_site="3456",
        title="Example Article 3",
        published_at=datetime.now(),
        page=page3,
    )
    execution = Execution(strategy=StrategyType.SEMANTIC_SIMILARITY)

    vector1 = rng.uniform(low=0, high=0.5, size=MAX_EMBEDDING_DIMENSIONS)
    vector2 = vector1 * 2  # cosine similarity to vector1 should be 1
    vector3 = 1 - vector1  # cosine similarity to vector1 should be less than 1

    embedding1 = Embedding(
        article=article1,
        execution=execution,
        vector=vector1.tolist(),
    )
    embedding2 = Embedding(
        article=article2,
        execution=execution,
        vector=vector2.tolist(),
    )
    embedding3 = Embedding(
        article=article3,
        execution=execution,
        vector=vector3.tolist(),
    )
    similarity_13 = (
        vector1.dot(vector3) / np.linalg.norm(vector1) / np.linalg.norm(vector3)
    )  # cosine similarity between 1 and 3

    with Session(engine) as session:
        session.add_all([embedding1, embedding2, embedding3])
        session.commit()

        # Query for nearest neighbors of article1 with cosine similarity score, then order by descending score
        similarity = (1 - Embedding.vector.cosine_distance(embedding1.vector)).label("similarity")
        statement = (
            select(Embedding.id, similarity)
            .where((Embedding.execution_id == execution.id) & (Embedding.id != embedding1.id))
            .order_by(similarity.desc())
        )
        results = session.exec(statement).all()

        assert len(results) == 2
        # Top result is article 2
        assert results[0][0] == embedding2.id
        assert np.isclose(results[0][1], 1).all()
        # Bottom result is article 3
        assert results[1][0] == embedding3.id
        assert np.isclose(results[1][1], similarity_13).all()
