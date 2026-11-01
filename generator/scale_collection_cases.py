
from datetime import date
from decimal import Decimal

from sqlalchemy import select, func

from backend.database.connection import SessionLocal
from backend.models import (
    Loan,
    Account,
    DelinquencySnapshot,
    CollectionCase,
)


AS_OF_DATE = date(2026, 10, 31)


def priority_from_dpd(dpd):
    if dpd >= 90:
        return 90
    if dpd >= 60:
        return 70
    if dpd >= 30:
        return 50
    return 30


def scale_collection_cases():
    inserted = 0
    skipped_existing = 0
    skipped_current = 0

    with SessionLocal() as db:
        existing_loan_ids = set(
            db.scalars(
                select(CollectionCase.loan_id)
            ).all()
        )

        records = db.execute(
            select(
                Loan.loan_id,
                Account.customer_id,
                DelinquencySnapshot.days_past_due,
                DelinquencySnapshot.overdue_amount,
            )
            .join(
                Account,
                Loan.account_id == Account.account_id
            )
            .join(
                DelinquencySnapshot,
                Loan.loan_id == DelinquencySnapshot.loan_id
            )
            .where(
                DelinquencySnapshot.snapshot_date == AS_OF_DATE
            )
            .order_by(Loan.loan_id)
        ).all()

        batch = []

        for (
            loan_id,
            customer_id,
            dpd,
            overdue_amount,
        ) in records:

            if loan_id in existing_loan_ids:
                skipped_existing += 1
                continue

            if (
                dpd <= 0
                or overdue_amount <= Decimal("0.00")
            ):
                skipped_current += 1
                continue

            case = CollectionCase(
                case_id=f"CASE{loan_id[4:]}",
                loan_id=loan_id,
                customer_id=customer_id,
                opened_date=AS_OF_DATE,
                case_status="OPEN",
                priority_score=priority_from_dpd(dpd),
                overdue_amount=overdue_amount,
                assigned_agent=(
                    f"AGENT{(int(loan_id[4:]) % 20) + 1:03d}"
                ),
                dispute_flag=False,
                hardship_flag=False,
            )

            batch.append(case)
            existing_loan_ids.add(loan_id)

            if len(batch) >= 500:
                db.add_all(batch)
                db.commit()

                inserted += len(batch)
                print(f"Inserted cases: {inserted}")

                batch.clear()

        if batch:
            db.add_all(batch)
            db.commit()
            inserted += len(batch)

        total = db.scalar(
            select(func.count())
            .select_from(CollectionCase)
        )

    print("\n=== COLLECTION CASE SCALING SUMMARY ===")
    print(f"Loans with snapshots: {len(records)}")
    print(f"New cases inserted: {inserted}")
    print(f"Existing cases preserved: {skipped_existing}")
    print(f"Current loans skipped: {skipped_current}")
    print(f"Total collection cases: {total}")
    print("Collection case scaling completed!")


if __name__ == "__main__":
    scale_collection_cases()
