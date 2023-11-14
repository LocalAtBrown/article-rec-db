from datetime import datetime
from typing import Annotated
from uuid import UUID

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

    # An article can be the target of one or more default recommendations
    default_recommendations_where_this_is_target: list["RecommendationDefault"] = Relationship(back_populates="article")  # type: ignore
