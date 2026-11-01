
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models import (
    PromiseToPay,
    CollectionCase,
    Loan,
    Account,
)


AS_OF_DATE = date(2026, 10, 31)
ZERO = Decimal("0.00")


def test_promise_structural_integrity():
    with SessionLocal() as db:
        promises = db.scalars(
            select(PromiseToPay)
        ).all()

        cases = {
            case.loan_id: case
            for case in db.scalars(
                select(CollectionCase)
            ).all()
        }

        loan_customers = {
            loan.loan_id: account.customer_id
            for loan, account in db.execute(
                select(Loan, Account).join(
                    Account,
                    Loan.account_id == Account.account_id
                )
            ).all()
        }

        assert promises, "No promises found"

        promise_ids = set()

        for promise in promises:
            # 1. Check unique promise IDs
            assert promise.promise_id not in promise_ids, (
                f"Duplicate promise ID: {promise.promise_id}"
            )
            promise_ids.add(promise.promise_id)

            # 2. Check collection case reference
            case = cases.get(promise.loan_id)

            assert case is not None, (
                f"Missing collection case: {promise.promise_id}"
            )

            # 3. Check customer matches collection case
            assert promise.customer_id == case.customer_id, (
                f"Customer mismatch: {promise.promise_id}"
            )

            # 4. Check loan ownership
            assert promise.customer_id == loan_customers.get(
                promise.loan_id
            ), (
                f"Loan ownership mismatch: {promise.promise_id}"
            )

            # 5. Check promised amount is positive
            assert promise.promised_amount > ZERO, (
                f"Invalid promised amount: {promise.promise_id}"
            )

            # Historical financial validity is evaluated
            # separately against arrears on the promise date.
            # Do not compare this historical promise with
            # the October 31 collection-case overdue amount.

            # 6. Check promise date sequence
            assert (
                promise.promised_payment_date
                >= promise.promise_date
            ), (
                f"Invalid date sequence: {promise.promise_id}"
            )

            # 7. Check actual paid amount range
            assert (
                ZERO
                <= promise.actual_paid_amount
                <= promise.promised_amount
            ), (
                f"Invalid paid amount: {promise.promise_id}"
            )

            # 8. Check allowed statuses
            assert promise.promise_status in {
                "ACTIVE",
                "FULFILLED",
                "BROKEN",
            }, (
                f"Invalid promise status: {promise.promise_id}"
            )

            # 9. Fulfilled promises must be fully paid
            if promise.promise_status == "FULFILLED":
                assert (
                    promise.actual_paid_amount
                    == promise.promised_amount
                ), (
                    f"Fulfilled amount mismatch: "
                    f"{promise.promise_id}"
                )

            # 10. Active promises must not be expired
            if promise.promise_status == "ACTIVE":
                assert (
                    promise.promised_payment_date > AS_OF_DATE
                ), (
                    f"Expired active promise: "
                    f"{promise.promise_id}"
                )

            # 11. Broken promises must not be fully paid
            if promise.promise_status == "BROKEN":
                assert (
                    promise.actual_paid_amount
                    < promise.promised_amount
                ), (
                    f"Broken promise fully paid: "
                    f"{promise.promise_id}"
                )

        print(
            f"\nPASS: Validated {len(promises)} promises"
        )
        print("PASS: Unique promise IDs")
        print("PASS: Loan and customer references")
        print("PASS: Positive promised amounts")
        print("PASS: Promise date sequences")
        print("PASS: Actual paid amount constraints")
        print("PASS: Promise status consistency")
        print(
            "NOTE: Historical arrears validation "
            "is reported separately"
        )
