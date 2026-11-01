
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest


@dataclass
class Scenario:
    scenario_id: str
    loan_status: str = "DELINQUENT"
    case_status: str = "OPEN"
    contact_hour: int = 11
    allowed_start_hour: int = 9
    allowed_end_hour: int = 18
    payment_loan_id: str = "LOAN001"
    installment_loan_id: str = "LOAN001"
    promised_amount: Decimal = Decimal("500.00")
    overdue_amount: Decimal = Decimal("1000.00")
    dispute_flag: bool = False
    debt_confirmed: bool = True


def detect_violations(scenario):
    violations = []

    if (
        scenario.loan_status == "PAID_OFF"
        and scenario.case_status in {"OPEN", "IN_PROGRESS"}
    ):
        violations.append("PAID_OFF_IN_COLLECTIONS")

    if not (
        scenario.allowed_start_hour
        <= scenario.contact_hour
        < scenario.allowed_end_hour
    ):
        violations.append("OUT_OF_HOURS_CONTACT")

    if (
        scenario.payment_loan_id
        != scenario.installment_loan_id
    ):
        violations.append("WRONG_PAYMENT_ALLOCATION")

    if scenario.promised_amount > scenario.overdue_amount:
        violations.append("PROMISE_EXCEEDS_ARREARS")

    if scenario.dispute_flag and scenario.debt_confirmed:
        violations.append("DISPUTED_DEBT_CONFIRMED")

    return violations


SCENARIOS = [
    (
        Scenario(
            scenario_id="NEG001",
            loan_status="PAID_OFF",
        ),
        "PAID_OFF_IN_COLLECTIONS",
    ),
    (
        Scenario(
            scenario_id="NEG002",
            contact_hour=22,
        ),
        "OUT_OF_HOURS_CONTACT",
    ),
    (
        Scenario(
            scenario_id="NEG003",
            payment_loan_id="LOAN001",
            installment_loan_id="LOAN002",
        ),
        "WRONG_PAYMENT_ALLOCATION",
    ),
    (
        Scenario(
            scenario_id="NEG004",
            promised_amount=Decimal("1500.00"),
        ),
        "PROMISE_EXCEEDS_ARREARS",
    ),
    (
        Scenario(
            scenario_id="NEG005",
            dispute_flag=True,
        ),
        "DISPUTED_DEBT_CONFIRMED",
    ),
]


@pytest.mark.parametrize(
    "scenario, expected_violation",
    SCENARIOS,
    ids=[scenario.scenario_id for scenario, _ in SCENARIOS],
)
def test_negative_scenario_detection(
    scenario,
    expected_violation,
):
    detected = detect_violations(scenario)

    assert expected_violation in detected, (
        f"{scenario.scenario_id}: "
        f"Expected {expected_violation}, got {detected}"
    )

    print(
        f"\nPASS: {scenario.scenario_id} -> "
        f"{expected_violation}"
    )


def test_clean_scenario():
    clean = Scenario(scenario_id="CLEAN001")

    assert detect_violations(clean) == []

    print("\nPASS: CLEAN001 -> No violations")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
