from datetime import datetime
from typing import Annotated
from uuid import UUID

from sqlmodel import Column, Field, String

from article_rec_db.sites import SiteName

from .base import TimestampTrackedModel


class Article(TimestampTrackedModel, table=True):
    page_id: Annotated[UUID, Field(primary_key=True, foreign_key="page.id")]
    site: Annotated[SiteName, Field(sa_column=Column(String))]
    id_in_site: str  # ID of article in the partner site's internal system
    title: str
    published_at: datetime
