from datetime import datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from article_rec_db.models import Article, Embedding, Execution, Page, Recommendation
from article_rec_db.models.article import Language
from article_rec_db.models.embedding import MAX_EMBEDDING_DIMENSIONS
from article_rec_db.models.execution import RecommendationType


def test_add_article_with_page(site_name, refresh_tables, engine):
    execution = Execution(
        task_name="create_pages",
        success=False,
    )

    # This is how we would add a page that is also an article
    page = Page(
        url="https://example.com/example-article/",
        execution=execution,
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
        execution_last_updated=execution,
    )

    with Session(engine) as session:
        session.add(article)
        session.commit()

        execution.success = True
        session.commit()

        assert isinstance(page.id, UUID)
        assert isinstance(page.db_created_at, datetime)
        assert page.url == "https://example.com/example-article/"
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
        assert article.execution_last_updated is execution
        assert len(article.embeddings) == 0
        assert len(article.recommendations_where_this_is_source) == 0
        assert len(article.recommendations_where_this_is_target) == 0

        assert len(execution.pages) == 1
        assert len(execution.articles) == 1


def test_add_article_without_page(site_name, refresh_tables, engine):
    execution = Execution(
        task_name="create_pages",
        success=False,
    )
    article = Article(
        page_id=uuid4(),
        site=site_name,
        id_in_site="2345",
        title="Example Article",
        content="<p>Content</p>",
        site_published_at=datetime.utcnow(),
        execution_last_updated=execution,
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
    execution = Execution(
        task_name="create_pages",
        success=False,
    )
    page1 = Page(
        url="https://example.com/example-article/",
        execution=execution,
    )
    page2 = Page(
        url="https://example.com/example-article-2/",
    )
    id_in_site = "1234"
    article1 = Article(
        site=site_name,
        id_in_site=id_in_site,
        title="Example Article",
        content="<p>Content</p>",
        site_published_at=datetime.utcnow(),
        page=page1,
        execution_last_updated=execution,
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

        page2.execution = execution
        article2.execution_last_updated = execution
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
    execution_create_pages = Execution(task_name="create_pages", success=False)
    page = Page(
        url="https://example.com/example-article/",
        execution=execution_create_pages,
    )
    article = Article(
        site=site_name,
        id_in_site="1234",
        title="Example Article",
        content="<p>Content</p>",
        site_published_at=datetime.utcnow(),
        page=page,
        execution_last_updated=execution_create_pages,
    )

    with Session(engine) as session:
        # Create article
        session.add(article)
        session.commit()

        execution_create_pages.success = True
        session.commit()

        # Upon creation, db_updated_at should be None
        assert article.db_updated_at is None
        assert article.execution_last_updated is execution_create_pages
        assert len(execution_create_pages.articles) == 1

        # Update article
        execution_update_pages = Execution(task_name="update_pages", success=False)
        article.title = "Example Article with Title Updated"
        article.execution_last_updated = execution_update_pages
        site_updated_at = datetime.utcnow()
        article.site_updated_at = site_updated_at
        session.commit()

        # Upon update, db_updated_at should be set
        article = session.exec(select(Article)).unique().one()
        assert isinstance(article.db_updated_at, datetime)
        assert article.title == "Example Article with Title Updated"
        assert article.site_updated_at == site_updated_at
        assert article.execution_last_updated is execution_update_pages

        assert len(execution_create_pages.articles) == 0
        assert len(execution_update_pages.articles) == 1


def test_upsert_article(site_name, refresh_tables, engine):
    execution_create_pages = Execution(task_name="create_pages", success=False)
    page = Page(
        url="https://example.com/example-article/",
        execution=execution_create_pages,
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
        execution_last_updated=execution_create_pages,
    )

    with Session(engine) as session:
        session.add(page)
        session.commit()

        execution_create_pages.success = True
        session.commit()

        assert page.article is article
        assert article.db_updated_at is None
        assert article.execution_last_updated is execution_create_pages
        assert len(execution_create_pages.articles) == 1

    # Now, do an upsert
    execution_update_pages = Execution(task_name="update_pages", success=False)
    article_updated_at = datetime.utcnow()
    with Session(engine) as session:
        session.add(execution_update_pages)
        stmt = insert(Article).values(
            [
                {
                    "page_id": page.id,
                    "site": article.site,
                    "id_in_site": article.id_in_site,
                    "title": "Example Article Updated",
                    "description": "Description Updated",
                    "content": "<p>Content Updated</p>",
                    "site_published_at": article.site_published_at,
                    "site_updated_at": article_updated_at,
                    "language": article.language,
                    "is_in_house_content": article.is_in_house_content,
                    "execution_id_last_updated": execution_update_pages.id,
                }
            ]
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[Article.site, Article.id_in_site],
            set_={
                "title": stmt.excluded.title,
                "description": stmt.excluded.description,
                "content": stmt.excluded.content,
                "site_updated_at": stmt.excluded.site_updated_at,
                "db_updated_at": datetime.utcnow(),
                "execution_id_last_updated": stmt.excluded.execution_id_last_updated,
            },
        ).returning(Article)

        article = session.scalars(stmt).unique().one()
        session.commit()

        execution_update_pages.success = True
        session.commit()

        # Checks
        assert len(session.exec(select(Article)).unique().all()) == 1

        assert page.id == article.page_id

        assert isinstance(article.db_updated_at, datetime)
        assert article.title == "Example Article Updated"
        assert article.description == "Description Updated"
        assert article.content == "<p>Content Updated</p>"
        assert article.site_updated_at == article_updated_at
        assert article.execution_last_updated is execution_update_pages

        execution_create_pages = session.exec(select(Execution).where(Execution.id == execution_create_pages.id)).one()
        execution_update_pages = session.exec(select(Execution).where(Execution.id == execution_update_pages.id)).one()
        assert len(execution_create_pages.articles) == 0
        assert len(execution_update_pages.articles) == 1


def test_delete_article(site_name, refresh_tables, engine):
    execution_create_pages = Execution(task_name="create_pages", success=False)
    page_id1 = UUID(int=1)
    page_id2 = UUID(int=2)
    page1 = Page(
        id=page_id1,
        url="https://example.com/example-article-1/",
        execution=execution_create_pages,
    )
    page2 = Page(
        id=page_id2,
        url="https://example.com/example-article-2/",
        execution=execution_create_pages,
    )
    article1 = Article(
        site=site_name,
        id_in_site="1234",
        title="Example Article 1",
        content="<p>Content</p>",
        site_published_at=datetime.utcnow(),
        page=page1,
        execution_last_updated=execution_create_pages,
    )
    article2 = Article(
        site=site_name,
        id_in_site="2345",
        title="Example Article 2",
        content="<p>Content</p>",
        site_published_at=datetime.utcnow(),
        page=page2,
        execution_last_updated=execution_create_pages,
    )

    with Session(engine) as session:
        session.add(article1)
        session.add(article2)
        session.commit()

        execution_create_pages.success = True
        session.commit()

        assert len(execution_create_pages.articles) == 2

    execution_create_recommendations = Execution(
        task_name="create_recommendations",
        success=True,
        recommendation_type=RecommendationType.SOURCE_TARGET_INTERCHANGEABLE,
    )
    embedding1 = Embedding(
        article=article1, execution=execution_create_recommendations, vector=[0.1] * MAX_EMBEDDING_DIMENSIONS
    )
    embedding2 = Embedding(
        article=article2, execution=execution_create_recommendations, vector=[0.4] * MAX_EMBEDDING_DIMENSIONS
    )
    recommendation = Recommendation(
        execution=execution_create_recommendations, source_article=article1, target_article=article2, score=0.9
    )

    with Session(engine) as session:
        session.add(embedding1)
        session.add(embedding2)
        session.add(recommendation)
        session.commit()

        execution_create_recommendations.success = True
        session.commit()

        # Check that everything is written
        assert session.exec(select(func.count(Page.id))).one() == 2
        assert session.exec(select(func.count(Article.page_id))).one() == 2
        assert session.exec(select(func.count(Execution.id))).one() == 2
        assert session.exec(select(func.count(Embedding.id))).one() == 2
        assert session.exec(select(func.count(Recommendation.id))).one() == 1
        assert len(article2.recommendations_where_this_is_target) == 1

        # Now delete Article 1
        execution_delete_articles = Execution(task_name="delete_articles", success=False)
        article1 = session.exec(select(Article).where(Article.page_id == page_id1)).unique().one()
        session.delete(article1)
        session.add(execution_delete_articles)
        session.commit()

        execution_delete_articles.success = True
        session.commit()

        # Check pages
        assert session.exec(select(func.count(Page.id))).one() == 2
        page1 = session.exec(select(Page).where(Page.id == page_id1)).one()
        assert page1.article is None

        # Check articles
        assert session.exec(select(Article).where(Article.page_id == page_id1)).one_or_none() is None
        article2 = session.exec(select(Article).where(Article.page_id == page_id2)).unique().one()
        assert article2.recommendations_where_this_is_target == []

        # Check executions
        assert session.exec(select(func.count(Execution.id))).one() == 3
        execution_create_pages = session.exec(select(Execution).where(Execution.id == execution_create_pages.id)).one()
        assert len(execution_create_pages.articles) == 1

        # Check embeddings
        assert session.exec(select(func.count(Embedding.id))).one() == 1
        assert session.exec(select(Embedding).where(Embedding.article_id == page_id1)).one_or_none() is None

        # Check recommendations
        assert session.exec(select(func.count(Recommendation.id))).one() == 0
