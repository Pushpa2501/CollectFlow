
# CollectFlow

Synthetic Loan Collections, Financial Validation and Compliance Exception Detection Platform

## Overview

CollectFlow is a Python-based prototype for generating and validating synthetic loan collection data.

It models customers, accounts, loans, installments, payments, delinquency snapshots, collection cases, contact preferences, contact attempts, and promises to pay.

The project also includes rule-based exception detection, synthetic ground-truth scenarios, financial reconciliation audits, and automated tests.

## Technology Stack

- Python 3.11
- SQLAlchemy
- SQLite
- Pandas and NumPy
- Pytest
- FastAPI and Streamlit dependencies

## Dataset Summary

The current validated local dataset contains:

| Entity | Records |
|---|---:|
| Customers | 10,000 |
| Accounts | 10,000 |
| Loans | 10,000 |
| Installments | 225,876 |
| Payments | 153,408 |
| Delinquency snapshots | 120,000 |
| Collection cases | 9,948 |
| Contact preferences | 10,000 |
| Contact attempts | 29,844 |
| Promises to pay | 7,058 |

The dataset is synthetic and uses a simulation cutoff of October 31, 2026.

## Dataset Generation

The project contains separate generation modules under `generator/`.

The verified dependency order begins with:

1. Database initialization
2. Customer generation
3. Account and loan generation
4. Installment generation
5. Payment generation
6. Historical delinquency snapshots
7. Collection cases
8. Contact preferences
9. Contact attempts
10. Promises to pay

The current dataset was built incrementally, with scaling and reconciliation steps.

**Reproducibility limitation:** Although generators use seeded randomization, a complete fresh-database run has not yet been independently verified to reproduce the exact current dataset. Some generators advance random state differently when existing records are skipped.

Do not assume that rerunning all generators against an existing database is safe or fully idempotent.

## Compliance Validation

Contact compliance checks evaluate:

- Do-not-contact restrictions
- Permitted communication channels
- Allowed contact hours
- Time-zone-aware contact timestamps

The synthetic contact generator deliberately includes violations for testing. It labels noncompliant attempts rather than preventing their creation.

The current dataset contains 15,335 compliant attempts and 14,509 violations, including 11,911 attempts flagged for outside-allowed-hours contact.

These rules are simplified simulation rules, not a comprehensive implementation of applicable debt collection laws.

## Exception Detection

The rule-based exception detector covers five negative scenarios:

1. Paid-off loan incorrectly included in collections
2. Contact outside permitted hours
3. Incorrect payment allocation
4. Promise amount exceeding arrears
5. Disputed debt treated as confirmed

Ground-truth examples are stored under `data/ground_truth/`.

The evaluation includes 35 handcrafted synthetic examples: 10 clean and 25 negative.

Reported precision, recall, and F1 are 100% on this small handcrafted evaluation set. These results must not be interpreted as production accuracy or generalization to real-world financial data.

The disputed-debt scenario uses a simplified review-state proxy rather than a dedicated `debt_confirmed` database field.

## Historical Promise Validation

The historical promise audit examined 7,058 promises:

- 7,002 valid against historical arrears
- 6 associated with zero historical arrears
- 50 exceeding historical arrears

The 56 flagged records are retained for transparency rather than silently altered.

The report is available at:

`results/validation/historical_promise_validation.csv`

Promise outcomes are simulated and are not independently reconciled against actual payment transactions.

The historical promise report test verifies expected classifications and completeness; it does not independently recalculate every historical balance.

## Testing

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run automated tests from the project root:

```powershell
python -m pytest -q
```

Latest recorded result:

```text
25 passed in 8.58s
```

This result applies to the existing local test environment and dataset.

## Evaluation Artifacts

- `data/ground_truth/exception_ground_truth.csv`
- `results/evaluation/exception_evaluation.json`
- `results/validation/collection_case_reconciliation.csv`
- `results/validation/historical_promise_validation.csv`

The SQLite database is excluded from version control. These artifacts document the existing evaluated dataset; they do not replace a complete fresh-generation verification.

## Limitations

- The complete pipeline has not yet been verified on a clean database.
- Incremental generation can change random outcomes.
- Some historical promises fail financial validation.
- Promise fulfillment is simulated rather than transaction-reconciled.
- Contact compliance rules are simplified.
- Evaluation metrics come from a small handcrafted synthetic dataset.
- This is a prototype, not a production collections platform.

## AI Assistance

AI assistance was used during implementation, debugging, test development, and documentation. Generated suggestions were reviewed and tested using local Python commands and Pytest.

Development decisions and verification activities are documented in `prompts/ai_prompt_history.md`.
