from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel  # noqa: F401


# Common fields as Pydantic model mixins
class AutoUUIDPrimaryKey(SQLModel, table=False):
    id: Annotated[UUID, Field(default_factory=uuid4, primary_key=True)]


class CreationTracked(SQLModel, table=False):
    db_created_at: Annotated[datetime, Field(default_factory=datetime.utcnow)]


class UpdateTracked(CreationTracked, table=False):
    db_updated_at: Annotated[Optional[datetime], Field(sa_column_kwargs={"onupdate": datetime.utcnow})]
