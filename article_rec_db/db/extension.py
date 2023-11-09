from sqlalchemy import text
from sqlalchemy.future.engine import Connection

from .helpers import Extension


def enable_extension(conn: Connection, extension: Extension) -> None:
    # extension should have already been installed to the machine running the database (which is an infra requirement)
    statement = text(f"CREATE EXTENSION IF NOT EXISTS {extension}")
    conn.execute(statement)
