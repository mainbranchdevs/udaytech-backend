"""add service image url

Revision ID: 7c1b02c91f4a
Revises: cf3a6e132382
Create Date: 2026-02-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c1b02c91f4a"
down_revision: Union[str, None] = "cf3a6e132382"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("services", sa.Column("image_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("services", "image_url")
