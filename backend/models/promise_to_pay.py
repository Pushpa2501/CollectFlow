
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    String,
    Date,
    DateTime,
    Numeric,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class PromiseToPay(Base):
    __tablename__ = "promises_to_pay"

    promise_id: Mapped[str] = mapped_column(
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

    promise_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    promised_payment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    promised_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    promise_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE"
    )

    actual_paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "promised_amount > 0",
            name="check_positive_promise_amount"
        ),
        CheckConstraint(
            "actual_paid_amount >= 0",
            name="check_nonnegative_actual_paid"
        ),
        CheckConstraint(
            "promised_payment_date >= promise_date",
            name="check_promise_dates"
        ),
        CheckConstraint(
            "promise_status IN "
            "('ACTIVE', 'FULFILLED', 'BROKEN', 'CANCELLED')",
            name="check_promise_status"
        ),
    )
