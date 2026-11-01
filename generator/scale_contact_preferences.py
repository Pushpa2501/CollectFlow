
import random

from sqlalchemy import select, func

from backend.database.connection import SessionLocal
from backend.models import Customer, ContactPreference


SEED = 42


def scale_contact_preferences():
    inserted = 0
    skipped = 0

    with SessionLocal() as db:
        customer_ids = db.scalars(
            select(Customer.customer_id)
            .order_by(Customer.customer_id)
        ).all()

        existing_ids = set(
            db.scalars(
                select(ContactPreference.customer_id)
            ).all()
        )

        batch = []

        for customer_id in customer_ids:
            if customer_id in existing_ids:
                skipped += 1
                continue

            # Independent RNG per customer ensures
            # reproducible preferences across reruns.
            customer_number = int(customer_id[4:])
            rng = random.Random(SEED + customer_number)

            allow_calls = rng.random() < 0.85
            allow_sms = rng.random() < 0.90
            allow_email = rng.random() < 0.95
            do_not_contact = rng.random() < 0.05

            allowed_channels = []

            if allow_calls:
                allowed_channels.append("CALL")

            if allow_sms:
                allowed_channels.append("SMS")

            if allow_email:
                allowed_channels.append("EMAIL")

            preferred_channel = (
                rng.choice(allowed_channels)
                if allowed_channels
                else "EMAIL"
            )

            preference = ContactPreference(
                preference_id=(
                    f"PREF{customer_number:06d}"
                ),
                customer_id=customer_id,
                allow_calls=allow_calls,
                allow_sms=allow_sms,
                allow_email=allow_email,
                preferred_channel=preferred_channel,
                allowed_start_hour=9,
                allowed_end_hour=18,
                timezone_name="Asia/Kolkata",
                do_not_contact=do_not_contact,
            )

            batch.append(preference)

            if len(batch) >= 500:
                db.add_all(batch)
                db.commit()
                inserted += len(batch)
                batch.clear()

        if batch:
            db.add_all(batch)
            db.commit()
            inserted += len(batch)

        total = db.scalar(
            select(func.count())
            .select_from(ContactPreference)
        )

        dnc_count = db.scalar(
            select(func.count())
            .select_from(ContactPreference)
            .where(ContactPreference.do_not_contact.is_(True))
        )

    print("\n=== CONTACT PREFERENCE SCALING SUMMARY ===")
    print(f"Customers processed: {len(customer_ids)}")
    print(f"New preferences inserted: {inserted}")
    print(f"Existing preferences preserved: {skipped}")
    print(f"Total contact preferences: {total}")
    print(f"Do-not-contact preferences: {dnc_count}")
    print("Contact preference scaling completed!")


if __name__ == "__main__":
    scale_contact_preferences()
