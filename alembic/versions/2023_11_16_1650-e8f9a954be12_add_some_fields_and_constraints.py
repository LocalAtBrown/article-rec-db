"""add some fields and constraints

Revision ID: e8f9a954be12
Revises: 66844fb0654a # noqa: W291
Create Date: 2023-11-16 16:50:05.113031

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "e8f9a954be12"
down_revision = "66844fb0654a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    sa.Enum(
        "DEFAULT_AKA_NO_SOURCE",
        "SOURCE_TARGET_INTERCHANGEABLE",
        "SOURCE_TARGET_NOT_INTERCHANGEABLE",
        name="strategyrecommendationtype",
    ).create(op.get_bind())
    op.drop_constraint("article_site_id_in_site_key", "article", type_="unique")
    op.create_unique_constraint("article_site_idinsite_unique", "article", ["site", "id_in_site"])
    op.add_column(
        "execution",
        sa.Column(
            "strategy_recommendation_type",
            postgresql.ENUM(
                "DEFAULT_AKA_NO_SOURCE",
                "SOURCE_TARGET_INTERCHANGEABLE",
                "SOURCE_TARGET_NOT_INTERCHANGEABLE",
                name="strategyrecommendationtype",
                create_type=False,
            ),
            nullable=False,
        ),
    )
    op.add_column("recommendation", sa.Column("score", sa.Float(), nullable=False))
    op.create_check_constraint("recommendation_score_between_0_and_1", "recommendation", "score >= 0 AND score <= 1")
    op.create_unique_constraint(
        "recommendation_execution_target_unique", "recommendation", ["execution_id", "target_article_id"]
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("recommendation_execution_target_unique", "recommendation", type_="unique")
    op.drop_constraint("recommendation_score_between_0_and_1", "recommendation", type_="check")
    op.drop_column("recommendation", "score")
    op.drop_column("execution", "strategy_recommendation_type")
    op.drop_constraint("article_site_idinsite_unique", "article", type_="unique")
    op.create_unique_constraint("article_site_id_in_site_key", "article", ["site", "id_in_site"])
    sa.Enum(
        "DEFAULT_AKA_NO_SOURCE",
        "SOURCE_TARGET_INTERCHANGEABLE",
        "SOURCE_TARGET_NOT_INTERCHANGEABLE",
        name="strategyrecommendationtype",
    ).drop(op.get_bind())
    # ### end Alembic commands ###