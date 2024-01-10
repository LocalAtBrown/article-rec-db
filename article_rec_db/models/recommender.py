from enum import StrEnum

from sqlmodel import Relationship

from .helpers import AutoUUIDPrimaryKey, CreationTracked


class RecommendationType(StrEnum):
    DEFAULT_AKA_NO_SOURCE = "default_aka_no_source"
    SOURCE_TARGET_INTERCHANGEABLE = "source_target_interchangeable"  # This is where either S -> T or T -> S is saved to save space, since one recommendation goes both ways
    SOURCE_TARGET_NOT_INTERCHANGEABLE = "source_target_not_interchangeable"


class Recommender(AutoUUIDPrimaryKey, CreationTracked, table=True):
    """
    Log of used recommenders.
    """

    # Name of the recommendation strategy (e.g., semantic similarity, item-based collaborative filtering)
    strategy: str

    # Type of recommendation
    recommendation_type: RecommendationType

    # A recommender can produce multiple embeddings
    embeddings: list["Embedding"] = Relationship(  # type: ignore
        back_populates="recommender",
        sa_relationship_kwargs={
            # If a recommender is deleted, delete all embeddings associated with it. If an embedding is disassociated from this recommender, delete it
            "cascade": "all, delete-orphan"
        },
    )
    # A recommender can produce multiple recommendations
    recommendations: list["Recommendation"] = Relationship(  # type: ignore
        back_populates="recommender",
        sa_relationship_kwargs={
            # If a recommender is deleted, delete all recommendations associated with it. If a recommendation is disassociated from this recommender, delete it
            "cascade": "all, delete-orphan"
        },
    )
