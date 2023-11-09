import os

from loguru import logger

from article_rec_db.db.controller import pre_table_initialization
from article_rec_db.db.helpers import Component, Extension, Stage
from article_rec_db.sites import AFRO_LA, DALLAS_FREE_PRESS

if __name__ == "__main__":
    stages = [Stage.DEV, Stage.PROD]
    training_job = Component(
        name="training_job",
        grants=[],
        policies=[],
    )
    components = [training_job]
    site_names = [AFRO_LA.name_snakecase, DALLAS_FREE_PRESS.name_snakecase]

    for stage in stages:
        pre_table_initialization(stage=stage, components=components, extensions=[Extension.VECTOR], site_names=site_names)

    logger.info(f"{os.path.relpath(__file__)} done!")
