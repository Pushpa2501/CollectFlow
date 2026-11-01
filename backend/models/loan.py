
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    String, Integer, Date, DateTime,
    Numeric, ForeignKey, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


class Loan(Base):
    __tablename__ = "loans"

    loan_id: Mapped[str] = mapped_column(
        String(30), primary_key=True
    )

    account_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("accounts.account_id"),
        nullable=False,
        index=True
    )

    principal_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False
    )

    annual_interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(6, 3), nullable=False
    )

    tenure_months: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    start_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    maturity_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    loan_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVE"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    account = relationship(
        "Account",
        back_populates="loans"
    )

    __table_args__ = (
        CheckConstraint(
            "principal_amount > 0",
            name="check_positive_principal"
        ),
        CheckConstraint(
            "annual_interest_rate >= 0",
            name="check_nonnegative_interest"
        ),
        CheckConstraint(
            "tenure_months > 0",
            name="check_positive_tenure"
        ),
        CheckConstraint(
            "maturity_date > start_date",
            name="check_loan_dates"
        ),
        CheckConstraint(
            "loan_status IN ('ACTIVE', 'DELINQUENT', 'PAID_OFF', 'DEFAULTED')",
            name="check_loan_status"
        ),
    )
