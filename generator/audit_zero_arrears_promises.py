
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models import (
    CollectionCase,
    DelinquencySnapshot,
    PromiseToPay,
)


AS_OF_DATE = date(2026, 10, 31)
ZERO = Decimal("0.00")


def audit():
    with SessionLocal() as db:
        cases = {
            case.loan_id: case
            for case in db.scalars(
                select(CollectionCase)
            ).all()
        }

        snapshots = {
            snapshot.loan_id: snapshot
            for snapshot in db.scalars(
                select(DelinquencySnapshot).where(
                    DelinquencySnapshot.snapshot_date == AS_OF_DATE
                )
            ).all()
        }

        promises = db.scalars(
            select(PromiseToPay)
        ).all()

        zero_arrears = []
        excessive_promises = []

        for promise in promises:
            snapshot = snapshots.get(promise.loan_id)
            case = cases.get(promise.loan_id)

            if snapshot is None or case is None:
                continue

            if snapshot.overdue_amount <= ZERO:
                zero_arrears.append(
                    (
                        promise.promise_id,
                        promise.loan_id,
                        str(promise.promised_amount),
                        promise.promise_status,
                        str(promise.actual_paid_amount),
                        str(snapshot.overdue_amount),
                    )
                )

            elif promise.promised_amount > snapshot.overdue_amount:
                excessive_promises.append(
                    promise.promise_id
                )

        print("\n=== ZERO-ARREARS PROMISE AUDIT ===")
        print(f"Total promises: {len(promises)}")
        print(
            "Promises linked to zero-arrears loans:",
            len(zero_arrears),
        )
        print(
            "Promises exceeding positive arrears:",
            len(excessive_promises),
        )

        print("\nZero-arrears promise details:")

        for item in zero_arrears[:20]:
            print(
                "Promise:", item[0],
                "| Loan:", item[1],
                "| Promised:", item[2],
                "| Status:", item[3],
                "| Recorded paid:", item[4],
                "| Corrected arrears:", item[5],
            )


if __name__ == "__main__":
    audit()
