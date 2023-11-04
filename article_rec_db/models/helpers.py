from datetime import datetime
from enum import StrEnum
from typing import Optional

from sqlmodel import Field, SQLModel


class ArticleExcludeReason(StrEnum):
    NOT_ARTICLE = "not_article"
    NOT_IN_HOUSE_ARTICLE = "not_in_house_article"
    TEST_ARTICLE = "test_article"
    HAS_EXCLUDED_TAG = "has_excluded_tag"


class TimestampTrackedModel(SQLModel):
    db_created_at: datetime = Field(default_factory=datetime.utcnow, allow_mutation=False)
    db_updated_at: Optional[datetime] = None
