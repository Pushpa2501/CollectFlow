
import csv
from collections import Counter
from pathlib import Path

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models import PromiseToPay


REPORT_PATH = Path(
    "results/validation/historical_promise_validation.csv"
)

EXPECTED_COUNTS = {
    "VALID": 7002,
    "ZERO_HISTORICAL_ARREARS": 6,
    "EXCEEDS_HISTORICAL_ARREARS": 50,
}


def test_historical_promise_validation_report():
    assert REPORT_PATH.exists(), (
        f"Missing validation report: {REPORT_PATH}"
    )

    with REPORT_PATH.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(csv.DictReader(file))

    with SessionLocal() as db:
        promise_ids = set(
            db.scalars(
                select(PromiseToPay.promise_id)
            ).all()
        )

    report_ids = [
        row["promise_id"]
        for row in rows
    ]

    assert len(report_ids) == len(set(report_ids)), (
        "Duplicate promise IDs in report"
    )

    assert set(report_ids) == promise_ids, (
        "Report does not cover every database promise"
    )

    counts = Counter(
        row["validation_result"]
        for row in rows
    )

    print("\n=== HISTORICAL PROMISE VALIDATION ===")
    print(f"Promises covered: {len(rows)}")

    for result, count in sorted(counts.items()):
        print(f"{result}: {count}")

    assert dict(counts) == EXPECTED_COUNTS, (
        "Historical validation counts differ "
        "from the audited dataset"
    )

    print(
        "PASS: All promises covered and "
        "known exceptions documented"
    )
