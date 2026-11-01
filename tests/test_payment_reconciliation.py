
from decimal import Decimal

from sqlalchemy import select, func

from backend.database.connection import SessionLocal
from backend.models import Payment, Installment


def test_payment_reconciliation():
    with SessionLocal() as db:
        records = db.execute(
            select(Payment, Installment)
            .join(
                Installment,
                Payment.installment_id
                == Installment.installment_id
            )
        ).all()

        payment_count = db.scalar(
            select(func.count()).select_from(Payment)
        )

        assert len(records) == payment_count, (
            "Some payments have missing installment references"
        )

        mismatched_loans = []
        allocation_totals = {}

        for payment, installment in records:
            if payment.loan_id != installment.loan_id:
                mismatched_loans.append(payment.payment_id)

            if payment.payment_status == "COMPLETED":
                allocation_totals.setdefault(
                    installment.installment_id,
                    Decimal("0.00")
                )

                allocation_totals[
                    installment.installment_id
                ] += payment.payment_amount

        assert not mismatched_loans, (
            f"Payments allocated to incorrect loans: "
            f"{mismatched_loans[:10]}"
        )

        overpayments = []

        for payment, installment in records:
            allocated = allocation_totals.get(
                installment.installment_id,
                Decimal("0.00")
            )

            if allocated > installment.due_amount:
                overpayments.append(
                    installment.installment_id
                )

        assert not overpayments, (
            f"Overpaid installments detected: "
            f"{sorted(set(overpayments))[:10]}"
        )

        print(
            f"\nPASS: Reconciled {payment_count} payments"
        )
        print("PASS: All payment-to-loan mappings valid")
        print("PASS: No installment overpayments")


if __name__ == "__main__":
    test_payment_reconciliation()
