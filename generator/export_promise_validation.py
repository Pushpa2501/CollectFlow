
import csv
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models import Installment, Payment, PromiseToPay


ZERO = Decimal("0.00")

OUTPUT_PATH = Path(
    "results/validation/historical_promise_validation.csv"
)


def export_validation():
    with SessionLocal() as db:
        installments = db.scalars(
            select(Installment)
        ).all()

        payments = db.scalars(
            select(Payment).where(
                Payment.payment_status == "COMPLETED"
            )
        ).all()

        promises = db.scalars(
            select(PromiseToPay).order_by(
                PromiseToPay.promise_id
            )
        ).all()

        installments_by_loan = defaultdict(list)
        payments_by_installment = defaultdict(list)

        for installment in installments:
            installments_by_loan[
                installment.loan_id
            ].append(installment)

        for payment in payments:
            payments_by_installment[
                payment.installment_id
            ].append(payment)

        rows = []
        counts = {
            "VALID": 0,
            "ZERO_HISTORICAL_ARREARS": 0,
            "EXCEEDS_HISTORICAL_ARREARS": 0,
        }

        for promise in promises:
            historical_arrears = ZERO

            for installment in installments_by_loan.get(
                promise.loan_id, []
            ):
                if installment.due_date >= promise.promise_date:
                    continue

                paid = ZERO

                for payment in payments_by_installment.get(
                    installment.installment_id, []
                ):
                    if (
                        payment.payment_date.date()
                        <= promise.promise_date
                    ):
                        paid += payment.payment_amount

                historical_arrears += max(
                    installment.due_amount - paid,
                    ZERO,
                )

            if historical_arrears <= ZERO:
                result = "ZERO_HISTORICAL_ARREARS"
            elif promise.promised_amount > historical_arrears:
                result = "EXCEEDS_HISTORICAL_ARREARS"
            else:
                result = "VALID"

            counts[result] += 1

            rows.append({
                "promise_id": promise.promise_id,
                "loan_id": promise.loan_id,
                "promise_date": str(promise.promise_date),
                "promised_amount": str(
                    promise.promised_amount
                ),
                "historical_arrears": str(
                    historical_arrears
                ),
                "promise_status": promise.promise_status,
                "validation_result": result,
            })

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "promise_id",
                "loan_id",
                "promise_date",
                "promised_amount",
                "historical_arrears",
                "promise_status",
                "validation_result",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    print("\n=== HISTORICAL PROMISE VALIDATION ===")
    print(f"Total promises: {len(rows)}")

    for result, count in counts.items():
        print(f"{result}: {count}")

    print(f"Report saved: {OUTPUT_PATH}")
    print("Validation report generated successfully!")


if __name__ == "__main__":
    export_validation()
