import re
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import validator
from sqlmodel import Field

from article_rec_db.sites import SiteName

from .base import TimestampTrackedModel
from .helpers import ArticleExcludeReason

PATTERN_URLPATH = re.compile(r"^(?P<path>/[^\s?#]*)?$")


class Page(TimestampTrackedModel, table=True):
    id: Annotated[UUID, Field(default_factory=uuid4, unique=True)]
    site: Annotated[SiteName, Field(primary_key=True)]
    path: Annotated[str, Field(primary_key=True)]
    article_exclude_reason: ArticleExcludeReason | None = None

    @validator("path")
    def path_must_be_valid(cls, value: str) -> str:
        assert PATTERN_URLPATH.fullmatch(value) is not None, "Path must be valid"
        return value
