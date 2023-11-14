from typing import Annotated
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship

from .article import Article
from .base import CreationTrackedModel
from .execution import Execution


class Recommendation:
    """
    Recommendations where there's a source article (i.e., the one the reader is reading)
    and a target article (i.e., the one the reader is recommended upon/after reading the source).
    """

    pass


class RecommendationDefault(CreationTrackedModel, table=True):
    """
    Default recommendations. Just target articles with no source, since it's
    supposed to be used as a fallback for any source.
    """

    id: Annotated[UUID, Field(default_factory=uuid4, primary_key=True)]
    execution_id: Annotated[UUID, Field(foreign_key="execution.id")]
    article_id: Annotated[UUID, Field(foreign_key="article.page_id")]

    # A recommendation always corresponds to a job execution
    execution: Execution = Relationship(back_populates="recommendations_default")

    # A default recommendation always corresponds to a target article
    article: Article = Relationship(back_populates="default_recommendations_where_this_is_target")
