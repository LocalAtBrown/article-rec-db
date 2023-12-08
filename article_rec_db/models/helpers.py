from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel  # noqa: F401


# Common fields as Pydantic model mixins
class AutoUUIDPrimaryKey(SQLModel, table=False):
    id: UUID = Field(default_factory=uuid4, primary_key=True)


class CreationTracked(SQLModel, table=False):
    db_created_at: datetime = Field(default_factory=datetime.utcnow)


class UpdateTracked(CreationTracked, table=False):
    db_updated_at: datetime | None = Field(sa_column_kwargs={"onupdate": datetime.utcnow})
