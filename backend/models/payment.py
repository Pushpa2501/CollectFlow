
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    String, DateTime, Numeric,
    ForeignKey, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


class Payment(Base):
    __tablename__ = "payments"

    payment_id: Mapped[str] = mapped_column(
        String(30), primary_key=True
    )

    loan_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("loans.loan_id"),
        nullable=False,
        index=True
    )

    installment_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("installments.installment_id"),
        nullable=False,
        index=True
    )

    payment_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False
    )

    payment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    payment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="COMPLETED"
    )

    payment_method: Mapped[str] = mapped_column(
        String(30), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    installment = relationship(
        "Installment",
        back_populates="payments"
    )

    __table_args__ = (
        CheckConstraint(
            "payment_amount > 0",
            name="check_positive_payment_amount"
        ),
        CheckConstraint(
            "payment_status IN "
            "('PENDING', 'COMPLETED', 'FAILED', 'REVERSED')",
            name="check_payment_status"
        ),
    )
