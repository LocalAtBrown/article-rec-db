from datetime import datetime
from uuid import UUID

from sqlmodel import Session, func, select

from article_rec_db.models import Article, Embedding, Page, Recommendation, Recommender
from article_rec_db.models.embedding import MAX_EMBEDDING_DIMENSIONS
from article_rec_db.models.recommender import RecommendationType


def test_add_recommender(refresh_tables, engine):
    recommender = Recommender(
        strategy="example-strategy",
        recommendation_type=RecommendationType.SOURCE_TARGET_INTERCHANGEABLE,
    )

    with Session(engine) as session:
        session.add(recommender)
        session.commit()

        assert isinstance(recommender.id, UUID)
        assert recommender.strategy == "example-strategy"
        assert isinstance(recommender.db_created_at, datetime)
        assert len(recommender.embeddings) == 0
        assert len(recommender.recommendations) == 0


def test_delete_recommender(site_name, refresh_tables, engine):
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
        site=site_name,
        id_in_site="1234",
        title="Example Article 1",
        content="<p>Content</p>",
        site_published_at=datetime.utcnow(),
        page=page1,
    )
    article2 = Article(
        site=site_name,
        id_in_site="2345",
        title="Example Article 2",
        content="<p>Content</p>",
        site_published_at=datetime.utcnow(),
        page=page2,
    )

    recommender = Recommender(
        strategy="example-strategy",
        recommendation_type=RecommendationType.SOURCE_TARGET_INTERCHANGEABLE,
    )
    embedding1 = Embedding(article=article1, recommender=recommender, vector=[0.1] * MAX_EMBEDDING_DIMENSIONS)
    embedding2 = Embedding(article=article2, recommender=recommender, vector=[0.4] * MAX_EMBEDDING_DIMENSIONS)
    recommendation = Recommendation(recommender=recommender, source_article=article1, target_article=article2, score=0.9)

    with Session(engine) as session:
        session.add(embedding1)
        session.add(embedding2)
        session.add(recommendation)
        session.commit()

        # Check that everything is written
        assert session.exec(select(func.count(Page.id))).one() == 2
        assert session.exec(select(func.count(Article.page_id))).one() == 2
        assert session.exec(select(func.count(Recommender.id))).one() == 1
        assert session.exec(select(func.count(Embedding.id))).one() == 2
        assert session.exec(select(func.count(Recommendation.id))).one() == 1
        assert len(article1.embeddings) == 1
        assert len(article2.embeddings) == 1
        assert len(article1.recommendations_where_this_is_source) == 1
        assert len(article2.recommendations_where_this_is_target) == 1

        # Now delete recommender
        recommender_id = recommender.id
        recommender = session.exec(select(Recommender).where(Recommender.id == recommender_id)).one()
        session.delete(recommender)
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

        # Check recommenders
        assert session.exec(select(func.count(Recommender.id))).one() == 0

        # Check embeddings
        assert session.exec(select(func.count(Embedding.id))).one() == 0

        # Check recommendations
        assert session.exec(select(func.count(Recommendation.id))).one() == 0
