import re
from datetime import datetime
from enum import StrEnum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import validator
from sqlmodel import Field, SQLModel

from article_rec_db.sites import SiteName


class ArticleExcludeReason(StrEnum):
    NOT_ARTICLE = "not_article"
    NOT_IN_HOUSE_ARTICLE = "not_in_house_article"
    TEST_ARTICLE = "test_article"
    HAS_EXCLUDED_TAG = "has_excluded_tag"


PATTERN_URLPATH = re.compile(r"^(?P<path>/[^\s?#]*)?$")


class TimestampTrackedModel(SQLModel):
    db_created_at: datetime = Field(default_factory=datetime.utcnow, allow_mutation=False)
    db_updated_at: Optional[datetime] = None


class Page(TimestampTrackedModel, table=True):
    id: UUID = Field(default_factory=uuid4, unique=True)
    site: SiteName = Field(primary_key=True)
    path: str = Field(primary_key=True)
    article_exclude_reason: Optional[ArticleExcludeReason] = None

    @validator("path")
    def path_must_be_valid(cls, value: str) -> str:
        assert PATTERN_URLPATH.fullmatch(value) is not None, "Path must be valid"
        return value


class Article(SQLModel, table=True):
    id: UUID = Field(primary_key=True, foreign_key="page.id")
    id_in_site: str  # ID of article in the partner site's internal system
    title: str
    published_at: datetime
