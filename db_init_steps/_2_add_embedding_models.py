import os

from loguru import logger
from sqlmodel import create_engine

from article_rec_db.db.controller import post_table_initialization
from article_rec_db.db.database import get_conn_string
from article_rec_db.db.extension import enable_extension
from article_rec_db.db.helpers import Component, Extension, Grant, Privilege, Stage
from article_rec_db.sites import AFRO_LA, DALLAS_FREE_PRESS

if __name__ == "__main__":
    stages = [Stage.DEV, Stage.PROD]
    training_job = Component(
        name="training_job",
        grants=[
            Grant(
                privileges=[Privilege.SELECT, Privilege.INSERT, Privilege.UPDATE, Privilege.DELETE],
                tables=["embedding", "execution"],
            )
        ],
        policies=[],
    )
    components = [training_job]
    site_names = [AFRO_LA.name_snakecase, DALLAS_FREE_PRESS.name_snakecase]

    for stage in stages:
        # enable extension vector for remote prod and dev dbs
        engine = create_engine(get_conn_string(db_name=stage))
        with engine.connect() as conn:
            enable_extension(conn=conn, extension=Extension(name="vector"))

        # needs this stage's db
        post_table_initialization(stage=stage, components=components)

    logger.info(f"{os.path.relpath(__file__)} done!")
