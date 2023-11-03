import re
from enum import StrEnum

from pydantic import BaseModel, validator

PATTERN_SITE_NAME_KEBAB = re.compile(r"^[a-z]+(-[a-z]+)*$")


class SiteName(StrEnum):
    AFRO_LA = "afro-la"
    DALLAS_FREE_PRESS = "dallas-free-press"


class Site(BaseModel):
    name: SiteName

    @validator("name")
    def name_must_be_kebabcase(cls, value: SiteName) -> SiteName:
        assert PATTERN_SITE_NAME_KEBAB.fullmatch(value) is not None, "Site name must be kebab-case"
        return value

    @property
    def name_snakecase(self) -> str:
        return self.name.replace("-", "_")
