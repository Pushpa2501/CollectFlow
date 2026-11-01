
import csv
from datetime import date
from pathlib import Path

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models import CollectionCase, DelinquencySnapshot


AS_OF_DATE = date(2026, 10, 31)
REPORT_PATH = Path(
    "results/validation/collection_case_reconciliation.csv"
)


def reconcile():
    changes = []

    with SessionLocal() as db:
        snapshots = {
            snapshot.loan_id: snapshot
            for snapshot in db.scalars(
                select(DelinquencySnapshot).where(
                    DelinquencySnapshot.snapshot_date == AS_OF_DATE
                )
            ).all()
        }

        cases = db.scalars(
            select(CollectionCase)
        ).all()

        for case in cases:
            snapshot = snapshots.get(case.loan_id)

            if snapshot is None:
                raise ValueError(
                    f"Missing October snapshot: {case.loan_id}"
                )

            if case.overdue_amount != snapshot.overdue_amount:
                changes.append({
                    "case_id": case.case_id,
                    "loan_id": case.loan_id,
                    "old_overdue": str(case.overdue_amount),
                    "new_overdue": str(snapshot.overdue_amount),
                    "reason": "SNAPSHOT_RECONCILIATION",
                })

                case.overdue_amount = snapshot.overdue_amount

        REPORT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with REPORT_PATH.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "case_id",
                    "loan_id",
                    "old_overdue",
                    "new_overdue",
                    "reason",
                ],
            )

            writer.writeheader()
            writer.writerows(changes)

        db.commit()

    print("\n=== COLLECTION CASE RECONCILIATION ===")
    print(f"Cases checked: {len(cases)}")
    print(f"Cases updated: {len(changes)}")
    print(f"Audit report: {REPORT_PATH}")
    print("Completed successfully!")


if __name__ == "__main__":
    reconcile()
