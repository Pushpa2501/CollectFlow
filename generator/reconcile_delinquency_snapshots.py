
from collections import defaultdict
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


def get_bucket(dpd):
    if dpd == 0:
        return "CURRENT"
    if dpd <= 30:
        return "DPD_1_30"
    if dpd <= 60:
        return "DPD_31_60"
    if dpd <= 90:
        return "DPD_61_90"
    return "DPD_90_PLUS"


def reconcile_snapshots():
    with SessionLocal() as db:
        loans = db.scalars(
            select(Loan).order_by(Loan.loan_id)
        ).all()

        installments = db.scalars(
            select(Installment)
        ).all()

        payments = db.scalars(
            select(Payment).where(
                Payment.payment_status == "COMPLETED"
            )
        ).all()

        snapshots = db.scalars(
            select(DelinquencySnapshot).where(
                DelinquencySnapshot.snapshot_date == AS_OF_DATE
            )
        ).all()

        snapshot_map = {
            snapshot.loan_id: snapshot
            for snapshot in snapshots
        }

        installments_by_loan = defaultdict(list)
        paid_by_installment = defaultdict(lambda: ZERO)

        for installment in installments:
            installments_by_loan[
                installment.loan_id
            ].append(installment)

        for payment in payments:
            if payment.payment_date.date() <= AS_OF_DATE:
                paid_by_installment[
                    payment.installment_id
                ] += payment.payment_amount

        updated = 0
        unchanged = 0
        missing = 0

        for loan in loans:
            snapshot = snapshot_map.get(loan.loan_id)

            if snapshot is None:
                missing += 1
                continue

            overdue = ZERO
            outstanding = ZERO
            oldest_unpaid = None

            for installment in installments_by_loan.get(
                loan.loan_id, []
            ):
                paid = paid_by_installment.get(
                    installment.installment_id,
                    ZERO,
                )

                unpaid = max(
                    installment.due_amount - paid,
                    ZERO,
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
                if oldest_unpaid is not None
                else 0
            )

            bucket = get_bucket(dpd)

            changed = (
                snapshot.overdue_amount != overdue
                or snapshot.outstanding_balance != outstanding
                or snapshot.days_past_due != dpd
                or snapshot.delinquency_bucket != bucket
            )

            if changed:
                snapshot.overdue_amount = overdue
                snapshot.outstanding_balance = outstanding
                snapshot.days_past_due = dpd
                snapshot.delinquency_bucket = bucket
                updated += 1
            else:
                unchanged += 1

        if missing:
            raise ValueError(
                f"{missing} loans have no October snapshot. "
                "No changes were committed."
            )

        db.commit()

    print("\n=== DELINQUENCY RECONCILIATION ===")
    print(f"Loans checked: {len(loans)}")
    print(f"Snapshots updated: {updated}")
    print(f"Snapshots unchanged: {unchanged}")
    print(f"Missing snapshots: {missing}")
    print("Reconciliation completed successfully!")


if __name__ == "__main__":
    reconcile_snapshots()
