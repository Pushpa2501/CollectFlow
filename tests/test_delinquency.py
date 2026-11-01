
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models import (
    Loan,
    Installment,
    Payment,
    DelinquencySnapshot,
)


AS_OF_DATE = date(2026, 10, 31)
ZERO = Decimal("0.00")


def expected_bucket(dpd):
    if dpd == 0:
        return "CURRENT"
    if dpd <= 30:
        return "DPD_1_30"
    if dpd <= 60:
        return "DPD_31_60"
    if dpd <= 90:
        return "DPD_61_90"
    return "DPD_90_PLUS"


def test_delinquency_reconciliation():
    with SessionLocal() as db:
        loans = db.scalars(select(Loan)).all()

        snapshots = db.scalars(
            select(DelinquencySnapshot).where(
                DelinquencySnapshot.snapshot_date == AS_OF_DATE
            )
        ).all()

        snapshot_map = {
            snapshot.loan_id: snapshot
            for snapshot in snapshots
        }

        assert len(snapshot_map) == len(loans), (
            "Every loan must have a snapshot"
        )

        installments = db.scalars(
            select(Installment)
        ).all()

        payments = db.scalars(
            select(Payment).where(
                Payment.payment_status == "COMPLETED"
            )
        ).all()

        paid_by_installment = {}

        for payment in payments:
            if payment.payment_date.date() > AS_OF_DATE:
                continue

            installment_id = payment.installment_id

            paid_by_installment[installment_id] = (
                paid_by_installment.get(
                    installment_id, ZERO
                )
                + payment.payment_amount
            )

        loan_installments = {}

        for installment in installments:
            loan_installments.setdefault(
                installment.loan_id, []
            ).append(installment)

        for loan in loans:
            overdue = ZERO
            outstanding = ZERO
            oldest_unpaid = None

            for installment in loan_installments.get(
                loan.loan_id, []
            ):
                paid = paid_by_installment.get(
                    installment.installment_id,
                    ZERO
                )

                unpaid = max(
                    installment.due_amount - paid,
                    ZERO
                )

                outstanding += unpaid

                if (
                    installment.due_date < AS_OF_DATE
                    and unpaid > ZERO
                ):
                    overdue += unpaid

                    if (
                        oldest_unpaid is None
                        or installment.due_date < oldest_unpaid
                    ):
                        oldest_unpaid = installment.due_date

            dpd = (
                (AS_OF_DATE - oldest_unpaid).days
                if oldest_unpaid
                else 0
            )

            snapshot = snapshot_map[loan.loan_id]

            assert snapshot.overdue_amount == overdue, (
                f"Overdue mismatch: {loan.loan_id}"
            )

            assert snapshot.outstanding_balance == outstanding, (
                f"Outstanding mismatch: {loan.loan_id}"
            )

            assert snapshot.days_past_due == dpd, (
                f"DPD mismatch: {loan.loan_id}"
            )

            assert snapshot.delinquency_bucket == expected_bucket(
                dpd
            ), (
                f"Bucket mismatch: {loan.loan_id}"
            )

        print(
            f"\nPASS: Validated {len(loans)} loan snapshots"
        )
        print("PASS: Overdue amounts reconciled")
        print("PASS: Outstanding scheduled amounts reconciled")
        print("PASS: Days past due reconciled")
        print("PASS: Delinquency buckets verified")


if __name__ == "__main__":
    test_delinquency_reconciliation()
