
import random
from datetime import datetime, timezone

from backend.database.connection import SessionLocal
from backend.models.customer import Customer


RANDOM_SEED = 42

FIRST_NAMES = [
    "Aarav", "Diya", "Arjun", "Ananya",
    "Rohan", "Meera", "Vikram", "Priya",
    "Kiran", "Sneha", "Rahul", "Kavya"
]

LAST_NAMES = [
    "Sharma", "Reddy", "Kumar", "Patel",
    "Rao", "Singh", "Nair", "Gupta"
]

REGIONS = [
    "Andhra Pradesh",
    "Telangana",
    "Karnataka",
    "Tamil Nadu",
    "Maharashtra"
]

REFERENCE_DATE = datetime(
    2026, 10, 31, 0, 0, 0, tzinfo=timezone.utc
)


def generate_customers(count=100):
    """Generate deterministic synthetic customer records."""

    rng = random.Random(RANDOM_SEED)

    customers = []

    for index in range(1, count + 1):

        customer_id = f"CUST{index:06d}"

        first_name = rng.choice(FIRST_NAMES)
        last_name = rng.choice(LAST_NAMES)

        age = rng.randint(21, 70)
        region = rng.choice(REGIONS)

        customer = Customer(
            customer_id=customer_id,
            full_name=f"{first_name} {last_name}",
            age=age,
            region=region,
            customer_status="ACTIVE",
            created_at=REFERENCE_DATE
        )

        customers.append(customer)

    return customers


def save_customers(customers):
    """Insert generated customers into the database."""

    db = SessionLocal()

    try:
        db.add_all(customers)
        db.commit()

        print(
            f"Successfully inserted {len(customers)} customers."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":

    print("=== COLLECTFLOW SYNTHETIC DATA GENERATOR ===")

    customers = generate_customers(count=100)

    save_customers(customers)

    print("Customer generation completed successfully!")
