import re

from pydantic import BaseModel, field_validator

from .helpers import SiteName

PATTERN_SITE_NAME_KEBAB = re.compile(r"^[a-z]+(-[a-z]+)*$")


class Site(BaseModel):
    name: SiteName

    @field_validator("name")
    @classmethod
    def name_must_be_kebabcase(cls, value: SiteName) -> SiteName:
        assert PATTERN_SITE_NAME_KEBAB.fullmatch(value) is not None, "Site name must be kebab-case"
        return value

    @property
    def name_snakecase(self) -> str:
        return self.name.replace("-", "_")
