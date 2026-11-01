
import calendar
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


ZERO = Decimal("0.00")


def month_end_dates():
    dates = []

    for year, month in [
        (2025, 11), (2025, 12),
        (2026, 1), (2026, 2),
        (2026, 3), (2026, 4),
        (2026, 5), (2026, 6),
        (2026, 7), (2026, 8),
        (2026, 9), (2026, 10),
    ]:
        last_day = calendar.monthrange(year, month)[1]
        dates.append(date(year, month, last_day))

    return dates


def bucket_for_dpd(dpd):
    if dpd == 0:
        return "CURRENT"
    if dpd <= 30:
        return "DPD_1_30"
    if dpd <= 60:
        return "DPD_31_60"
    if dpd <= 90:
        return "DPD_61_90"
    return "DPD_90_PLUS"


def generate_historical_snapshots():
    with SessionLocal() as db:
        loans = db.scalars(
            select(Loan).order_by(Loan.loan_id)
        ).all()

        installments = db.scalars(
            select(Installment)
            .order_by(Installment.loan_id, Installment.due_date)
        ).all()

        payments = db.scalars(
            select(Payment)
            .where(Payment.payment_status == "COMPLETED")
            .order_by(Payment.payment_date)
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

        snapshot_dates = month_end_dates()

        existing_keys = set(
            db.execute(
                select(
                    DelinquencySnapshot.loan_id,
                    DelinquencySnapshot.snapshot_date
                )
            ).all()
        )

        inserted = 0

        for snapshot_date in snapshot_dates:
            batch = []

            for loan in loans:
                key = (loan.loan_id, snapshot_date)

                if key in existing_keys:
                    continue

                overdue = ZERO
                outstanding = ZERO
                oldest_unpaid = None

                for installment in installments_by_loan[
                    loan.loan_id
                ]:
                    paid = ZERO

                    for payment in payments_by_installment.get(
                        installment.installment_id, []
                    ):
                        if (
                            payment.payment_date.date()
                            <= snapshot_date
                        ):
                            paid += payment.payment_amount

                    unpaid = max(
                        installment.due_amount - paid,
                        ZERO
                    )

                    outstanding += unpaid

                    if (
                        installment.due_date < snapshot_date
                        and unpaid > ZERO
                    ):
                        overdue += unpaid

                        if (
                            oldest_unpaid is None
                            or installment.due_date < oldest_unpaid
                        ):
                            oldest_unpaid = installment.due_date

                dpd = (
                    (snapshot_date - oldest_unpaid).days
                    if oldest_unpaid
                    else 0
                )

                snapshot = DelinquencySnapshot(
                    snapshot_id=(
                        f"HIST{loan.loan_id[4:]}"
                        f"{snapshot_date:%Y%m%d}"
                    ),
                    loan_id=loan.loan_id,
                    snapshot_date=snapshot_date,
                    days_past_due=dpd,
                    overdue_amount=overdue,
                    outstanding_balance=outstanding,
                    delinquency_bucket=bucket_for_dpd(dpd),
                )

                batch.append(snapshot)

            if batch:
                db.add_all(batch)
                db.commit()
                inserted += len(batch)

            print(
                f"{snapshot_date}: "
                f"{len(batch)} snapshots inserted"
            )

        print("\n=== HISTORICAL SNAPSHOT SUMMARY ===")
        print(f"Loans: {len(loans)}")
        print(f"Months: {len(snapshot_dates)}")
        print(f"New snapshots inserted: {inserted}")
        print("Historical generation completed!")


if __name__ == "__main__":
    generate_historical_snapshots()
