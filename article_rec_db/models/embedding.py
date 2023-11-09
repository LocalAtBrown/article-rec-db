from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector  # type: ignore
from sqlmodel import Column, Field, Relationship

from .article import Article
from .base import SQLModel
from .execution import Execution

# The maximum number of dimensions that the vector can have. Vectors with fewer dimensions will be padded with zeros.
MAX_DIMENSIONS = 384


class Embedding(SQLModel, table=True):
    id: Annotated[UUID, Field(default_factory=uuid4, primary_key=True)]
    db_created_at: Annotated[datetime, Field(default_factory=datetime.utcnow)]
    article_id: Annotated[UUID, Field(foreign_key="article.page_id")]
    execution_id: Annotated[UUID, Field(foreign_key="execution.id")]
    vector: Annotated[list[float], Field(sa_column=Column(Vector(MAX_DIMENSIONS)))]

    # An embedding always corresonds to an article
    article: Article = Relationship(back_populates="embeddings")

    # An embedding always corresponds to an execution
    execution: Execution = Relationship(back_populates="embeddings")
