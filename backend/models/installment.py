
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    String, Integer, Date, Numeric,
    ForeignKey, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


class Installment(Base):
    __tablename__ = "installments"

    installment_id: Mapped[str] = mapped_column(
        String(30), primary_key=True
    )

    loan_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("loans.loan_id"),
        nullable=False,
        index=True
    )

    installment_number: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    due_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    due_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False
    )

    installment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING"
    )

    payments = relationship(
        "Payment",
        back_populates="installment"
    )

    __table_args__ = (
        UniqueConstraint(
            "loan_id",
            "installment_number",
            name="uq_loan_installment_number"
        ),
        CheckConstraint(
            "installment_number > 0",
            name="check_installment_number"
        ),
        CheckConstraint(
            "due_amount > 0",
            name="check_positive_due_amount"
        ),
        CheckConstraint(
            "installment_status IN "
            "('PENDING', 'PARTIAL', 'PAID', 'OVERDUE')",
            name="check_installment_status"
        ),
    )
