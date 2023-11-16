from enum import StrEnum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import HttpUrl
from sqlmodel import Column, Field, Relationship, String

from .helpers import AutoUUIDPrimaryKey, SQLModel, UpdateTracked


class ArticleExcludeReason(StrEnum):
    NOT_ARTICLE = "not_article"
    NOT_IN_HOUSE_ARTICLE = "not_in_house_article"
    TEST_ARTICLE = "test_article"
    HAS_EXCLUDED_TAG = "has_excluded_tag"


class Page(SQLModel, AutoUUIDPrimaryKey, UpdateTracked, table=True):
    id: Annotated[UUID, Field(default_factory=uuid4, primary_key=True)]
    url: Annotated[HttpUrl, Field(sa_column=Column(String, unique=True))]
    article_exclude_reason: ArticleExcludeReason | None = None

    # An article is always a page, but a page is not always an article
    # Techinically SQLModel considers Page the "many" in the many-to-one relationship, so this list will only ever have at most one element
    article: list["Article"] = Relationship(  # type: ignore
        back_populates="page",
        sa_relationship_kwargs={
            # If a page is deleted, delete the article associated with it. If an article is disassociated from this page, delete it
            "cascade": "all, delete-orphan"
        },
    )
