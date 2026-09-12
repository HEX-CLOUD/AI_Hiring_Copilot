"""add job requirements experience

Revision ID: f4b72d8c3a11
Revises: cd7a19e42f03
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4b72d8c3a11"
down_revision: Union[str, Sequence[str], None] = "cd7a19e42f03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("min_experience", sa.Integer(), nullable=True),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "requirements",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )
    op.alter_column("jobs", "requirements", server_default=None)


def downgrade() -> None:
    op.drop_column("jobs", "requirements")
    op.drop_column("jobs", "min_experience")
