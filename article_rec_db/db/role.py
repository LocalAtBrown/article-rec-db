import json
import os
import random

from sqlalchemy.future.engine import Connection
from sqlmodel import text

from .helpers import (
    Component,
    DatabaseConnectionCredentials,
    Privilege,
    Stage,
    generate_password,
    get_ssm_client,
)


def create_role(conn: Connection, role: str) -> None:
    statement = text(f"CREATE ROLE {role}")
    conn.execute(statement)


def create_user(conn: Connection, username: str, bypassrls: bool = False) -> str:
    pw = generate_password()
    rls_flag = ""
    if bypassrls:
        rls_flag = " BYPASSRLS"
    statement = text(f"CREATE USER {username} WITH PASSWORD :password{rls_flag}")
    conn.execute(statement, {"password": pw})
    return pw


def assign_role(conn: Connection, role: str, usernames: list[str]) -> None:
    users = ", ".join(usernames)
    statement = text(f"GRANT {role} TO {users}")
    conn.execute(statement)


def grant_privileges(conn: Connection, user_or_role: str, table: str, privileges: list[Privilege]) -> None:
    formatted_privileges = ", ".join(privileges)
    statement = text(f"GRANT {formatted_privileges} ON {table} TO {user_or_role}")
    conn.execute(statement)


def enable_row_level_security(conn: Connection, table: str, target_column: str, role: str) -> None:
    s1 = text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    conn.execute(s1)
    random_postfix = "%06x" % random.randrange(16**6)
    policy_name = f"{table}_{role}_{random_postfix}"
    s2 = text(
        f"CREATE POLICY {policy_name} ON {table} TO {role} USING (current_user ~ REPLACE({target_column}, '-', '_'))"
    )
    conn.execute(s2)


def create_users(conn: Connection, stage: Stage, component: Component, site_names: list[str]) -> None:
    ssm_client = get_ssm_client()
    for site_name in site_names:
        username = f"{stage}_{component.name}_{site_name}"
        pw = create_user(conn, username=username)
        if ssm_client:
            user_creds = DatabaseConnectionCredentials(
                HOST=os.getenv("HOST", "localhost"),
                PORT=int(os.getenv("PORT", "5432")),
                DB_NAME=stage,
                USERNAME=username,
                PASSWORD=pw,
            )
            ssm_client.put_parameter(
                Name=f"/{stage}/ata/{site_name}/{component.name}/database-credentials",
                Description=f"DB credentials for partner {site_name}, component {component}, and env {stage}.",
                Value=json.dumps(user_creds.__dict__),
                Type="String",
                Overwrite=True,
            )
