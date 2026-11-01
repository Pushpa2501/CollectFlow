
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from backend.database.connection import Base
import backend.models

from backend.models import (
    Customer,
    Account,
    Loan,
    Installment,
    Payment,
    CollectionCase,
    ContactPreference,
    ContactAttempt,
    PromiseToPay,
)

from backend.services.exception_detector import (
    detect_exceptions,
)
from backend.services.database_exception_scanner import (
    local_contact_hour,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


def create_base_records(db):
    customer = Customer(
        customer_id="TESTCUST001",
        full_name="Test Customer",
        age=30,
        region="Andhra Pradesh",
        customer_status="ACTIVE",
    )

    account = Account(
        account_id="TESTACC001",
        customer_id="TESTCUST001",
        account_type="LOAN",
        account_status="ACTIVE",
        opened_at=date(2025, 1, 1),
    )

    loan = Loan(
        loan_id="TESTLOAN001",
        account_id="TESTACC001",
        principal_amount=Decimal("10000.00"),
        annual_interest_rate=Decimal("10.000"),
        tenure_months=12,
        start_date=date(2025, 1, 1),
        maturity_date=date(2026, 1, 1),
        loan_status="ACTIVE",
    )

    case = CollectionCase(
        case_id="TESTCASE001",
        loan_id="TESTLOAN001",
        customer_id="TESTCUST001",
        opened_date=date(2025, 6, 1),
        case_status="OPEN",
        priority_score=50,
        overdue_amount=Decimal("1000.00"),
        dispute_flag=False,
        hardship_flag=False,
    )

    db.add(customer)
    db.flush()

    db.add(account)
    db.flush()

    db.add(loan)
    db.flush()

    db.add(case)
    db.flush()

    return customer, account, loan, case


def test_paid_off_loan_in_collections(db):
    _, _, loan, case = create_base_records(db)

    loan.loan_status = "PAID_OFF"
    db.flush()

    record = {
        "loan_status": loan.loan_status,
        "case_status": case.case_status,
    }

    assert (
        "PAID_OFF_IN_COLLECTIONS"
        in detect_exceptions(record)
    )


def test_out_of_hours_contact(db):
    customer, _, loan, _ = create_base_records(db)

    preference = ContactPreference(
        preference_id="TESTPREF001",
        customer_id=customer.customer_id,
        allowed_start_hour=9,
        allowed_end_hour=18,
        timezone_name="Asia/Kolkata",
    )

    attempt = ContactAttempt(
        attempt_id="TESTATT001",
        loan_id=loan.loan_id,
        customer_id=customer.customer_id,
        contact_datetime=datetime(
            2026, 10, 31, 17, 0, tzinfo=timezone.utc
        ),
        channel="CALL",
        attempt_status="COMPLETED",
        outcome="NO_ANSWER",
        compliance_status="VIOLATION",
        violation_reason="OUTSIDE_ALLOWED_HOURS",
    )

    db.add_all([preference, attempt])
    db.flush()

    hour = local_contact_hour(
        attempt.contact_datetime,
        preference.timezone_name,
    )

    record = {
        "contact_hour": hour,
        "allowed_start_hour": preference.allowed_start_hour,
        "allowed_end_hour": preference.allowed_end_hour,
    }

    assert (
        "OUT_OF_HOURS_CONTACT"
        in detect_exceptions(record)
    )


def test_wrong_payment_allocation(db):
    _, _, loan, _ = create_base_records(db)

    second_customer = Customer(
        customer_id="TESTCUST002",
        full_name="Second Customer",
        age=35,
        region="Andhra Pradesh",
        customer_status="ACTIVE",
    )

    second_account = Account(
        account_id="TESTACC002",
        customer_id="TESTCUST002",
        account_type="LOAN",
        account_status="ACTIVE",
        opened_at=date(2025, 1, 1),
    )

    second_loan = Loan(
        loan_id="TESTLOAN002",
        account_id="TESTACC002",
        principal_amount=Decimal("20000.00"),
        annual_interest_rate=Decimal("10.000"),
        tenure_months=12,
        start_date=date(2025, 1, 1),
        maturity_date=date(2026, 1, 1),
    )

    db.add(second_customer)
    db.flush()
    db.add(second_account)
    db.flush()
    db.add(second_loan)
    db.flush()

    installment = Installment(
        installment_id="TESTINST002",
        loan_id=second_loan.loan_id,
        installment_number=1,
        due_date=date(2025, 2, 1),
        due_amount=Decimal("2000.00"),
    )

    db.add(installment)
    db.flush()

    payment = Payment(
        payment_id="TESTPAY001",
        loan_id=loan.loan_id,
        installment_id=installment.installment_id,
        payment_amount=Decimal("500.00"),
        payment_date=datetime(
            2025, 2, 2, tzinfo=timezone.utc
        ),
        payment_method="UPI",
    )

    db.add(payment)
    db.flush()

    record = {
        "payment_loan_id": payment.loan_id,
        "installment_loan_id": installment.loan_id,
    }

    assert (
        "WRONG_PAYMENT_ALLOCATION"
        in detect_exceptions(record)
    )


def test_promise_exceeds_arrears(db):
    customer, _, loan, case = create_base_records(db)

    promise = PromiseToPay(
        promise_id="TESTPROM001",
        loan_id=loan.loan_id,
        customer_id=customer.customer_id,
        promise_date=date(2026, 10, 1),
        promised_payment_date=date(2026, 10, 10),
        promised_amount=Decimal("1500.00"),
        promise_status="ACTIVE",
        actual_paid_amount=Decimal("0.00"),
    )

    db.add(promise)
    db.flush()

    record = {
        "promised_amount": promise.promised_amount,
        "overdue_amount": case.overdue_amount,
    }

    assert (
        "PROMISE_EXCEEDS_ARREARS"
        in detect_exceptions(record)
    )


def test_disputed_debt_confirmed(db):
    _, _, loan, case = create_base_records(db)

    case.dispute_flag = True
    db.flush()

    # Explicit workflow state supplied separately,
    # because CollectionCase has no debt_confirmed column.
    workflow_debt_confirmed = True

    record = {
        "dispute_flag": case.dispute_flag,
        "debt_confirmed": workflow_debt_confirmed,
    }

    assert (
        "DISPUTED_DEBT_CONFIRMED"
        in detect_exceptions(record)
    )


def test_clean_database_record(db):
    _, _, loan, case = create_base_records(db)

    record = {
        "loan_status": loan.loan_status,
        "case_status": case.case_status,
        "contact_hour": 11,
        "allowed_start_hour": 9,
        "allowed_end_hour": 18,
        "payment_loan_id": loan.loan_id,
        "installment_loan_id": loan.loan_id,
        "promised_amount": Decimal("500.00"),
        "overdue_amount": case.overdue_amount,
        "dispute_flag": False,
        "debt_confirmed": False,
    }

    assert detect_exceptions(record) == []
