import re
from datetime import datetime
from enum import StrEnum
from typing import Optional

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


class Path(TimestampTrackedModel, table=True):
    site: SiteName = Field(primary_key=True)
    id_site: str = Field(primary_key=True)
    path: str
    article_exclude_reason: Optional[ArticleExcludeReason] = None

    @validator("path")
    def path_must_be_valid(cls, value: str) -> str:
        assert PATTERN_URLPATH.fullmatch(value) is not None, "Path must be valid"
        return value


class Article(SQLModel, table=True):
    site: SiteName = Field(primary_key=True, foreign_key="path.site")
    id_site: str = Field(primary_key=True, foreign_key="path.id_site")
    title: str
    published_at: datetime
