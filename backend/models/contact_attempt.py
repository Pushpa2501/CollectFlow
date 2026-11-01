
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


class ContactAttempt(Base):
    __tablename__ = "contact_attempts"

    attempt_id: Mapped[str] = mapped_column(
        String(30),
        primary_key=True
    )

    loan_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("loans.loan_id"),
        nullable=False,
        index=True
    )

    customer_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("customers.customer_id"),
        nullable=False,
        index=True
    )

    contact_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    attempt_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    outcome: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    compliance_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING"
    )

    violation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "channel IN ('CALL', 'SMS', 'EMAIL')",
            name="check_contact_channel"
        ),
        CheckConstraint(
            "attempt_status IN "
            "('SCHEDULED', 'COMPLETED', 'FAILED', 'BLOCKED')",
            name="check_attempt_status"
        ),
        CheckConstraint(
            "compliance_status IN "
            "('PENDING', 'COMPLIANT', 'VIOLATION')",
            name="check_contact_compliance"
        ),
    )
