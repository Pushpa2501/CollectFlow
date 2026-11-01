
from datetime import date

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models.loan import Loan
from backend.models.account import Account
from backend.models.delinquency_snapshot import DelinquencySnapshot
from backend.models.collection_case import CollectionCase


AS_OF_DATE = date(2026, 10, 31)


def calculate_priority(dpd, overdue_amount):
    score = 0

    if dpd > 90:
        score += 60
    elif dpd > 60:
        score += 45
    elif dpd > 30:
        score += 30
    elif dpd > 0:
        score += 15

    if overdue_amount >= 50000:
        score += 40
    elif overdue_amount >= 20000:
        score += 25
    elif overdue_amount > 0:
        score += 10

    return min(score, 100)


def generate_collection_cases():
    with SessionLocal() as db:
        records = db.execute(
            select(
                Loan,
                Account,
                DelinquencySnapshot
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

        existing_loan_ids = set(
            db.scalars(
                select(CollectionCase.loan_id)
            ).all()
        )

        cases = []

        for loan, account, snapshot in records:
            if loan.loan_id in existing_loan_ids:
                continue

            if snapshot.overdue_amount <= 0:
                continue

            priority = calculate_priority(
                snapshot.days_past_due,
                snapshot.overdue_amount
            )

            case = CollectionCase(
                case_id=f"CASE{loan.loan_id[4:]}",
                loan_id=loan.loan_id,
                customer_id=account.customer_id,
                opened_date=AS_OF_DATE,
                case_status="OPEN",
                priority_score=priority,
                overdue_amount=snapshot.overdue_amount,
                assigned_agent=None,
                dispute_flag=False,
                hardship_flag=False,
            )

            cases.append(case)

        try:
            db.add_all(cases)
            db.commit()
        except Exception:
            db.rollback()
            raise

        print("=== COLLECTION CASE GENERATION ===")
        print(f"Loans evaluated: {len(records)}")
        print(f"Collection cases inserted: {len(cases)}")
        print("Collection case generation completed!")


if __name__ == "__main__":
    generate_collection_cases()
