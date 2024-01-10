from datetime import datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from article_rec_db.models import Article, Embedding, Page, Recommendation, Recommender
from article_rec_db.models.article import Language
from article_rec_db.models.embedding import MAX_EMBEDDING_DIMENSIONS
from article_rec_db.models.recommender import RecommendationType


def test_add_article_with_page(site_name, refresh_tables, engine):
    # This is how we would add a page that is also an article
    page = Page(
        url="https://dallasfreepress.com/example-article/",
    )
    article_published_at = datetime.utcnow()
    article = Article(
        site=site_name,
        id_in_site="1234",
        title="Example Article",
        description="Description",
        content="<p>Content</p>",
        site_published_at=article_published_at,
        language=Language.SPANISH,
        page=page,
    )

    with Session(engine) as session:
        session.add(article)
        session.commit()

        assert isinstance(page.id, UUID)
        assert isinstance(page.db_created_at, datetime)
        assert page.url == "https://dallasfreepress.com/example-article/"
        assert page.article is article

        assert isinstance(article.db_created_at, datetime)
        assert article.db_updated_at is None
        assert article.page_id == page.id
        assert article.site == site_name
        assert article.id_in_site == "1234"
        assert article.title == "Example Article"
        assert article.description == "Description"
        assert article.content == "<p>Content</p>"
        assert article.site_published_at == article_published_at
        assert article.site_updated_at is None
        assert article.language == Language.SPANISH
        assert article.is_in_house_content is True
        assert article.page is page
        assert len(article.embeddings) == 0
        assert len(article.recommendations_where_this_is_source) == 0
        assert len(article.recommendations_where_this_is_target) == 0


def test_add_article_without_page(site_name, refresh_tables, engine):
    article = Article(
        page_id=uuid4(),
        site=site_name,
        id_in_site="2345",
        title="Example Article",
        content="<p>Content</p>",
        site_published_at=datetime.utcnow(),
    )

    with Session(engine) as session:
        session.add(article)

        # Since there's no page to refer to, adding an standalone article must fail
        with pytest.raises(
            IntegrityError,
            match=r"insert or update on table \"article\" violates foreign key constraint \"article_page_id_fkey\"",
        ):
            session.commit()

        # Check that nothing is written
        session.rollback()
        num_articles = session.exec(select(func.count(Article.page_id))).one()
        assert num_articles == 0


def test_add_articles_duplicate_site_and_id_in_site(site_name, refresh_tables, engine):
    page1 = Page(
        url="https://dallasfreepress.com/example-article/",
    )
    page2 = Page(
        url="https://dallasfreepress.com/example-article-2/",
    )
    id_in_site = "1234"
    article1 = Article(
        site=site_name,
        id_in_site=id_in_site,
        title="Example Article",
        content="<p>Content</p>",
        site_published_at=datetime.utcnow(),
        page=page1,
    )
    article2 = Article(
        site=site_name,
        id_in_site=id_in_site,
        title="Example Article 2",
        content="<p>Content</p>",
        site_published_at=datetime.utcnow(),
        page=page2,
    )

    with Session(engine) as session:
        session.add(article1)
        session.commit()

        session.add(article2)
        # Since the combination of site and id_in_site is unique, adding an article with an already existing site and id_in_site must fail
        with pytest.raises(
            IntegrityError,
            match=r"duplicate key value violates unique constraint \"article_site_idinsite_unique\"",
        ):
            session.commit()

        # Check that only 1 article is written
        session.rollback()
        num_articles = session.exec(select(func.count(Article.page_id))).one()
        assert num_articles == 1


def test_update_article(site_name, refresh_tables, engine):
    page = Page(
        url="https://dallasfreepress.com/example-article/",
    )
    article = Article(
        site=site_name,
        id_in_site="1234",
        title="Example Article",
        content="<p>Content</p>",
        site_published_at=datetime.utcnow(),
        page=page,
    )

    with Session(engine) as session:
        session.add(article)
        session.commit()

        # Upon creation, db_updated_at should be None
        assert article.db_updated_at is None

        article.title = "Example Article with Title Updated"
        site_updated_at = datetime.utcnow()
        article.site_updated_at = site_updated_at
        session.commit()

        # Upon update, db_updated_at should be set
        assert isinstance(article.db_updated_at, datetime)
        assert article.title == "Example Article with Title Updated"
        assert article.site_updated_at == site_updated_at


def test_upsert_article(site_name, refresh_tables, engine):
    page = Page(
        url="https://dallasfreepress.com/example-article/",
    )
    article_published_at = datetime.utcnow()
    article = Article(
        site=site_name,
        id_in_site="1234",
        title="Example Article",
        description="Description",
        content="<p>Content</p>",
        site_published_at=article_published_at,
        language=Language.SPANISH,
        page=page,
    )

    with Session(engine) as session:
        session.add(page)
        session.commit()

        assert page.article is article
        assert article.db_updated_at is None

    # Now, do an upsert
    article_updated_at = datetime.utcnow()
    article_updated = Article(
        site=article.site,
        id_in_site=article.id_in_site,
        title="Example Article Updated",
        description="Description Updated",
        content="<p>Content Updated</p>",
        site_published_at=article.site_published_at,
        site_updated_at=article_updated_at,
        language=article.language,
    )

    with Session(engine) as session:
        stmt = (
            insert(Article)
            .values(
                page_id=page.id,
                site=article_updated.site,
                id_in_site=article_updated.id_in_site,
                title=article_updated.title,
                description=article_updated.description,
                content=article_updated.content,
                site_published_at=article_updated.site_published_at,
                site_updated_at=article_updated.site_updated_at,
                language=article_updated.language,
                is_in_house_content=article_updated.is_in_house_content,
            )
            .on_conflict_do_update(
                index_elements=["site", "id_in_site"],
                set_={
                    "title": article_updated.title,
                    "description": article_updated.description,
                    "content": article_updated.content,
                    "site_updated_at": article_updated.site_updated_at,
                    "db_updated_at": datetime.utcnow(),
                },
            )
        )
        session.exec(stmt)
        session.commit()

        # Checks
        assert len(session.exec(select(Article)).unique().all()) == 1

        page = session.exec(select(Page).where(Page.id == page.id)).one()
        article_updated = session.exec(select(Article).where(Article.page_id == page.id)).unique().one()

        assert page.article is article_updated

        assert article_updated.db_created_at == article.db_created_at
        assert isinstance(article_updated.db_updated_at, datetime)
        assert article_updated.page_id == article_updated.page.id == page.id == article.page_id
        assert article_updated.site == site_name
        assert article_updated.id_in_site == "1234"
        assert article_updated.title == "Example Article Updated"
        assert article_updated.description == "Description Updated"
        assert article_updated.content == "<p>Content Updated</p>"
        assert article_updated.site_published_at == article_published_at
        assert article_updated.site_updated_at == article_updated_at
        assert article_updated.language == Language.SPANISH
        assert article_updated.is_in_house_content is True


def test_delete_article(site_name, refresh_tables, engine):
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
        assert len(article2.recommendations_where_this_is_target) == 1

        # Now delete Article 1
        article1 = session.exec(select(Article).where(Article.page_id == page_id1)).unique().one()
        session.delete(article1)
        session.commit()

        # Check pages
        assert session.exec(select(func.count(Page.id))).one() == 2
        page1 = session.exec(select(Page).where(Page.id == page_id1)).one()
        assert page1.article is None

        # Check articles
        assert session.exec(select(Article).where(Article.page_id == page_id1)).one_or_none() is None
        article2 = session.exec(select(Article).where(Article.page_id == page_id2)).unique().one()
        assert article2.recommendations_where_this_is_target == []

        # Check recommenders
        assert session.exec(select(func.count(Recommender.id))).one() == 1

        # Check embeddings
        assert session.exec(select(func.count(Embedding.id))).one() == 1
        assert session.exec(select(Embedding).where(Embedding.article_id == page_id1)).one_or_none() is None

        # Check recommendations
        assert session.exec(select(func.count(Recommendation.id))).one() == 0
