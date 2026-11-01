
import csv
from pathlib import Path


OUTPUT_PATH = Path(
    "data/ground_truth/exception_ground_truth.csv"
)

FIELDS = [
    "scenario_id",
    "loan_status",
    "case_status",
    "contact_hour",
    "allowed_start_hour",
    "allowed_end_hour",
    "payment_loan_id",
    "installment_loan_id",
    "promised_amount",
    "overdue_amount",
    "dispute_flag",
    "debt_confirmed",
    "expected_exception",
]


def baseline(scenario_id):
    return {
        "scenario_id": scenario_id,
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
        "expected_exception": "NONE",
    }


def create_ground_truth():
    rows = []

    # 10 clean scenarios
    for i in range(1, 11):
        rows.append(baseline(f"CLEAN{i:03d}"))

    scenarios = [
        (
            "PAID_OFF_IN_COLLECTIONS",
            {"loan_status": "PAID_OFF", "case_status": "OPEN"},
        ),
        (
            "OUT_OF_HOURS_CONTACT",
            {"contact_hour": 22},
        ),
        (
            "WRONG_PAYMENT_ALLOCATION",
            {"installment_loan_id": "LOAN002"},
        ),
        (
            "PROMISE_EXCEEDS_ARREARS",
            {"promised_amount": "1500.00"},
        ),
        (
            "DISPUTED_DEBT_CONFIRMED",
            {"dispute_flag": True},
        ),
    ]

    # 5 examples for each exception type
    for exception_code, changes in scenarios:
        for i in range(1, 6):
            row = baseline(
                f"{exception_code}_{i:03d}"
            )
            row.update(changes)
            row["expected_exception"] = exception_code
            rows.append(row)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_PATH.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS
        )
        writer.writeheader()
        writer.writerows(rows)

    print("=== GROUND-TRUTH DATASET ===")
    print(f"Records created: {len(rows)}")
    print(f"Clean records: 10")
    print(f"Exception records: 25")
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    create_ground_truth()
