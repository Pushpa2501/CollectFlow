
from decimal import Decimal


def detect_exceptions(record):
    """
    Detect loan collection data-quality and compliance exceptions.

    Input:
        Dictionary containing loan, payment, contact,
        promise, and dispute-related fields.

    Output:
        List of detected exception codes.
    """

    exceptions = []

    loan_status = record.get("loan_status")
    case_status = record.get("case_status")

    if (
        loan_status == "PAID_OFF"
        and case_status in {"OPEN", "IN_PROGRESS"}
    ):
        exceptions.append("PAID_OFF_IN_COLLECTIONS")

    contact_hour = record.get("contact_hour")
    start_hour = record.get("allowed_start_hour")
    end_hour = record.get("allowed_end_hour")

    if all(
        value is not None
        for value in [contact_hour, start_hour, end_hour]
    ):
        if not (start_hour <= contact_hour < end_hour):
            exceptions.append("OUT_OF_HOURS_CONTACT")

    payment_loan_id = record.get("payment_loan_id")
    installment_loan_id = record.get(
        "installment_loan_id"
    )

    if (
        payment_loan_id is not None
        and installment_loan_id is not None
        and payment_loan_id != installment_loan_id
    ):
        exceptions.append("WRONG_PAYMENT_ALLOCATION")

    promised_amount = record.get("promised_amount")
    overdue_amount = record.get("overdue_amount")

    if (
        promised_amount is not None
        and overdue_amount is not None
    ):
        if (
            Decimal(str(promised_amount))
            > Decimal(str(overdue_amount))
        ):
            exceptions.append("PROMISE_EXCEEDS_ARREARS")

    dispute_flag = record.get("dispute_flag", False)
    debt_confirmed = record.get(
        "debt_confirmed", False
    )

    if dispute_flag and debt_confirmed:
        exceptions.append("DISPUTED_DEBT_CONFIRMED")

    return exceptions
