import os
from typing import Optional

from sqlalchemy.future.engine import Connection
from sqlmodel import text

from .helpers import Stage


def create_database(conn: Connection, db_name: Stage) -> None:
    statement = text(f"CREATE DATABASE {db_name}")
    conn.execution_options(isolation_level="AUTOCOMMIT").execute(statement)


def get_conn_string(db_name: Optional[str] = None) -> str:
    # everything but dbname should be the same, since we are using the admin user for everything
    host = os.getenv("HOST", "localhost")
    port = os.getenv("PORT", "5432")
    user = os.getenv("USERNAME", "postgres")
    password = os.getenv("PASSWORD", "postgres")
    if not db_name:
        # if no db_name is passed, we assume it is for the default db. This is assumed to be "default"
        # unless indicated otherwise via this DB_NAME env var
        db_name = os.getenv("DB_NAME", "postgres")

    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
