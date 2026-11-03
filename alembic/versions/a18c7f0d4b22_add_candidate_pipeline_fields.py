"""add candidate pipeline fields

Revision ID: a18c7f0d4b22
Revises: d7c42a9e1f10
Create Date: 2026-10-22 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a18c7f0d4b22"
down_revision: Union[str, Sequence[str], None] = "d7c42a9e1f10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "candidates",
        sa.Column(
            "pipeline_stage",
            sa.String(length=32),
            nullable=False,
            server_default="new",
        ),
    )
    op.add_column("candidates", sa.Column("recruiter_notes", sa.Text(), nullable=True))
    op.alter_column("candidates", "pipeline_stage", server_default=None)


def downgrade() -> None:
    op.drop_column("candidates", "recruiter_notes")
    op.drop_column("candidates", "pipeline_stage")
