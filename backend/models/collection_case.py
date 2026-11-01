
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    String,
    Integer,
    Date,
    DateTime,
    Numeric,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


class CollectionCase(Base):
    __tablename__ = "collection_cases"

    case_id: Mapped[str] = mapped_column(
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

    opened_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    closed_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    case_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN"
    )

    priority_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    overdue_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    assigned_agent: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True
    )

    dispute_flag: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )

    hardship_flag: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "priority_score >= 0 AND priority_score <= 100",
            name="check_priority_score"
        ),
        CheckConstraint(
            "overdue_amount >= 0",
            name="check_case_overdue_amount"
        ),
        CheckConstraint(
            "case_status IN "
            "('OPEN', 'IN_PROGRESS', 'ON_HOLD', 'CLOSED')",
            name="check_collection_case_status"
        ),
        CheckConstraint(
            "closed_date IS NULL OR closed_date >= opened_date",
            name="check_case_dates"
        ),
    )
