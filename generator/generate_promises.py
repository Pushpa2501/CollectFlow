
import random
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models.collection_case import CollectionCase
from backend.models.promise_to_pay import PromiseToPay


RANDOM_SEED = 42
AS_OF_DATE = date(2026, 10, 31)
CENT = Decimal("0.01")


def money(value):
    return value.quantize(
        CENT,
        rounding=ROUND_HALF_UP
    )


def generate_promises():
    rng = random.Random(RANDOM_SEED)

    with SessionLocal() as db:
        cases = db.scalars(
            select(CollectionCase)
            .order_by(CollectionCase.case_id)
        ).all()

        existing_loan_ids = set(
            db.scalars(
                select(PromiseToPay.loan_id)
            ).all()
        )

        promises = []
        status_counts = {
            "ACTIVE": 0,
            "FULFILLED": 0,
            "BROKEN": 0,
        }

        for case in cases:
            if case.loan_id in existing_loan_ids:
                continue

            if case.overdue_amount <= 0:
                continue

            # Approximately 70% of cases receive a promise.
            if rng.random() >= 0.70:
                continue

            promise_date = AS_OF_DATE - timedelta(
                days=rng.randint(5, 30)
            )

            promised_payment_date = (
                promise_date
                + timedelta(days=rng.randint(3, 15))
            )

            fraction = Decimal(
                str(rng.choice([0.25, 0.50, 0.75, 1.00]))
            )

            promised_amount = money(
                case.overdue_amount * fraction
            )

            # Never exceed the case's overdue amount.
            promised_amount = min(
                promised_amount,
                case.overdue_amount
            )

            if promised_amount <= 0:
                continue

            if promised_payment_date > AS_OF_DATE:
                status = "ACTIVE"
                actual_paid_amount = Decimal("0.00")
            else:
                fulfilled = rng.random() < 0.55

                if fulfilled:
                    status = "FULFILLED"
                    actual_paid_amount = promised_amount
                else:
                    status = "BROKEN"
                    actual_paid_amount = money(
                        promised_amount * Decimal(
                            str(rng.choice([0, 0.25, 0.50]))
                        )
                    )

            promise = PromiseToPay(
                promise_id=f"PTP{case.loan_id[4:]}",
                loan_id=case.loan_id,
                customer_id=case.customer_id,
                promise_date=promise_date,
                promised_payment_date=promised_payment_date,
                promised_amount=promised_amount,
                promise_status=status,
                actual_paid_amount=actual_paid_amount,
            )

            promises.append(promise)
            status_counts[status] += 1

        try:
            db.add_all(promises)
            db.commit()
        except Exception:
            db.rollback()
            raise

        print("=== PROMISE-TO-PAY GENERATION ===")
        print(f"Collection cases processed: {len(cases)}")
        print(f"Promises inserted: {len(promises)}")

        for status, count in status_counts.items():
            print(f"{status}: {count}")

        print("Promise generation completed successfully!")


if __name__ == "__main__":
    generate_promises()
