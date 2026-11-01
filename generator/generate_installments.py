
import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select, func

from backend.database.connection import SessionLocal
from backend.models.loan import Loan
from backend.models.installment import Installment


CENT = Decimal("0.01")


def round_money(amount):
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def add_months(start_date, months):
    total = start_date.year * 12 + start_date.month - 1 + months

    year = total // 12
    month = total % 12 + 1

    day = min(
        start_date.day,
        calendar.monthrange(year, month)[1]
    )

    return date(year, month, day)


def calculate_schedule(loan):
    principal = loan.principal_amount
    monthly_rate = (
        loan.annual_interest_rate / Decimal("1200")
    )
    tenure = loan.tenure_months

    if monthly_rate == 0:
        emi = round_money(principal / tenure)
    else:
        factor = (Decimal("1") + monthly_rate) ** tenure
        emi = round_money(
            principal * monthly_rate * factor / (factor - 1)
        )

    balance = principal
    schedule = []

    for number in range(1, tenure + 1):
        interest = round_money(balance * monthly_rate)

        if number == tenure:
            payment = round_money(balance + interest)
            principal_paid = balance
        else:
            payment = emi
            principal_paid = payment - interest

            if principal_paid <= 0:
                raise ValueError(
                    f"Invalid amortization for {loan.loan_id}"
                )

            if principal_paid > balance:
                principal_paid = balance
                payment = round_money(principal_paid + interest)

        balance = round_money(balance - principal_paid)

        schedule.append(
            Installment(
                installment_id=f"INST{loan.loan_id[4:]}{number:03d}",
                loan_id=loan.loan_id,
                installment_number=number,
                due_date=add_months(loan.start_date, number),
                due_amount=payment,
                installment_status="PENDING",
            )
        )

    if balance != Decimal("0.00"):
        raise ValueError(
            f"Loan {loan.loan_id} did not fully amortize"
        )

    return schedule


def generate_installments():
    with SessionLocal() as db:
        loans = db.scalars(
            select(Loan).order_by(Loan.loan_id)
        ).all()

        inserted = 0
        skipped = 0

        try:
            for loan in loans:
                existing_count = db.scalar(
                    select(func.count())
                    .select_from(Installment)
                    .where(Installment.loan_id == loan.loan_id)
                )

                if existing_count > 0:
                    if existing_count != loan.tenure_months:
                        raise ValueError(
                            f"Incomplete schedule for {loan.loan_id}: "
                            f"{existing_count}/{loan.tenure_months}"
                        )

                    skipped += 1
                    continue

                schedule = calculate_schedule(loan)
                db.add_all(schedule)
                inserted += len(schedule)

            db.commit()

        except Exception:
            db.rollback()
            raise

        print("=== INSTALLMENT GENERATION SUMMARY ===")
        print(f"Loans processed: {len(loans)}")
        print(f"Installments inserted: {inserted}")
        print(f"Existing loan schedules skipped: {skipped}")
        print("Installment generation completed successfully!")


if __name__ == "__main__":
    generate_installments()
