
from datetime import datetime, timezone

from sqlalchemy import (
    String, DateTime, ForeignKey, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(
        String(30), primary_key=True
    )

    customer_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("customers.customer_id"),
        nullable=False,
        index=True
    )

    account_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )

    account_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVE"
    )

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    customer = relationship(
        "Customer",
        back_populates="accounts"
    )

    loans = relationship(
        "Loan",
        back_populates="account"
    )

    __table_args__ = (
        CheckConstraint(
            "account_status IN ('ACTIVE', 'CLOSED', 'SUSPENDED')",
            name="check_account_status"
        ),
    )
