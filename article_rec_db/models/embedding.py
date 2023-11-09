from typing import Annotated
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlmodel import Column, Field, Relationship

from .article import Article
from .base import TimestampTrackedModel
from .helpers import RecommendationStrategy

# The maximum number of dimensions that the vector can have. Vectors with fewer dimensions will be padded with zeros.
MAX_DIMENSIONS = 384


class Embedding(TimestampTrackedModel, table=True):
    id: Annotated[UUID, Field(default_factory=uuid4, primary_key=True)]
    article_id: Annotated[UUID, Field(foreign_key="article.page_id")]
    strategy: RecommendationStrategy
    vector: Annotated[list[float], Field(sa_column=Column(Vector(MAX_DIMENSIONS)))]

    # An embedding always corresonds to an article
    article: Article = Relationship(back_populates="embeddings")
