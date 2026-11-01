
import random
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select, func

from backend.database.connection import SessionLocal
from backend.models import CollectionCase, PromiseToPay


SEED = 42
REFERENCE_DATE = date(2026, 10, 31)


def money(value):
    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def scale_promises():
    inserted = 0
    skipped_existing = 0
    skipped_not_selected = 0

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

        existing_promise_ids = set(
            db.scalars(
                select(PromiseToPay.promise_id)
            ).all()
        )

        batch = []

        for case in cases:
            if case.loan_id in existing_loan_ids:
                skipped_existing += 1
                continue

            loan_number = int(case.loan_id[4:])
            rng = random.Random(SEED + loan_number)

            # Approximately 70% of eligible cases
            # receive a synthetic promise.
            if rng.random() >= 0.70:
                skipped_not_selected += 1
                continue

            if case.overdue_amount <= Decimal("0.00"):
                skipped_not_selected += 1
                continue

            promise_id = f"PROM{loan_number:06d}"

            if promise_id in existing_promise_ids:
                raise ValueError(
                    f"Promise ID collision: {promise_id}"
                )

            fraction = rng.choice([
                Decimal("0.25"),
                Decimal("0.50"),
                Decimal("0.75"),
                Decimal("1.00"),
            ])

            promised_amount = money(
                case.overdue_amount * fraction
            )

            if promised_amount <= 0:
                skipped_not_selected += 1
                continue

            promise_date = (
                REFERENCE_DATE
                - timedelta(days=rng.randint(5, 20))
            )

            promised_payment_date = (
                promise_date
                + timedelta(days=rng.randint(1, 7))
            )

            promise_status = rng.choice([
                "ACTIVE",
                "FULFILLED",
                "BROKEN",
            ])

            # These are simulated outcomes, not
            # independently reconciled payment events.
            actual_paid_amount = (
                promised_amount
                if promise_status == "FULFILLED"
                else Decimal("0.00")
            )

            promise = PromiseToPay(
                promise_id=promise_id,
                loan_id=case.loan_id,
                customer_id=case.customer_id,
                promise_date=promise_date,
                promised_payment_date=promised_payment_date,
                promised_amount=promised_amount,
                promise_status=promise_status,
                actual_paid_amount=actual_paid_amount,
            )

            batch.append(promise)
            existing_loan_ids.add(case.loan_id)
            existing_promise_ids.add(promise_id)

            if len(batch) >= 500:
                db.add_all(batch)
                db.commit()
                inserted += len(batch)
                batch.clear()

        if batch:
            db.add_all(batch)
            db.commit()
            inserted += len(batch)

        total = db.scalar(
            select(func.count())
            .select_from(PromiseToPay)
        )

    print("\n=== PROMISE SCALING SUMMARY ===")
    print(f"Collection cases processed: {len(cases)}")
    print(f"New promises inserted: {inserted}")
    print(f"Existing promises preserved: {skipped_existing}")
    print(f"Cases not selected: {skipped_not_selected}")
    print(f"Total promises: {total}")
    print("Promise scaling completed!")


if __name__ == "__main__":
    scale_promises()
