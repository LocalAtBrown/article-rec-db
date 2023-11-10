from sqlalchemy import text
from sqlalchemy.future.engine import Connection

from .helpers import Extension


def enable_extension(conn: Connection, extension: Extension) -> None:
    # extension should have already been installed to the machine running the database (which is an infra requirement)
    statement_str = f"CREATE EXTENSION IF NOT EXISTS {extension.name}"
    if extension.schema is not None:
        statement_str += f" SCHEMA {extension.schema}"
    if extension.version is not None:
        statement_str += f" VERSION {extension.version}"
    if extension.cascade:
        statement_str += " CASCADE"
    statement = text(statement_str)
    conn.execute(statement)
