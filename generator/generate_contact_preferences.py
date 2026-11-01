
import random
from datetime import datetime, timezone

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models.customer import Customer
from backend.models.contact_preference import ContactPreference


RANDOM_SEED = 42
REFERENCE_DATE = datetime(
    2026, 10, 31, 12, 0, tzinfo=timezone.utc
)


def generate_contact_preferences():
    rng = random.Random(RANDOM_SEED)

    with SessionLocal() as db:
        customers = db.scalars(
            select(Customer).order_by(Customer.customer_id)
        ).all()

        existing_customer_ids = set(
            db.scalars(
                select(ContactPreference.customer_id)
            ).all()
        )

        preferences = []

        for customer in customers:
            if customer.customer_id in existing_customer_ids:
                continue

            do_not_contact = rng.random() < 0.05

            allow_calls = rng.random() < 0.85
            allow_sms = rng.random() < 0.90
            allow_email = rng.random() < 0.75

            allowed_channels = []

            if allow_calls:
                allowed_channels.append("CALL")

            if allow_sms:
                allowed_channels.append("SMS")

            if allow_email:
                allowed_channels.append("EMAIL")

            if not allowed_channels:
                preferred_channel = "CALL"
            else:
                preferred_channel = rng.choice(
                    allowed_channels
                )

            preference = ContactPreference(
                preference_id=(
                    f"PREF{customer.customer_id[4:]}"
                ),
                customer_id=customer.customer_id,
                allow_calls=allow_calls,
                allow_sms=allow_sms,
                allow_email=allow_email,
                preferred_channel=preferred_channel,
                allowed_start_hour=9,
                allowed_end_hour=18,
                timezone_name="Asia/Kolkata",
                do_not_contact=do_not_contact,
                updated_at=REFERENCE_DATE,
            )

            preferences.append(preference)

        try:
            db.add_all(preferences)
            db.commit()
        except Exception:
            db.rollback()
            raise

        print("=== CONTACT PREFERENCE GENERATION ===")
        print(f"Customers processed: {len(customers)}")
        print(f"Preferences inserted: {len(preferences)}")
        print(
            "Do-not-contact customers: "
            f"{sum(p.do_not_contact for p in preferences)}"
        )
        print(
            "Contact preference generation completed!"
        )


if __name__ == "__main__":
    generate_contact_preferences()
