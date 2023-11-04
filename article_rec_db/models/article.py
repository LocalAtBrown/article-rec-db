from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel


class Article(SQLModel, table=True):
    id: UUID = Field(primary_key=True, foreign_key="page.id")
    id_in_site: str  # ID of article in the partner site's internal system
    title: str
    published_at: datetime
