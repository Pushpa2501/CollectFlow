
from collections import Counter

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models import ContactAttempt, ContactPreference
from backend.services.database_exception_scanner import (
    local_contact_hour,
)


def test_contact_compliance_integration():
    with SessionLocal() as db:
        records = db.execute(
            select(ContactAttempt, ContactPreference)
            .join(
                ContactPreference,
                ContactAttempt.customer_id
                == ContactPreference.customer_id
            )
        ).all()

        assert records, "No contact attempts found"

        stored_statuses = Counter()
        stored_reasons = Counter()

        out_of_hours_ids = set()
        stored_violation_ids = set()

        for attempt, preference in records:
            stored_statuses[attempt.compliance_status] += 1

            if attempt.violation_reason:
                stored_reasons[
                    attempt.violation_reason
                ] += 1

            if attempt.compliance_status == "VIOLATION":
                stored_violation_ids.add(attempt.attempt_id)

            hour = local_contact_hour(
                attempt.contact_datetime,
                preference.timezone_name,
            )

            if not (
                preference.allowed_start_hour
                <= hour
                < preference.allowed_end_hour
            ):
                out_of_hours_ids.add(attempt.attempt_id)

        print("\n=== CONTACT COMPLIANCE AUDIT ===")
        print(f"Total attempts: {len(records)}")
        print(f"Stored statuses: {dict(stored_statuses)}")
        print(f"Stored reasons: {dict(stored_reasons)}")
        print(
            "Recalculated out-of-hours:",
            len(out_of_hours_ids),
        )
        print(
            "Out-of-hours also marked VIOLATION:",
            len(
                out_of_hours_ids
                & stored_violation_ids
            ),
        )

        missing_flags = (
            out_of_hours_ids - stored_violation_ids
        )

        print(
            "Out-of-hours not marked VIOLATION:",
            len(missing_flags),
        )

        if missing_flags:
            print(
                "Sample inconsistent attempts:",
                sorted(missing_flags)[:10],
            )

        assert not missing_flags, (
            "Some out-of-hours attempts are not "
            "marked as compliance violations"
        )
