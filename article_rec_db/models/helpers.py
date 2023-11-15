from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlmodel import Column, DateTime, Field, SQLModel  # noqa: F401


# Common fields as Pydantic model mixins
class AutoUUIDPrimaryKey(BaseModel):
    id: Annotated[UUID, Field(default_factory=uuid4, primary_key=True)]


class CreationTracked(BaseModel):
    db_created_at: Annotated[datetime, Field(default_factory=datetime.utcnow)]


class UpdateTracked(CreationTracked):
    db_updated_at: Annotated[Optional[datetime], Field(sa_column=Column(DateTime, onupdate=datetime.utcnow))]


class TableOperationError(Exception):
    pass


def forbid_update(mapper, connection, target) -> None:
    raise TableOperationError(f"Updating records is forbidden on table {target.__tablename__}")
