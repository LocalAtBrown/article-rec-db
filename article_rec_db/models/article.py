from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlmodel import Field, Relationship, String, Text, UniqueConstraint

from .helpers import UpdateTracked
from .page import Page


class Language(StrEnum):
    """
    Languages an article can have, in the IETF tag format
    """

    # Add more as needed
    ENGLISH = "en"
    SPANISH = "es"


class Article(UpdateTracked, table=True):
    __table_args__ = (UniqueConstraint("site", "id_in_site", name="article_site_idinsite_unique"),)

    # Page ID refers to the page table
    page_id: UUID = Field(primary_key=True, foreign_key="page.id")

    # Site name
    site: str = Field(sa_type=String)
    # ID of article in the partner site's internal system
    id_in_site: str

    # Title/headline
    title: str
    # Description/summary
    description: str | None
    # Full text of article; might also include (sanitized) HTML tags
    content: str = Field(sa_type=Text)

    # When the article was published on the partner site
    site_published_at: datetime
    # When the article was last updated on the partner site
    site_updated_at: datetime | None

    # Language of the article
    language: Language = Language.ENGLISH

    # Whether the article is in-house content or not (e.g., republished from another source)
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
