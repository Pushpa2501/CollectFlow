
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models import PromiseToPay


AS_OF_DATE = date(2026, 10, 31)


def fix_expired_promises():
    expired_count = 0
    marked_broken = 0
    marked_fulfilled = 0

    with SessionLocal() as db:
        expired_promises = db.scalars(
            select(PromiseToPay).where(
                PromiseToPay.promise_status == "ACTIVE",
                PromiseToPay.promised_payment_date <= AS_OF_DATE,
            )
        ).all()

        for promise in expired_promises:
            expired_count += 1

            if (
                promise.actual_paid_amount
                >= promise.promised_amount
                and promise.promised_amount > Decimal("0.00")
            ):
                promise.promise_status = "FULFILLED"
                marked_fulfilled += 1
            else:
                promise.promise_status = "BROKEN"
                marked_broken += 1

        db.commit()

    print("\n=== EXPIRED PROMISE CORRECTION ===")
    print(f"Expired ACTIVE promises found: {expired_count}")
    print(f"Changed to BROKEN: {marked_broken}")
    print(f"Changed to FULFILLED: {marked_fulfilled}")
    print("Correction completed!")


if __name__ == "__main__":
    fix_expired_promises()
