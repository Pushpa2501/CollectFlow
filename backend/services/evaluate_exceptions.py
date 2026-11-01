
import csv
import json
from pathlib import Path

from backend.services.exception_detector import (
    detect_exceptions,
)


INPUT_PATH = Path(
    "data/ground_truth/exception_ground_truth.csv"
)

OUTPUT_PATH = Path(
    "results/evaluation/exception_evaluation.json"
)


def evaluate():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "Ground-truth dataset not found. "
            "Run python -m generator.create_ground_truth first."
        )

    with INPUT_PATH.open(
        newline="",
        encoding="utf-8"
    ) as file:
        rows = list(csv.DictReader(file))

    tp = fp = fn = tn = 0
    correct = 0
    details = []

    for row in rows:
        expected = row["expected_exception"]

        record = dict(row)

        record["dispute_flag"] = (
            row["dispute_flag"].lower() == "true"
        )
        record["debt_confirmed"] = (
            row["debt_confirmed"].lower() == "true"
        )

        for field in [
            "contact_hour",
            "allowed_start_hour",
            "allowed_end_hour",
        ]:
            record[field] = int(row[field])

        detected = detect_exceptions(record)

        predicted = (
            detected[0] if detected else "NONE"
        )

        if predicted == expected:
            correct += 1

        expected_positive = expected != "NONE"
        predicted_positive = predicted != "NONE"

        if expected_positive and predicted_positive:
            tp += 1
        elif not expected_positive and predicted_positive:
            fp += 1
        elif expected_positive and not predicted_positive:
            fn += 1
        else:
            tn += 1

        details.append({
            "scenario_id": row["scenario_id"],
            "expected": expected,
            "predicted": predicted,
            "correct": predicted == expected,
        })

    total = len(rows)

    accuracy = correct / total if total else 0
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0
    )

    results = {
        "total_records": total,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "confusion_matrix": {
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "TN": tn,
        },
        "details": details,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_PATH.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8"
    )

    print("=== EXCEPTION DETECTION EVALUATION ===")
    print(f"Records: {total}")
    print(f"Accuracy: {accuracy:.2%}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
    print(f"F1 Score: {f1:.2%}")
    print(f"TP={tp}, FP={fp}, FN={fn}, TN={tn}")
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    evaluate()
