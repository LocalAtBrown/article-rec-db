from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class TimestampTrackedModel(SQLModel):
    db_created_at: datetime = Field(default_factory=datetime.utcnow, allow_mutation=False)
    db_updated_at: Optional[datetime] = None
