"""add job description and updated at

Revision ID: cd7a19e42f03
Revises: b1f4d2c8a901
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "cd7a19e42f03"
down_revision: Union[str, Sequence[str], None] = "b1f4d2c8a901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("description", sa.String(), nullable=True),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.alter_column("jobs", "updated_at", server_default=None)


def downgrade() -> None:
    op.drop_column("jobs", "updated_at")
    op.drop_column("jobs", "description")
