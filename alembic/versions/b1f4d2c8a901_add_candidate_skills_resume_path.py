"""add candidate skills and resume path

Revision ID: b1f4d2c8a901
Revises: a88641ad0e8c
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b1f4d2c8a901"
down_revision: Union[str, Sequence[str], None] = "a88641ad0e8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "candidates",
        sa.Column("skills", sa.String(), nullable=True),
    )
    op.add_column(
        "candidates",
        sa.Column("resume_path", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("candidates", "resume_path")
    op.drop_column("candidates", "skills")
