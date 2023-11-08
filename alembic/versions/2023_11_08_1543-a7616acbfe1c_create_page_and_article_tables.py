"""create page and article tables

Revision ID: a7616acbfe1c
Revises: # noqa: W291
Create Date: 2023-11-08 15:43:49.135624

"""
import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision = "a7616acbfe1c"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "page",
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("db_created_at", sa.DateTime(), nullable=False),
        sa.Column("db_updated_at", sa.DateTime(), nullable=True),
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column(
            "article_exclude_reason",
            sa.Enum(
                "NOT_ARTICLE", "NOT_IN_HOUSE_ARTICLE", "TEST_ARTICLE", "HAS_EXCLUDED_TAG", name="articleexcludereason"
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_table(
        "article",
        sa.Column("site", sa.String(), nullable=True),
        sa.Column("db_created_at", sa.DateTime(), nullable=False),
        sa.Column("db_updated_at", sa.DateTime(), nullable=True),
        sa.Column("page_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("id_in_site", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["page_id"],
            ["page.id"],
        ),
        sa.PrimaryKeyConstraint("page_id"),
        sa.UniqueConstraint("site", "id_in_site"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("article")
    op.drop_table("page")
    # ### end Alembic commands ###