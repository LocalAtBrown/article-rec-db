from sqlmodel import Relationship

from .base import AutoUUIDPrimaryKey, CreationTracked, SQLModel
from .helpers import StrategyType


class Execution(SQLModel, AutoUUIDPrimaryKey, CreationTracked, table=True):
    """
    Log of training job executions, each with respect to a single strategy.
    """

    strategy: StrategyType

    # An execution has multiple embeddings
    embeddings: list["Embedding"] = Relationship(back_populates="execution")  # type: ignore
    # An execution can produce zero (if it doesn't have a default strategy, such as popularity)
    # or multiple default recommendations (if it has a default strategy)
    recommendations: list["Recommendation"] = Relationship(back_populates="execution")  # type: ignore
