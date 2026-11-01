
import random
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models.collection_case import CollectionCase
from backend.models.contact_preference import ContactPreference
from backend.models.contact_attempt import ContactAttempt


RANDOM_SEED = 42
REFERENCE_DATE = datetime(2026, 10, 31, 12, 0)
LOCAL_TIMEZONE = ZoneInfo("Asia/Kolkata")


def check_compliance(preference, channel, contact_datetime):
    local_time = contact_datetime.astimezone(
        ZoneInfo(preference.timezone_name)
    )

    if preference.do_not_contact:
        return "VIOLATION", "DO_NOT_CONTACT"

    allowed_channels = {
        "CALL": preference.allow_calls,
        "SMS": preference.allow_sms,
        "EMAIL": preference.allow_email,
    }

    if not allowed_channels.get(channel, False):
        return "VIOLATION", "CHANNEL_NOT_ALLOWED"

    if not (
        preference.allowed_start_hour
        <= local_time.hour
        < preference.allowed_end_hour
    ):
        return "VIOLATION", "OUTSIDE_ALLOWED_HOURS"

    return "COMPLIANT", None


def generate_contact_attempts():
    rng = random.Random(RANDOM_SEED)

    with SessionLocal() as db:
        cases = db.scalars(
            select(CollectionCase).order_by(
                CollectionCase.case_id
            )
        ).all()

        preferences = {
            p.customer_id: p
            for p in db.scalars(
                select(ContactPreference)
            ).all()
        }

        existing_ids = set(
            db.scalars(
                select(ContactAttempt.attempt_id)
            ).all()
        )

        attempts = []
        violation_counts = {}

        for case in cases:
            preference = preferences.get(case.customer_id)

            if preference is None:
                raise ValueError(
                    f"Missing preference: {case.customer_id}"
                )

            # Generate three attempts for each collection case.
            for attempt_number in range(1, 4):
                attempt_id = (
                    f"ATT{case.loan_id[4:]}"
                    f"{attempt_number:03d}"
                )

                if attempt_id in existing_ids:
                    continue

                channel = rng.choice(
                    ["CALL", "SMS", "EMAIL"]
                )

                # Most attempts occur during normal working hours.
                # Some occur outside permitted hours for testing.
                hour = rng.choices(
                    [10, 12, 15, 17, 20, 22],
                    weights=[25, 25, 20, 15, 10, 5],
                    k=1
                )[0]

                day_offset = rng.randint(0, 20)

                local_datetime = (
                    REFERENCE_DATE
                    - timedelta(days=day_offset)
                ).replace(
                    hour=hour,
                    minute=rng.choice([0, 15, 30, 45]),
                    tzinfo=LOCAL_TIMEZONE
                )

                contact_datetime = (
                    local_datetime.astimezone(timezone.utc)
                )

                compliance_status, reason = check_compliance(
                    preference,
                    channel,
                    contact_datetime
                )

                attempt = ContactAttempt(
                    attempt_id=attempt_id,
                    loan_id=case.loan_id,
                    customer_id=case.customer_id,
                    contact_datetime=contact_datetime,
                    channel=channel,
                    attempt_status="COMPLETED",
                    outcome=rng.choice(
                        ["ANSWERED", "NO_ANSWER", "FOLLOW_UP"]
                    ),
                    compliance_status=compliance_status,
                    violation_reason=reason,
                    created_at=contact_datetime,
                )

                attempts.append(attempt)

                if reason:
                    violation_counts[reason] = (
                        violation_counts.get(reason, 0) + 1
                    )

        try:
            db.add_all(attempts)
            db.commit()
        except Exception:
            db.rollback()
            raise

        print("=== CONTACT ATTEMPT GENERATION ===")
        print(f"Collection cases: {len(cases)}")
        print(f"Contact attempts inserted: {len(attempts)}")
        print(
            "Compliant attempts:",
            sum(
                a.compliance_status == "COMPLIANT"
                for a in attempts
            )
        )
        print(
            "Violating attempts:",
            sum(
                a.compliance_status == "VIOLATION"
                for a in attempts
            )
        )

        for reason, count in sorted(violation_counts.items()):
            print(f"{reason}: {count}")

        print("Contact attempt generation completed!")


if __name__ == "__main__":
    generate_contact_attempts()
