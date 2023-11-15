from enum import StrEnum

from sqlmodel import Relationship

from .helpers import AutoUUIDPrimaryKey, CreationTracked, SQLModel


class StrategyType(StrEnum):
    POPULARITY = "popularity"
    COLLABORATIVE_FILTERING_ITEM_BASED = "collaborative_filtering_item_based"
    SEMANTIC_SIMILARITY = "semantic_similarity"


class StrategyRecommendationType(StrEnum):
    DEFAULT_AKA_NO_SOURCE = "default_aka_no_source"
    SOURCE_TARGET_INTERCHANGEABLE = "source_target_interchangeable"  # This is where either S -> T or T -> S is saved to save space, since one recommendation goes both ways
    SOURCE_TARGET_NOT_INTERCHANGEABLE = "source_target_not_interchangeable"


class Execution(SQLModel, AutoUUIDPrimaryKey, CreationTracked, table=True):
    """
    Log of training job executions, each with respect to a single strategy.
    """

    strategy: StrategyType
    strategy_recommendation_type: StrategyRecommendationType

    # An execution has multiple embeddings
    embeddings: list["Embedding"] = Relationship(back_populates="execution")  # type: ignore
    # An execution can produce zero (if it doesn't have a default strategy, such as popularity)
    # or multiple default recommendations (if it has a default strategy)
    recommendations: list["Recommendation"] = Relationship(back_populates="execution")  # type: ignore
