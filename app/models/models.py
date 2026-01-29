from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# Comentário (pt-BR):
# Este módulo define os modelos de banco de dados usando SQLAlchemy 2.0 (ORM).
# As classes abaixo representam as tabelas principais do sistema:
# - User: usuários do bot (trabalhadores e construtoras)
# - JobOpportunity: oportunidades de trabalho criadas por construtoras


class UserType(str, PyEnum):
    """Domain-level user types."""

    WORKER = "WORKER"
    CONTRACTOR = "CONTRACTOR"


class JobStatus(str, PyEnum):
    """Domain-level status for job opportunities."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    FILLED = "FILLED"


class User(Base):
    """
    User table.

    Represents both workers (pedreiros, eletricistas, etc.) and contractors
    (empresas de construção civil) that interact with the WhatsApp bot.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    phone_number: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
    )

    user_type: Mapped[UserType] = mapped_column(
        Enum(UserType, name="user_type_enum"),
        nullable=False,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    conversation_stage: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="NEW",
    )

    # Relationship: a contractor can own many job opportunities.
    job_opportunities: Mapped[list["JobOpportunity"]] = relationship(
        back_populates="contractor",
        cascade="all, delete-orphan",
    )


class JobOpportunity(Base):
    """
    JobOpportunity table.

    Represents a job posting created by a contractor, which can be matched
    to nearby workers based on location and skills.
    """

    __tablename__ = "job_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )

    payment_offer: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    contractor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum"),
        nullable=False,
        default=JobStatus.OPEN,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    contractor: Mapped[User] = relationship(
        back_populates="job_opportunities",
    )

