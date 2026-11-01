
from datetime import date
from decimal import Decimal

from sqlalchemy import select, func

from backend.database.connection import SessionLocal
from backend.models.loan import Loan
from backend.models.installment import Installment
from backend.models.payment import Payment
from backend.models.delinquency_snapshot import DelinquencySnapshot


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


def calculate_loan_delinquency(db, loan):
    installments = db.scalars(
        select(Installment)
        .where(Installment.loan_id == loan.loan_id)
        .order_by(Installment.due_date)
    ).all()

    payments = db.scalars(
        select(Payment)
        .where(
            Payment.loan_id == loan.loan_id,
            Payment.payment_status == "COMPLETED",
            func.date(Payment.payment_date) <= AS_OF_DATE.isoformat()
        )
    ).all()

    paid_by_installment = {}

    for payment in payments:
        installment_id = payment.installment_id
        paid_by_installment[installment_id] = (
            paid_by_installment.get(installment_id, ZERO)
            + payment.payment_amount
        )

    overdue_amount = ZERO
    oldest_unpaid_due_date = None
    remaining_scheduled = ZERO

    for installment in installments:
        paid = paid_by_installment.get(
            installment.installment_id,
            ZERO
        )

        unpaid = max(
            installment.due_amount - paid,
            ZERO
        )

        remaining_scheduled += unpaid

        if installment.due_date < AS_OF_DATE and unpaid > ZERO:
            overdue_amount += unpaid

            if (
                oldest_unpaid_due_date is None
                or installment.due_date < oldest_unpaid_due_date
            ):
                oldest_unpaid_due_date = installment.due_date

    dpd = 0

    if oldest_unpaid_due_date is not None:
        dpd = (
            AS_OF_DATE - oldest_unpaid_due_date
        ).days

    return {
        "days_past_due": dpd,
        "overdue_amount": overdue_amount,
        "outstanding_balance": remaining_scheduled,
        "delinquency_bucket": get_bucket(dpd),
    }


def generate_delinquency_snapshots():
    with SessionLocal() as db:
        loans = db.scalars(
            select(Loan).order_by(Loan.loan_id)
        ).all()

        existing_loan_ids = set(
            db.scalars(
                select(DelinquencySnapshot.loan_id)
                .where(
                    DelinquencySnapshot.snapshot_date
                    == AS_OF_DATE
                )
            ).all()
        )

        snapshots = []
        bucket_counts = {}

        for loan in loans:
            if loan.loan_id in existing_loan_ids:
                continue

            result = calculate_loan_delinquency(
                db, loan
            )

            snapshot = DelinquencySnapshot(
                snapshot_id=f"SNAP{loan.loan_id[4:]}20261031",
                loan_id=loan.loan_id,
                snapshot_date=AS_OF_DATE,
                days_past_due=result["days_past_due"],
                overdue_amount=result["overdue_amount"],
                outstanding_balance=result["outstanding_balance"],
                delinquency_bucket=result["delinquency_bucket"],
            )

            snapshots.append(snapshot)

            bucket = result["delinquency_bucket"]
            bucket_counts[bucket] = (
                bucket_counts.get(bucket, 0) + 1
            )

        try:
            db.add_all(snapshots)
            db.commit()
        except Exception:
            db.rollback()
            raise

        print("=== DELINQUENCY GENERATION SUMMARY ===")
        print(f"Loans processed: {len(loans)}")
        print(f"Snapshots inserted: {len(snapshots)}")

        for bucket in [
            "CURRENT",
            "DPD_1_30",
            "DPD_31_60",
            "DPD_61_90",
            "DPD_90_PLUS",
        ]:
            print(
                f"{bucket}: {bucket_counts.get(bucket, 0)}"
            )

        print(
            "Delinquency generation completed successfully!"
        )


if __name__ == "__main__":
    generate_delinquency_snapshots()
