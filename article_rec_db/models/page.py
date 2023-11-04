import re
from typing import Optional
from uuid import UUID, uuid4

from pydantic import validator
from sqlmodel import Field

from article_rec_db.sites import SiteName

from .helpers import ArticleExcludeReason, TimestampTrackedModel

PATTERN_URLPATH = re.compile(r"^(?P<path>/[^\s?#]*)?$")


class Page(TimestampTrackedModel, table=True):
    id: UUID = Field(default_factory=uuid4, unique=True)
    site: SiteName = Field(primary_key=True)
    path: str = Field(primary_key=True)
    article_exclude_reason: Optional[ArticleExcludeReason] = None

    @validator("path")
    def path_must_be_valid(cls, value: str) -> str:
        assert PATTERN_URLPATH.fullmatch(value) is not None, "Path must be valid"
        return value
