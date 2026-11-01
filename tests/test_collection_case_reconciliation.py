
from datetime import date

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models import (
    CollectionCase,
    DelinquencySnapshot,
)


AS_OF_DATE = date(2026, 10, 31)


def test_collection_case_reconciliation():
    with SessionLocal() as db:
        cases = db.scalars(
            select(CollectionCase)
        ).all()

        snapshots = {
            snapshot.loan_id: snapshot
            for snapshot in db.scalars(
                select(DelinquencySnapshot).where(
                    DelinquencySnapshot.snapshot_date == AS_OF_DATE
                )
            ).all()
        }

        assert cases, "No collection cases found"

        missing_snapshots = []
        overdue_mismatches = []

        for case in cases:
            snapshot = snapshots.get(case.loan_id)

            if snapshot is None:
                missing_snapshots.append(case.loan_id)
                continue

            if case.overdue_amount != snapshot.overdue_amount:
                overdue_mismatches.append(
                    (
                        case.case_id,
                        case.loan_id,
                        str(case.overdue_amount),
                        str(snapshot.overdue_amount),
                    )
                )

        print("\n=== COLLECTION CASE INTEGRITY ===")
        print(f"Cases checked: {len(cases)}")
        print(
            f"Missing snapshots: {len(missing_snapshots)}"
        )
        print(
            f"Overdue mismatches: {len(overdue_mismatches)}"
        )

        for mismatch in overdue_mismatches[:5]:
            print("Mismatch:", mismatch)

        assert not missing_snapshots, (
            f"{len(missing_snapshots)} cases have "
            "no October snapshot"
        )

        assert not overdue_mismatches, (
            f"{len(overdue_mismatches)} cases have "
            "incorrect overdue amounts"
        )

        print("PASS: All collection-case overdue amounts reconciled")
