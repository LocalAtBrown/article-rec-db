from datetime import datetime
from typing import Annotated
from uuid import UUID

from sqlmodel import Column, Field, Relationship, String, UniqueConstraint

from article_rec_db.sites import SiteName

from .helpers import SQLModel, UpdateTracked
from .page import Page


class Article(SQLModel, UpdateTracked, table=True):
    __table_args__ = (UniqueConstraint("site", "id_in_site", name="article_site_idinsite_unique"),)

    page_id: Annotated[UUID, Field(primary_key=True, foreign_key="page.id")]
    site: Annotated[SiteName, Field(sa_column=Column(String))]
    id_in_site: str  # ID of article in the partner site's internal system
    title: str
    published_at: datetime

    is_in_house_content: bool = True

    # An article is always a page, but a page is not always an article
    page: Page = Relationship(back_populates="article")

    # An article can have zero or more embeddings
    embeddings: list["Embedding"] = Relationship(  # type: ignore
        back_populates="article",
        sa_relationship_kwargs={
            # If an article is deleted, delete all embeddings associated with it. If an embedding is disassociated from this article, delete it
            "cascade": "all, delete-orphan"
        },
    )

    # An article can be the target of one or more default recommendations, and the source of zero or more recommendations
    # Typically, it's advised to combine these two lists to get to a final list of recommendations w.r.t. to an article, especially
    # in cases where rec A -> B is the same as rec B -> A (e.g., semantic similarity) but we only record one of these two to save space
    # The sa_relationship_kwargs is here to avert the AmbiguousForeignKeyError, see: https://github.com/tiangolo/sqlmodel/issues/10#issuecomment-1537445078
    recommendations_where_this_is_source: list["Recommendation"] = Relationship(  # type: ignore
        back_populates="source_article",
        sa_relationship_kwargs={
            "primaryjoin": "Recommendation.source_article_id==Article.page_id",
            # If an article is deleted, delete all recommendations where it is the source. If a recommendation is disassociated from this source list, delete it
            "cascade": "all, delete-orphan",
            "lazy": "joined",
        },
    )
    recommendations_where_this_is_target: list["Recommendation"] = Relationship(  # type: ignore
        back_populates="target_article",
        sa_relationship_kwargs={
            "primaryjoin": "Recommendation.target_article_id==Article.page_id",
            # If an article is deleted, delete all recommendations where it is the target. If a recommendation is disassociated from this target list, delete it
            "cascade": "all, delete-orphan",
            "lazy": "joined",
        },
    )
