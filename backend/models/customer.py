
from datetime import datetime, timezone

from sqlalchemy import (
    String, Integer, DateTime, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(
        String(30), primary_key=True
    )

    full_name: Mapped[str] = mapped_column(
        String(120), nullable=False
    )

    age: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    region: Mapped[str] = mapped_column(
        String(60), nullable=False
    )

    customer_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVE"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    accounts = relationship(
        "Account",
        back_populates="customer"
    )

    __table_args__ = (
        CheckConstraint(
            "age >= 18 AND age <= 100",
            name="check_customer_age"
        ),
        CheckConstraint(
            "customer_status IN ('ACTIVE', 'INACTIVE')",
            name="check_customer_status"
        ),
    )
    contact_preference = relationship(
    "ContactPreference",
    back_populates="customer",
    uselist=False
)
