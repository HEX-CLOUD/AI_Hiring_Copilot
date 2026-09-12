from datetime import UTC, datetime

from sqlalchemy import String, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now():
    return datetime.now(UTC).replace(tzinfo=None)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )

    description: Mapped[str] = mapped_column(
        String,
        nullable=True
    )

    min_experience: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )

    skills: Mapped[list] = mapped_column(
        JSON,
        nullable=False
    )

    requirements: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list
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
