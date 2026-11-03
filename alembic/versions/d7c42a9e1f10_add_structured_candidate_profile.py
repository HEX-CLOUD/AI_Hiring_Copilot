"""add structured candidate profile fields

Revision ID: d7c42a9e1f10
Revises: b1f4d2c8a901
Create Date: 2026-10-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7c42a9e1f10"
down_revision: Union[str, Sequence[str], None] = "f4b72d8c3a11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("education", sa.JSON(), nullable=True))
    op.add_column("candidates", sa.Column("projects", sa.JSON(), nullable=True))
    op.add_column("candidates", sa.Column("certifications", sa.JSON(), nullable=True))
    op.add_column("candidates", sa.Column("work_history", sa.JSON(), nullable=True))
    op.add_column("candidates", sa.Column("source_text", sa.Text(), nullable=True))
    op.add_column(
        "candidates",
        sa.Column("extraction_metadata", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("candidates", "extraction_metadata")
    op.drop_column("candidates", "source_text")
    op.drop_column("candidates", "work_history")
    op.drop_column("candidates", "certifications")
    op.drop_column("candidates", "projects")
    op.drop_column("candidates", "education")
