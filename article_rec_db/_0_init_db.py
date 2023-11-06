from typing import Type

from sqlmodel import SQLModel

from article_rec_db.db.controller import (
    initialize_tables,
    post_table_initialization,
    pre_table_initialization,
)
from article_rec_db.db.helpers import (
    Component,
    Grant,
    Privilege,
    RowLevelSecurityPolicy,
    Stage,
)
from article_rec_db.models import SQLModel as ArticleRecDbSQLModel
from article_rec_db.sites import AFRO_LA, DALLAS_FREE_PRESS


def initialize_all_database_entities(
    stage: Stage, components: list[Component], site_names: list[str], sqlmodel_class: Type[SQLModel]
) -> None:
    # needs default db
    pre_table_initialization(stage=stage, components=components, site_names=site_names)
    # needs to connect to this stage's db
    initialize_tables(stage=stage, sqlmodel_class=sqlmodel_class)
    # needs this stage's db
    post_table_initialization(stage=stage, components=components)


if __name__ == "__main__":
    stages = [Stage.DEV, Stage.PROD]
    training_job = Component(
        name="training_job",
        grants=[
            Grant(
                privileges=[Privilege.SELECT, Privilege.INSERT, Privilege.UPDATE, Privilege.DELETE],
                tables=["page", "article"],
            )
        ],
        policies=[RowLevelSecurityPolicy(table="article", user_column="site")],
    )
    components = [training_job]
    site_names = [AFRO_LA.name_snakecase, DALLAS_FREE_PRESS.name_snakecase]

    # roles are dev-training-job and prod-pipeline0
    # users are dev-pipeline0-afro-la, dev-pipeline0-dallas-free-press, ... , prod-pipeline0-the-19th

    for stage in stages:
        initialize_all_database_entities(
            stage=stage, components=components, site_names=site_names, sqlmodel_class=ArticleRecDbSQLModel
        )
