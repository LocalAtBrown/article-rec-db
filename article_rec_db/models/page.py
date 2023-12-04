from typing import Annotated
from uuid import UUID, uuid4

from pydantic import HttpUrl
from sqlmodel import Column, Field, Relationship, String

from .helpers import AutoUUIDPrimaryKey, SQLModel, UpdateTracked


class Page(SQLModel, AutoUUIDPrimaryKey, UpdateTracked, table=True):
    id: Annotated[UUID, Field(default_factory=uuid4, primary_key=True)]
    url: Annotated[HttpUrl, Field(sa_column=Column(String, unique=True))]

    # An article is always a page, but a page is not always an article
    # Techinically SQLModel considers Page the "many" in the many-to-one relationship, so this list will only ever have at most one element
    article: list["Article"] = Relationship(  # type: ignore
        back_populates="page",
        sa_relationship_kwargs={
            # If a page is deleted, delete the article associated with it. If an article is disassociated from this page, delete it
            "cascade": "all, delete-orphan"
        },
    )
