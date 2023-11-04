from datetime import datetime
from typing import Annotated

from sqlmodel import Field, SQLModel


class TimestampTrackedModel(SQLModel, table=False):
    db_created_at: Annotated[datetime, Field(default_factory=datetime.utcnow)]
    db_updated_at: datetime | None = None
