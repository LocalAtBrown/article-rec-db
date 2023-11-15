from typing import Annotated, Optional
from uuid import UUID

from sqlmodel import Field, Relationship

from .article import Article
from .base import AutoUUIDPrimaryKey, CreationTracked, SQLModel
from .execution import Execution


class Recommendation(SQLModel, AutoUUIDPrimaryKey, CreationTracked, table=True):
    """
    Usual recommendations have a source article (i.e., the one the reader is reading)
    and a target article (i.e., the one the reader is recommended upon/after reading the source).

    Default recommendations are recommendations with just a target and without a source, since it's
    supposed to be used as a fallback for any source.
    """

    execution_id: Annotated[UUID, Field(foreign_key="execution.id")]
    source_article_id: Annotated[Optional[UUID], Field(foreign_key="article.page_id")]
    target_article_id: Annotated[UUID, Field(foreign_key="article.page_id")]

    # A recommendation always corresponds to a job execution
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
