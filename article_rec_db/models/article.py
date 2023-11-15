from datetime import datetime
from typing import Annotated
from uuid import UUID

from sqlalchemy.orm import validates as sa_validates
from sqlmodel import Column, Field, Relationship, String, UniqueConstraint

from article_rec_db.sites import SiteName

from .base import SQLModel, UpdateTracked
from .page import Page


class Article(SQLModel, UpdateTracked, table=True):
    __table_args__ = (UniqueConstraint("site", "id_in_site"),)

    page_id: Annotated[UUID, Field(primary_key=True, foreign_key="page.id")]
    site: Annotated[SiteName, Field(sa_column=Column(String))]
    id_in_site: str  # ID of article in the partner site's internal system
    title: str
    published_at: datetime

    # An article is always a page, but a page is not always an article
    page: Page = Relationship(back_populates="article")

    # An article can have zero or more embeddings
    embeddings: list["Embedding"] = Relationship(back_populates="article")  # type: ignore

    # An article can be the target of one or more default recommendations, and the source of zero or more recommendations
    # Typically, it's advised to combine these two lists to get to a final list of recommendations w.r.t. to an article, especially
    # in cases where rec A -> B is the same as rec B -> A (e.g., semantic similarity) but we only record one of these two to save space
    # The sa_relationship_kwargs is here to avert the AmbiguousForeignKeyError, see: https://github.com/tiangolo/sqlmodel/issues/10#issuecomment-1537445078
    recommendations_where_this_is_source: list["Recommendation"] = Relationship(  # type: ignore
        back_populates="source_article",
        sa_relationship_kwargs={"primaryjoin": "Recommendation.source_article_id==Article.page_id", "lazy": "joined"},
    )
    recommendations_where_this_is_target: list["Recommendation"] = Relationship(  # type: ignore
        back_populates="target_article",
        sa_relationship_kwargs={"primaryjoin": "Recommendation.target_article_id==Article.page_id", "lazy": "joined"},
    )

    @sa_validates("page")  # type: ignore
    def page_is_not_excluded(self, key: str, page: Page) -> Page:
        assert (
            page.article_exclude_reason is None
        ), "Page has a non-null article_exclude_reason, so it cannot be added as an article"
        return page
