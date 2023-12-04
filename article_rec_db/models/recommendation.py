from typing import Annotated, Any, Optional
from uuid import UUID

from sqlalchemy import event
from sqlmodel import (
    CheckConstraint,
    Column,
    Field,
    Float,
    Relationship,
    UniqueConstraint,
)

from .article import Article
from .execution import Execution, StrategyRecommendationType
from .helpers import AutoUUIDPrimaryKey, CreationTracked, SQLModel


class Recommendation(SQLModel, AutoUUIDPrimaryKey, CreationTracked, table=True):
    """
    Usual recommendations have a source article (i.e., the one the reader is reading)
    and a target article (i.e., the one the reader is recommended upon/after reading the source).

    Default recommendations are recommendations with just a target and without a source, since it's
    supposed to be used as a fallback for any source.
    """

    # Unique constraint on execution_id and target_article_id, since we don't want to record the same recommendation twice
    __table_args__ = (
        UniqueConstraint("execution_id", "target_article_id", name="recommendation_execution_target_unique"),
    )

    execution_id: Annotated[UUID, Field(foreign_key="execution.id")]
    source_article_id: Annotated[Optional[UUID], Field(foreign_key="article.page_id")]
    target_article_id: Annotated[UUID, Field(foreign_key="article.page_id")]

    # Recommendation score, between 0 and 1. Top recs should have higher scores
    score: Annotated[
        float,
        Field(
            sa_column=Column(
                Float, CheckConstraint("score >= 0 AND score <= 1", name="recommendation_score_between_0_and_1")
            )
        ),
    ]

    # A recommendation always corresponds to a task execution
    execution: Execution = Relationship(back_populates="recommendations")

    # A default recommendation always corresponds to a target article, but not necessarily to a source article
    # The sa_relationship_kwargs is here to avert the AmbiguousForeignKeyError, see: https://github.com/tiangolo/sqlmodel/issues/10#issuecomment-1537445078
    source_article: Optional[Article] = Relationship(
        back_populates="recommendations_where_this_is_source",
        sa_relationship_kwargs={"foreign_keys": "[Recommendation.source_article_id]"},
    )
    target_article: Article = Relationship(
        back_populates="recommendations_where_this_is_target",
        sa_relationship_kwargs={"foreign_keys": "[Recommendation.target_article_id]"},
    )


@event.listens_for(Recommendation, "before_insert")
def validate_source_id_lower_then_target_id_when_interchangeable(
    mapper: Any, connection: Any, target: Recommendation
) -> None:
    if target.execution.strategy_recommendation_type == StrategyRecommendationType.SOURCE_TARGET_INTERCHANGEABLE:
        assert (
            target.source_article_id is not None
        ), "Source article ID must be non-null when source and target are interchangeable."
        assert target.source_article_id < target.target_article_id, (
            "Source article ID must be lower than target article ID when source and target are interchangeable. "
            "This is a convention to make sure that the same recommendation is not recorded twice."
        )


@event.listens_for(Recommendation, "before_insert")
def validate_source_id_empty_when_strategy_default(mapper: Any, connection: Any, target: Recommendation) -> None:
    if target.execution.strategy_recommendation_type == StrategyRecommendationType.DEFAULT_AKA_NO_SOURCE:
        assert (
            target.source_article_id is None
        ), f"Source article ID must be empty when execution strategy's recommendation type is default."
