from datetime import UTC, datetime

from sqlalchemy import String, Integer, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now():
    return datetime.now(UTC).replace(tzinfo=None)


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    phone: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

   
    years_experience: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now
    )

    skills: Mapped[str] = mapped_column(
    String,
    nullable=True
    )

    resume_path: Mapped[str] = mapped_column(
    String(255),
    nullable=True
)

    education: Mapped[list] = mapped_column(
        JSON,
        nullable=True
    )

    projects: Mapped[list] = mapped_column(
        JSON,
        nullable=True
    )

    certifications: Mapped[list] = mapped_column(
        JSON,
        nullable=True
    )

    work_history: Mapped[list] = mapped_column(
        JSON,
        nullable=True
    )

    source_text: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    extraction_metadata: Mapped[dict] = mapped_column(
        JSON,
        nullable=True
    )

    pipeline_stage: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="new"
    )

    recruiter_notes: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
