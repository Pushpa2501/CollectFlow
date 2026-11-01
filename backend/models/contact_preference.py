
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


class ContactPreference(Base):
    __tablename__ = "contact_preferences"

    preference_id: Mapped[str] = mapped_column(
        String(30),
        primary_key=True
    )

    customer_id: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("customers.customer_id"),
        nullable=False,
        unique=True,
        index=True
    )

    allow_calls: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    allow_sms: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    allow_email: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    preferred_channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EMAIL"
    )

    allowed_start_hour: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=9
    )

    allowed_end_hour: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=18
    )

    timezone_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="Asia/Kolkata"
    )

    do_not_contact: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    customer = relationship(
        "Customer",
        back_populates="contact_preference"
    )

    __table_args__ = (
        CheckConstraint(
            "preferred_channel IN ('CALL', 'SMS', 'EMAIL')",
            name="check_preferred_channel"
        ),
        CheckConstraint(
            "allowed_start_hour >= 0 AND allowed_start_hour <= 23",
            name="check_contact_start_hour"
        ),
        CheckConstraint(
            "allowed_end_hour >= 1 AND allowed_end_hour <= 24",
            name="check_contact_end_hour"
        ),
        CheckConstraint(
            "allowed_start_hour < allowed_end_hour",
            name="check_contact_time_range"
        ),
    )
