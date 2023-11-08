from builtins import type

from sqlalchemy.future.engine import create_engine
from sqlmodel import SQLModel

from .database import create_database, get_conn_string
from .helpers import Component, Stage
from .role import (
    assign_role,
    create_role,
    create_users,
    enable_row_level_security,
    grant_privileges,
)


def pre_table_initialization(
    stage: Stage, components: list[Component], site_names: list[str], create_dbs: bool = True
) -> None:
    engine = create_engine(get_conn_string())

    with engine.connect() as conn:
        if create_dbs:
            create_database(conn, db_name=stage)
        for component in components:
            role = f"{stage}_{component.name}"
            create_role(conn, role=role)
            usernames = [f"{stage}_{component.name}_{site_name}" for site_name in site_names]
            create_users(conn, stage=stage, component=component, site_names=site_names)
            assign_role(conn, role=role, usernames=usernames)
        conn.commit()


def initialize_tables(stage: Stage, sqlmodel_class: type[SQLModel]) -> None:
    engine = create_engine(get_conn_string(db_name=stage))
    sqlmodel_class.metadata.create_all(engine)


def post_table_initialization(stage: Stage, components: list[Component]) -> None:
    engine = create_engine(get_conn_string(db_name=stage))

    with engine.connect() as conn:
        for component in components:
            for grant in component.grants:
                for table in grant.tables:
                    grant_privileges(
                        conn, user_or_role=f"{stage}_{component.name}", table=table, privileges=grant.privileges
                    )
            for policy in component.policies:
                enable_row_level_security(
                    conn, table=policy.table, target_column=policy.user_column, role=f"{stage}_{component.name}"
                )

        conn.commit()
