from enum import StrEnum

from sqlmodel import Relationship

from .helpers import AutoUUIDPrimaryKey, CreationTracked


class RecommendationType(StrEnum):
    DEFAULT_AKA_NO_SOURCE = "default_aka_no_source"
    SOURCE_TARGET_INTERCHANGEABLE = "source_target_interchangeable"  # This is where either S -> T or T -> S is saved to save space, since one recommendation goes both ways
    SOURCE_TARGET_NOT_INTERCHANGEABLE = "source_target_not_interchangeable"


class Execution(AutoUUIDPrimaryKey, CreationTracked, table=True):
    """
    Log of training job task executions.
    """

    # Name of task, to be defined by training job
    task_name: str

    # Task success/failure status
    success: bool

    # Recommendation type, if the task creates recommendations
    recommendation_type: RecommendationType | None

    # An execution can have multiple pages, if it creates multiple pages
    pages: list["Page"] = Relationship(  # type: ignore
        back_populates="execution",
        sa_relationship_kwargs={
            # If an execution is deleted, delete all pages associated with it. If a page is disassociated from this execution, delete it
            "cascade": "all, delete-orphan"
        },
    )

    # An execution can have multiple articles, if it creates or updates multiple articles
    articles: list["Article"] = Relationship(  # type: ignore
        back_populates="execution_last_updated",
        sa_relationship_kwargs={
            # If an execution is deleted, delete all articles associated with it. If an article is disassociated from this execution, delete it
            "cascade": "all, delete-orphan"
        },
    )

    # An execution can have multiple embeddings, if it creates multiple embeddings
    embeddings: list["Embedding"] = Relationship(  # type: ignore
        back_populates="execution",
        sa_relationship_kwargs={
            # If an execution is deleted, delete all embeddings associated with it. If an embedding is disassociated from this execution, delete it
            "cascade": "all, delete-orphan"
        },
    )
    # An execution can have multiple recommendations, if it creates multiple recommendations
    recommendations: list["Recommendation"] = Relationship(  # type: ignore
        back_populates="execution",
        sa_relationship_kwargs={
            # If an execution is deleted, delete all recommendations associated with it. If a recommendation is disassociated from this execution, delete it
            "cascade": "all, delete-orphan"
        },
    )
