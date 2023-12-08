"""remove sqlmodel annotated and disable page update

Revision ID: e8ee289b5631
Revises: 1feba14fd658 # noqa: W291
Create Date: 2023-12-08 15:26:43.897283

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "e8ee289b5631"
down_revision = "1feba14fd658"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("page", "db_updated_at")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("page", sa.Column("db_updated_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
