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
    Log of training job task executions, each with respect to a single strategy.
    """

    strategy: StrategyType
    strategy_recommendation_type: StrategyRecommendationType

    # An execution has multiple embeddings
    embeddings: list["Embedding"] = Relationship(  # type: ignore
        back_populates="execution",
        sa_relationship_kwargs={
            # If an execution is deleted, delete all embeddings associated with it. If an embedding is disassociated from this execution, delete it
            "cascade": "all, delete-orphan"
        },
    )
    # An execution can produce zero (if it doesn't have a default strategy, such as popularity)
    # or multiple default recommendations (if it has a default strategy)
    recommendations: list["Recommendation"] = Relationship(  # type: ignore
        back_populates="execution",
        sa_relationship_kwargs={
            # If an execution is deleted, delete all recommendations associated with it. If a recommendation is disassociated from this execution, delete it
            "cascade": "all, delete-orphan"
        },
    )
