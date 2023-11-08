import os
import secrets
import string
from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

import boto3
from mypy_boto3_ssm import SSMClient


class Privilege(StrEnum):
    """
    Possible privileges to grant to Postgres users: https://www.postgresql.org/docs/15/ddl-priv.html
    """

    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    TRUNCATE = "TRUNCATE"
    REFERENCES = "REFERENCES"
    TRIGGER = "TRIGGER"
    CREATE = "CREATE"
    CONNECT = "CONNECT"
    TEMPORARY = "TEMPORARY"
    EXECUTE = "EXECUTE"
    USAGE = "USAGE"
    SET = "SET"
    ALTER_SYSTEM = "ALTER_SYSTEM"


class Stage(StrEnum):
    DEV = "dev"
    PROD = "prod"


@dataclass
class Grant:
    privileges: list[Privilege]
    tables: list[str]


@dataclass
class RowLevelSecurityPolicy:
    # TODO have table and user_column reference actual Table and Column objects
    table: str
    user_column: str
    policy_name: Optional[str] = None


@dataclass
class Component:
    # effectively a db-constrained role
    name: str
    grants: list[Grant]
    policies: list[RowLevelSecurityPolicy]


@dataclass
class DatabaseConnectionCredentials:
    HOST: str
    PORT: int
    DB_NAME: str
    USERNAME: str
    PASSWORD: str


def get_ssm_client() -> Optional[SSMClient]:
    # ENABLE_SSM has to explicitly be set to exactly "TRUE" or else no SSM interactions take place
    if os.getenv("ENABLE_SSM", "FALSE") == "TRUE":
        return boto3.client("ssm")
    else:
        return None


def generate_password() -> str:
    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        password = "".join(secrets.choice(alphabet) for i in range(20))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and sum(c.isdigit() for c in password) >= 3
        ):
            break
    return password
