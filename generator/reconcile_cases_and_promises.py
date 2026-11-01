
import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models import (
    CollectionCase,
    DelinquencySnapshot,
    PromiseToPay,
)


AS_OF_DATE = date(2026, 10, 31)

REPORT_PATH = Path(
    "results/validation/case_promise_reconciliation.csv"
)


def priority_from_dpd(dpd):
    if dpd >= 90:
        return 90
    if dpd >= 60:
        return 70
    if dpd >= 30:
        return 50
    return 30


def reconcile():
    changes = []

    with SessionLocal() as db:
        cases = db.scalars(
            select(CollectionCase)
        ).all()

        snapshots = {
            snapshot.loan_id: snapshot
            for snapshot in db.scalars(
                select(DelinquencySnapshot).where(
                    DelinquencySnapshot.snapshot_date == AS_OF_DATE
                )
            ).all()
        }

        promises_by_loan = {}

        for promise in db.scalars(
            select(PromiseToPay)
        ).all():
            promises_by_loan.setdefault(
                promise.loan_id, []
            ).append(promise)

        cases_updated = 0
        promises_updated = 0
        statuses_updated = 0

        for case in cases:
            snapshot = snapshots.get(case.loan_id)

            if snapshot is None:
                raise ValueError(
                    f"Missing snapshot: {case.loan_id}"
                )

            corrected_overdue = snapshot.overdue_amount

            if case.overdue_amount != corrected_overdue:
                changes.append({
                    "entity_type": "CollectionCase",
                    "entity_id": case.case_id,
                    "field": "overdue_amount",
                    "old_value": str(case.overdue_amount),
                    "new_value": str(corrected_overdue),
                    "reason": "OCTOBER_SNAPSHOT_RECONCILIATION",
                })

                case.overdue_amount = corrected_overdue
                cases_updated += 1

            # Update priority only for cases whose
            # priority follows the generator's DPD rule.
            expected_priority = priority_from_dpd(
                snapshot.days_past_due
            )

            if case.priority_score != expected_priority:
                changes.append({
                    "entity_type": "CollectionCase",
                    "entity_id": case.case_id,
                    "field": "priority_score",
                    "old_value": str(case.priority_score),
                    "new_value": str(expected_priority),
                    "reason": "DPD_PRIORITY_RECALCULATION",
                })

                case.priority_score = expected_priority

            for promise in promises_by_loan.get(
                case.loan_id, []
            ):
                if promise.promised_amount > corrected_overdue:
                    old_amount = promise.promised_amount

                    if corrected_overdue <= Decimal("0.00"):
                        # No outstanding arrears remain.
                        # Retain the amount and flag for
                        # manual review rather than creating
                        # an invalid zero-value promise.
                        raise ValueError(
                            f"Promise {promise.promise_id} "
                            "has no remaining arrears. "
                            "Manual resolution required."
                        )

                    changes.append({
                        "entity_type": "PromiseToPay",
                        "entity_id": promise.promise_id,
                        "field": "promised_amount",
                        "old_value": str(old_amount),
                        "new_value": str(corrected_overdue),
                        "reason": "PROMISE_EXCEEDS_CORRECTED_ARREARS",
                    })

                    promise.promised_amount = corrected_overdue
                    promises_updated += 1

                    if (
                        promise.actual_paid_amount
                        > promise.promised_amount
                    ):
                        changes.append({
                            "entity_type": "PromiseToPay",
                            "entity_id": promise.promise_id,
                            "field": "actual_paid_amount",
                            "old_value": str(
                                promise.actual_paid_amount
                            ),
                            "new_value": str(
                                promise.promised_amount
                            ),
                            "reason": "SYNTHETIC_OUTCOME_ADJUSTMENT",
                        })

                        promise.actual_paid_amount = (
                            promise.promised_amount
                        )

        # Generate the audit report before committing.
        REPORT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with REPORT_PATH.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "entity_type",
                    "entity_id",
                    "field",
                    "old_value",
                    "new_value",
                    "reason",
                ],
            )

            writer.writeheader()
            writer.writerows(changes)

        db.commit()

    print("\n=== CASE AND PROMISE RECONCILIATION ===")
    print(f"Collection cases updated: {cases_updated}")
    print(f"Promises adjusted: {promises_updated}")
    print(f"Total field changes logged: {len(changes)}")
    print(f"Audit report: {REPORT_PATH}")
    print("Reconciliation completed!")


if __name__ == "__main__":
    reconcile()
