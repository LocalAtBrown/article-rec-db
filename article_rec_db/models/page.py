from typing import Annotated
from uuid import UUID, uuid4

from pydantic import HttpUrl
from sqlmodel import Column, Field, Relationship, String

from .base import TimestampTrackedModel
from .helpers import ArticleExcludeReason


class Page(TimestampTrackedModel, table=True):
    id: Annotated[UUID, Field(default_factory=uuid4, primary_key=True)]
    url: Annotated[HttpUrl, Field(sa_column=Column(String, unique=True))]
    article_exclude_reason: ArticleExcludeReason | None = None

    # An article is always a page, but a page is not always an article
    # Techinically SQLModel considers Page the "many" in the many-to-one relationship, so this list will only ever have at most one element
    article: list["Article"] = Relationship(back_populates="page")  # type: ignore
