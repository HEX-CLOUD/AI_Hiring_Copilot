"""add candidate job decisions

Revision ID: c94a2e6b0d77
Revises: a18c7f0d4b22
Create Date: 2026-10-22 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c94a2e6b0d77"
down_revision: Union[str, Sequence[str], None] = "a18c7f0d4b22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "candidate_job_decisions" in inspector.get_table_names():
        return

    op.create_table(
        "candidate_job_decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job_decision"),
    )
    op.create_index("ix_candidate_job_decisions_candidate_id", "candidate_job_decisions", ["candidate_id"])
    op.create_index("ix_candidate_job_decisions_job_id", "candidate_job_decisions", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_candidate_job_decisions_job_id", table_name="candidate_job_decisions")
    op.drop_index("ix_candidate_job_decisions_candidate_id", table_name="candidate_job_decisions")
    op.drop_table("candidate_job_decisions")
