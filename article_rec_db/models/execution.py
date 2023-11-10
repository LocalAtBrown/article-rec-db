from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship

from .base import SQLModel
from .helpers import StrategyType


class Execution(SQLModel, table=True):
    """
    Log of training job executions, each with respect to a single strategy.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    strategy: StrategyType
    db_created_at: Annotated[datetime, Field(default_factory=datetime.utcnow)]

    # An execution has multiple embeddings
    embeddings: list["Embedding"] = Relationship(back_populates="execution")  # type: ignore
    # An execution has multiple recommendations
    # recommendations: list["Recommendation"] = Relationship(back_populates="execution")
