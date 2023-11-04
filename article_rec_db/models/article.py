from datetime import datetime
from typing import Annotated
from uuid import UUID

from sqlmodel import Field

from .base import SQLModel


class Article(SQLModel, table=True):
    id: Annotated[UUID, Field(primary_key=True, foreign_key="page.id")]
    id_in_site: str  # ID of article in the partner site's internal system
    title: str
    published_at: datetime
