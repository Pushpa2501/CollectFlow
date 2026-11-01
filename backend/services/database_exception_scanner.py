
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models import (
    Loan,
    Installment,
    Payment,
    CollectionCase,
    ContactAttempt,
    ContactPreference,
    PromiseToPay,
)
from backend.services.exception_detector import detect_exceptions


def add_findings(
    findings,
    record,
    entity_type,
    entity_id,
    loan_id,
):
    for code in detect_exceptions(record):
        findings.append({
            "entity_type": entity_type,
            "entity_id": entity_id,
            "loan_id": loan_id,
            "exception_code": code,
        })


def local_contact_hour(contact_datetime, timezone_name):
    """
    Convert a contact timestamp to the customer's
    configured timezone.

    Existing SQLite timestamps are interpreted as UTC
    if timezone information is absent.
    """
    if contact_datetime.tzinfo is None:
        contact_datetime = contact_datetime.replace(
            tzinfo=ZoneInfo("UTC")
        )

    return contact_datetime.astimezone(
        ZoneInfo(timezone_name or "Asia/Kolkata")
    ).hour


def scan_collection_cases(db, findings):
    records = db.execute(
        select(Loan, CollectionCase)
        .join(
            CollectionCase,
            Loan.loan_id == CollectionCase.loan_id
        )
    ).all()

    for loan, case in records:
        add_findings(
            findings,
            {
                "loan_status": loan.loan_status,
                "case_status": case.case_status,
            },
            "CollectionCase",
            case.case_id,
            loan.loan_id,
        )

    return len(records)


def scan_contacts(db, findings):
    records = db.execute(
        select(ContactAttempt, ContactPreference)
        .join(
            ContactPreference,
            ContactAttempt.customer_id
            == ContactPreference.customer_id
        )
    ).all()

    for attempt, preference in records:
        hour = local_contact_hour(
            attempt.contact_datetime,
            preference.timezone_name,
        )

        add_findings(
            findings,
            {
                "contact_hour": hour,
                "allowed_start_hour":
                    preference.allowed_start_hour,
                "allowed_end_hour":
                    preference.allowed_end_hour,
            },
            "ContactAttempt",
            attempt.attempt_id,
            attempt.loan_id,
        )

    return len(records)


def scan_payments(db, findings):
    records = db.execute(
        select(Payment, Installment)
        .join(
            Installment,
            Payment.installment_id
            == Installment.installment_id
        )
    ).all()

    for payment, installment in records:
        add_findings(
            findings,
            {
                "payment_loan_id": payment.loan_id,
                "installment_loan_id":
                    installment.loan_id,
            },
            "Payment",
            payment.payment_id,
            payment.loan_id,
        )

    return len(records)


def scan_promises(db, findings):
    records = db.execute(
        select(PromiseToPay, CollectionCase)
        .join(
            CollectionCase,
            PromiseToPay.loan_id
            == CollectionCase.loan_id
        )
    ).all()

    for promise, case in records:
        add_findings(
            findings,
            {
                "promised_amount":
                    promise.promised_amount,
                "overdue_amount":
                    case.overdue_amount,
            },
            "PromiseToPay",
            promise.promise_id,
            promise.loan_id,
        )

    return len(records)


def scan_disputes(db, findings):
    records = db.scalars(
        select(CollectionCase)
    ).all()

    for case in records:
        # Provisional proxy:
        # an open disputed case is flagged for review.
        #
        # The schema does not yet contain an explicit
        # debt_confirmed field.
        # Therefore, this is NOT definitive evidence
        # that a disputed debt was confirmed.
        if case.dispute_flag and case.case_status == "OPEN":
            findings.append({
                "entity_type": "CollectionCase",
                "entity_id": case.case_id,
                "loan_id": case.loan_id,
                "exception_code":
                    "DISPUTED_CASE_REQUIRES_REVIEW",
            })

    return len(records)


def scan_database():
    findings = []

    with SessionLocal() as db:
        counts = {
            "collection_cases":
                scan_collection_cases(db, findings),
            "contact_attempts":
                scan_contacts(db, findings),
            "payments":
                scan_payments(db, findings),
            "promises":
                scan_promises(db, findings),
            "dispute_checks":
                scan_disputes(db, findings),
        }

    return findings, counts


if __name__ == "__main__":
    findings, counts = scan_database()

    print("=== COLLECTFLOW DATABASE EXCEPTION SCAN ===")

    for entity, count in counts.items():
        print(f"{entity}: {count}")

    print(f"\nTotal findings: {len(findings)}")

    summary = Counter(
        item["exception_code"]
        for item in findings
    )

    print("\n=== FINDINGS BY CATEGORY ===")

    if not summary:
        print("No findings detected.")

    for code, count in sorted(summary.items()):
        print(f"{code}: {count}")

    print("\n=== SAMPLE FINDINGS ===")

    for finding in findings[:10]:
        print(finding)

    print("\nDatabase scan completed!")
