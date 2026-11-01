
import pytest

from backend.services.exception_detector import (
    detect_exceptions,
)


TEST_CASES = [
    (
        {
            "loan_status": "PAID_OFF",
            "case_status": "OPEN",
        },
        "PAID_OFF_IN_COLLECTIONS",
    ),
    (
        {
            "contact_hour": 22,
            "allowed_start_hour": 9,
            "allowed_end_hour": 18,
        },
        "OUT_OF_HOURS_CONTACT",
    ),
    (
        {
            "payment_loan_id": "LOAN001",
            "installment_loan_id": "LOAN002",
        },
        "WRONG_PAYMENT_ALLOCATION",
    ),
    (
        {
            "promised_amount": "1500.00",
            "overdue_amount": "1000.00",
        },
        "PROMISE_EXCEEDS_ARREARS",
    ),
    (
        {
            "dispute_flag": True,
            "debt_confirmed": True,
        },
        "DISPUTED_DEBT_CONFIRMED",
    ),
]


@pytest.mark.parametrize(
    "record, expected_exception",
    TEST_CASES,
)
def test_exception_detection(record, expected_exception):
    detected = detect_exceptions(record)

    assert expected_exception in detected


def test_clean_record():
    record = {
        "loan_status": "ACTIVE",
        "case_status": "CLOSED",
        "contact_hour": 11,
        "allowed_start_hour": 9,
        "allowed_end_hour": 18,
        "payment_loan_id": "LOAN001",
        "installment_loan_id": "LOAN001",
        "promised_amount": "500.00",
        "overdue_amount": "1000.00",
        "dispute_flag": False,
        "debt_confirmed": True,
    }

    assert detect_exceptions(record) == []
