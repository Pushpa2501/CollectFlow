
import random
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models.installment import Installment
from backend.models.payment import Payment


RANDOM_SEED = 42
AS_OF_DATE = datetime(2026, 10, 31, 23, 59, 59, tzinfo=timezone.utc)
CENT = Decimal("0.01")


def money(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def generate_payments():
    rng = random.Random(RANDOM_SEED)

    with SessionLocal() as db:
        installments = db.scalars(
            select(Installment).order_by(Installment.installment_id)
        ).all()

        existing_installments = set(
            db.scalars(select(Payment.installment_id)).all()
        )

        payments = []
        counts = {
            "ON_TIME": 0,
            "LATE": 0,
            "PARTIAL": 0,
            "MISSED": 0,
            "FUTURE": 0,
            "EXISTING": 0,
        }

        for installment in installments:
            if installment.installment_id in existing_installments:
                counts["EXISTING"] += 1
                continue

            due_datetime = datetime.combine(
                installment.due_date,
                time(12, 0),
                tzinfo=timezone.utc
            )

            if due_datetime > AS_OF_DATE:
                counts["FUTURE"] += 1
                continue

            scenario = rng.choices(
                ["ON_TIME", "LATE", "PARTIAL", "MISSED"],
                weights=[55, 15, 15, 15],
                k=1
            )[0]

            if scenario == "MISSED":
                counts["MISSED"] += 1
                continue

            if scenario == "ON_TIME":
                payment_datetime = due_datetime - timedelta(
                    days=rng.randint(0, 3)
                )
                amount = installment.due_amount

            elif scenario == "LATE":
                payment_datetime = due_datetime + timedelta(
                    days=rng.randint(1, 20)
                )
                amount = installment.due_amount

            else:
                payment_datetime = due_datetime + timedelta(
                    days=rng.randint(0, 10)
                )

                fraction = Decimal(
                    str(rng.choice([0.25, 0.50, 0.75]))
                )

                amount = money(
                    installment.due_amount * fraction
                )

            # Do not create payments after the simulation cutoff.
            if payment_datetime > AS_OF_DATE:
                counts["FUTURE"] += 1
                continue

            payment = Payment(
                payment_id=f"PAY{installment.installment_id[4:]}",
                loan_id=installment.loan_id,
                installment_id=installment.installment_id,
                payment_amount=amount,
                payment_date=payment_datetime,
                payment_status="COMPLETED",
                payment_method=rng.choice(
                    ["UPI", "BANK_TRANSFER", "CARD"]
                ),
                created_at=payment_datetime,
            )

            payments.append(payment)
            counts[scenario] += 1

        try:
            db.add_all(payments)
            db.commit()
        except Exception:
            db.rollback()
            raise

        print("\n=== PAYMENT GENERATION SUMMARY ===")
        print(f"Installments processed: {len(installments)}")
        print(f"Payments inserted: {len(payments)}")

        for scenario, count in counts.items():
            print(f"{scenario}: {count}")

        print("Payment generation completed successfully!")


if __name__ == "__main__":
    generate_payments()
