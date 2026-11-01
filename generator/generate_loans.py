
import random
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models.customer import Customer
from backend.models.account import Account
from backend.models.loan import Loan


RANDOM_SEED = 42

REFERENCE_DATE = date(2026, 10, 31)


def add_months(year, month, months):
    total = year * 12 + (month - 1) + months
    return total // 12, total % 12 + 1


def generate_accounts_and_loans():
    rng = random.Random(RANDOM_SEED)

    with SessionLocal() as db:
        customers = db.scalars(
            select(Customer).order_by(Customer.customer_id)
        ).all()

        if not customers:
            raise RuntimeError(
                "No customers found. Generate customers first."
            )

        existing_accounts = set(
            db.scalars(select(Account.account_id)).all()
        )

        existing_loans = set(
            db.scalars(select(Loan.loan_id)).all()
        )

        accounts = []
        loans = []

        for index, customer in enumerate(customers, start=1):
            account_id = f"ACC{index:06d}"
            loan_id = f"LOAN{index:06d}"

            if (
                account_id in existing_accounts
                or loan_id in existing_loans
            ):
                continue

            account = Account(
                account_id=account_id,
                customer_id=customer.customer_id,
                account_type="LOAN",
                account_status="ACTIVE",
                opened_at=date(2025, 1, 1),
            )

            principal = Decimal(
                rng.randrange(50000, 500001, 1000)
            )

            interest = Decimal(
                str(rng.choice([8.5, 9.5, 10.5, 12.0, 14.0]))
            )

            tenure = rng.choice([12, 18, 24, 36])

            start_date = date(2025, 1, 1)

            year, month = add_months(
                start_date.year,
                start_date.month,
                tenure
            )

            maturity_date = date(year, month, 1)

            loan = Loan(
                loan_id=loan_id,
                account_id=account_id,
                principal_amount=principal,
                annual_interest_rate=interest,
                tenure_months=tenure,
                start_date=start_date,
                maturity_date=maturity_date,
                loan_status="ACTIVE",
            )

            accounts.append(account)
            loans.append(loan)

        try:
            db.add_all(accounts)
            db.flush()

            db.add_all(loans)
            db.commit()

        except Exception:
            db.rollback()
            raise

        print(f"Accounts inserted: {len(accounts)}")
        print(f"Loans inserted: {len(loans)}")
        print("Account and loan generation completed!")


if __name__ == "__main__":
    generate_accounts_and_loans()
