
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    String,
    Integer,
    Date,
    Numeric,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


class DelinquencySnapshot(Base):
    __tablename__ = "delinquency_snapshots"

    snapshot_id: Mapped[str] = mapped_column(
        String(30),
        primary_key=True
    )

    loan_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("loans.loan_id"),
        nullable=False,
        index=True
    )

    snapshot_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    days_past_due: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    overdue_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00")
    )

    outstanding_balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False
    )

    delinquency_bucket: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "loan_id",
            "snapshot_date",
            name="uq_loan_snapshot_date"
        ),
        CheckConstraint(
            "days_past_due >= 0",
            name="check_nonnegative_dpd"
        ),
        CheckConstraint(
            "overdue_amount >= 0",
            name="check_nonnegative_overdue"
        ),
        CheckConstraint(
            "outstanding_balance >= 0",
            name="check_nonnegative_balance"
        ),
        CheckConstraint(
            "delinquency_bucket IN "
            "('CURRENT', 'DPD_1_30', 'DPD_31_60', "
            "'DPD_61_90', 'DPD_90_PLUS')",
            name="check_delinquency_bucket"
        ),
    )
