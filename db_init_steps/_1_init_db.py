import os

from loguru import logger

from article_rec_db.db.controller import initialize_tables, post_table_initialization
from article_rec_db.db.helpers import (
    Component,
    Grant,
    Privilege,
    RowLevelSecurityPolicy,
    Stage,
)
from article_rec_db.models import SQLModel
from article_rec_db.sites import AFRO_LA, DALLAS_FREE_PRESS

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
        # needs to connect to this stage's db
        initialize_tables(stage=stage, sqlmodel_class=SQLModel)
        # needs this stage's db
        post_table_initialization(stage=stage, components=components)

    logger.info(f"{os.path.relpath(__file__)} done!")
