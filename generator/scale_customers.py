
from sqlalchemy import select, func

from backend.database.connection import SessionLocal
from backend.models.customer import Customer
from generator.generate_data import generate_customers


TARGET_CUSTOMERS = 10000


def scale_customers():
    with SessionLocal() as db:
        existing_ids = set(
            db.scalars(select(Customer.customer_id)).all()
        )

        all_customers = generate_customers(
            count=TARGET_CUSTOMERS
        )

        new_customers = [
            customer
            for customer in all_customers
            if customer.customer_id not in existing_ids
        ]

        try:
            # Insert in batches to limit memory usage.
            batch_size = 1000

            for start in range(0, len(new_customers), batch_size):
                batch = new_customers[
                    start:start + batch_size
                ]

                db.add_all(batch)
                db.commit()

        except Exception:
            db.rollback()
            raise

        total = db.scalar(
            select(func.count()).select_from(Customer)
        )

        print("=== CUSTOMER SCALING SUMMARY ===")
        print(f"New customers inserted: {len(new_customers)}")
        print(f"Total customers: {total}")

        if total != TARGET_CUSTOMERS:
            raise RuntimeError(
                f"Expected {TARGET_CUSTOMERS}, found {total}"
            )

        print("Customer scaling completed successfully!")


if __name__ == "__main__":
    scale_customers()
