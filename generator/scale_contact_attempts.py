
import random
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select, func

from backend.database.connection import SessionLocal
from backend.models import (
    CollectionCase,
    ContactAttempt,
    ContactPreference,
)


SEED = 42
IST = ZoneInfo("Asia/Kolkata")
CHANNELS = ["CALL", "SMS", "EMAIL"]
CONTACT_HOURS = [8, 9, 10, 11, 14, 16, 17, 19, 20, 22]


def check_compliance(preference, channel, local_hour):
    reasons = []

    if preference.do_not_contact:
        reasons.append("DO_NOT_CONTACT")

    if not (
        preference.allowed_start_hour
        <= local_hour
        < preference.allowed_end_hour
    ):
        reasons.append("OUTSIDE_ALLOWED_HOURS")

    permissions = {
        "CALL": preference.allow_calls,
        "SMS": preference.allow_sms,
        "EMAIL": preference.allow_email,
    }

    if not permissions.get(channel, False):
        reasons.append("CHANNEL_NOT_ALLOWED")

    return (
        "VIOLATION" if reasons else "COMPLIANT",
        ";".join(reasons) if reasons else None,
    )


def scale_contact_attempts():
    inserted = 0
    skipped = 0

    with SessionLocal() as db:
        cases = db.scalars(
            select(CollectionCase)
            .order_by(CollectionCase.case_id)
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

        batch = []

        for case in cases:
            preference = preferences.get(case.customer_id)

            if preference is None:
                raise ValueError(
                    f"Missing preference for {case.customer_id}"
                )

            loan_number = int(case.loan_id[4:])

            for attempt_number in range(1, 4):
                attempt_id = (
                    f"ATT{loan_number:06d}"
                    f"{attempt_number:03d}"
                )

                if attempt_id in existing_ids:
                    skipped += 1
                    continue

                rng = random.Random(
                    SEED + loan_number * 10 + attempt_number
                )

                channel = rng.choice(CHANNELS)
                hour = rng.choice(CONTACT_HOURS)
                minute = rng.randrange(0, 60)

                # Generate a local IST timestamp, then
                # convert to UTC for database storage.
                local_datetime = datetime(
                    2026, 10, 1,
                    hour, minute,
                    tzinfo=IST,
                ) + timedelta(days=rng.randrange(0, 30))

                utc_datetime = local_datetime.astimezone(
                    timezone.utc
                )

                compliance, reason = check_compliance(
                    preference,
                    channel,
                    local_datetime.hour,
                )

                attempt = ContactAttempt(
                    attempt_id=attempt_id,
                    loan_id=case.loan_id,
                    customer_id=case.customer_id,
                    contact_datetime=utc_datetime,
                    channel=channel,
                    attempt_status="COMPLETED",
                    outcome=rng.choice([
                        "NO_ANSWER",
                        "CONNECTED",
                        "CALL_BACK",
                    ]),
                    compliance_status=compliance,
                    violation_reason=reason,
                )

                batch.append(attempt)
                existing_ids.add(attempt_id)

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
            .select_from(ContactAttempt)
        )

        violations = db.scalar(
            select(func.count())
            .select_from(ContactAttempt)
            .where(
                ContactAttempt.compliance_status == "VIOLATION"
            )
        )

    print("\n=== CONTACT ATTEMPT SCALING SUMMARY ===")
    print(f"Collection cases processed: {len(cases)}")
    print(f"New attempts inserted: {inserted}")
    print(f"Existing attempts preserved: {skipped}")
    print(f"Total contact attempts: {total}")
    print(f"Compliance violations: {violations}")
    print("Contact attempt scaling completed!")


if __name__ == "__main__":
    scale_contact_attempts()
