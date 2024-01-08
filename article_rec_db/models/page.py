from typing import Optional
from uuid import UUID, uuid4

from pydantic import HttpUrl
from sqlmodel import Field, Relationship, String

from .execution import Execution
from .helpers import AutoUUIDPrimaryKey, CreationTracked


class Page(AutoUUIDPrimaryKey, CreationTracked, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    url: HttpUrl = Field(sa_type=String, unique=True)

    # ID of task execution that created this page
    execution_id: UUID = Field(foreign_key="execution.id")

    # An execution always correspononds to the task execution that created it
    execution: Execution = Relationship(back_populates="pages")

    # An article is always a page, but a page is not always an article
    article: Optional["Article"] = Relationship(  # type: ignore
        back_populates="page",
        sa_relationship_kwargs={
            # If a page is deleted, delete the article associated with it. If an article is disassociated from this page, delete it
            "cascade": "all, delete-orphan",
            # Specify a one-to-one relationship between page and article
            "uselist": False,
        },
    )
