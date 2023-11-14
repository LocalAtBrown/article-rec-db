from typing import Annotated
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship

from .base import CreationTrackedModel
from .helpers import StrategyType


class Execution(CreationTrackedModel, table=True):
    """
    Log of training job executions, each with respect to a single strategy.
    """

    id: Annotated[UUID, Field(default_factory=uuid4, primary_key=True)]
    strategy: StrategyType

    # An execution has multiple embeddings
    embeddings: list["Embedding"] = Relationship(back_populates="execution")  # type: ignore
    # An execution can produce zero (if it doesn't have a default strategy, such as popularity)
    # or multiple default recommendations (if it has a default strategy)
    recommendations_default: list["RecommendationDefault"] = Relationship(back_populates="execution")  # type: ignore
