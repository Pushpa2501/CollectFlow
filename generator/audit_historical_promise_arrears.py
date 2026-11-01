
from collections import defaultdict
from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models import (
    Installment,
    Payment,
    PromiseToPay,
    DelinquencySnapshot,
)


ZERO = Decimal("0.00")


def audit():
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
            select(PromiseToPay)
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

        zero_historical_arrears = []
        exceeds_historical_arrears = []
        valid_at_promise_date = []

        for promise in promises:
            promise_date = promise.promise_date

            overdue = ZERO

            for installment in installments_by_loan.get(
                promise.loan_id, []
            ):
                if installment.due_date >= promise_date:
                    continue

                paid = ZERO

                for payment in payments_by_installment.get(
                    installment.installment_id, []
                ):
                    if payment.payment_date.date() <= promise_date:
                        paid += payment.payment_amount

                overdue += max(
                    installment.due_amount - paid,
                    ZERO,
                )

            if overdue <= ZERO:
                zero_historical_arrears.append(
                    (promise.promise_id, promise.loan_id)
                )
            elif promise.promised_amount > overdue:
                exceeds_historical_arrears.append(
                    (
                        promise.promise_id,
                        promise.loan_id,
                        str(promise.promised_amount),
                        str(overdue),
                    )
                )
            else:
                valid_at_promise_date.append(
                    promise.promise_id
                )

        print("\n=== HISTORICAL PROMISE ARREARS AUDIT ===")
        print(f"Total promises: {len(promises)}")
        print(
            "Valid against arrears on promise date:",
            len(valid_at_promise_date),
        )
        print(
            "Promises with zero historical arrears:",
            len(zero_historical_arrears),
        )
        print(
            "Promises exceeding historical arrears:",
            len(exceeds_historical_arrears),
        )

        print("\nSample zero-arrears promises:")
        for item in zero_historical_arrears[:10]:
            print(item)

        print("\nSample excessive promises:")
        for item in exceeds_historical_arrears[:10]:
            print(item)


if __name__ == "__main__":
    audit()
