
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backend.database.connection import engine


def test_invalid_foreign_key():
    """Verify that SQLite rejects an account with an invalid customer."""

    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            connection.execute(
                text("""
                    INSERT INTO accounts (
                        account_id,
                        customer_id,
                        account_type,
                        account_status,
                        opened_at,
                        created_at
                    )
                    VALUES (
                        :account_id,
                        :customer_id,
                        :account_type,
                        :account_status,
                        :opened_at,
                        :created_at
                    )
                """),
                {
                    "account_id": "INVALID_TEST_001",
                    "customer_id": "NONEXISTENT_CUSTOMER",
                    "account_type": "SAVINGS",
                    "account_status": "ACTIVE",
                    "opened_at": "2026-01-01",
                    "created_at": "2026-01-01"
                }
            )

        except IntegrityError:
            print("PASS: Invalid foreign key correctly rejected")

        else:
            raise AssertionError(
                "FAIL: Database accepted an invalid foreign key"
            )

        finally:
            transaction.rollback()


if __name__ == "__main__":
    test_invalid_foreign_key()
