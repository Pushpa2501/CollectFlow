# CollectFlow ? Data Dictionary

## Overview

This document describes the SQLite database schema used by CollectFlow.
It is generated from the SQLAlchemy-managed database schema.
All data is synthetic.

## Schema Conventions

- Primary keys uniquely identify records within their tables.
- Foreign keys reference related parent records.
- Required means the database column is NOT NULL.
- Optional means the database column permits NULL.
- NUMERIC(14, 2) monetary values use two decimal places; currency is not enforced by the schema.
- DATE stores calendar dates; DATETIME stores date and time values.
- VARCHAR(n) indicates the declared string length.
- Allowed status values and business lifecycle rules are implemented or assessed separately; they are not inferred from column types.

## accounts

| Field | SQL type | Required | Key / Reference |
|---|---|---|---|
| `account_id` | `VARCHAR(30)` | Yes | PK |
| `customer_id` | `VARCHAR(30)` | Yes | FK ? customers.customer_id |
| `account_type` | `VARCHAR(30)` | Yes |  |
| `account_status` | `VARCHAR(20)` | Yes |  |
| `opened_at` | `DATETIME` | Yes |  |
| `created_at` | `DATETIME` | Yes |  |

## collection_cases

| Field | SQL type | Required | Key / Reference |
|---|---|---|---|
| `case_id` | `VARCHAR(30)` | Yes | PK |
| `loan_id` | `VARCHAR(30)` | Yes | FK ? loans.loan_id |
| `customer_id` | `VARCHAR(30)` | Yes | FK ? customers.customer_id |
| `opened_date` | `DATE` | Yes |  |
| `closed_date` | `DATE` | No |  |
| `case_status` | `VARCHAR(20)` | Yes |  |
| `priority_score` | `INTEGER` | Yes |  |
| `overdue_amount` | `NUMERIC(14, 2)` | Yes |  |
| `assigned_agent` | `VARCHAR(80)` | No |  |
| `dispute_flag` | `BOOLEAN` | Yes |  |
| `hardship_flag` | `BOOLEAN` | Yes |  |
| `created_at` | `DATETIME` | Yes |  |

## contact_attempts

| Field | SQL type | Required | Key / Reference |
|---|---|---|---|
| `attempt_id` | `VARCHAR(30)` | Yes | PK |
| `loan_id` | `VARCHAR(30)` | Yes | FK ? loans.loan_id |
| `customer_id` | `VARCHAR(30)` | Yes | FK ? customers.customer_id |
| `contact_datetime` | `DATETIME` | Yes |  |
| `channel` | `VARCHAR(20)` | Yes |  |
| `attempt_status` | `VARCHAR(20)` | Yes |  |
| `outcome` | `VARCHAR(30)` | Yes |  |
| `compliance_status` | `VARCHAR(20)` | Yes |  |
| `violation_reason` | `TEXT` | No |  |
| `created_at` | `DATETIME` | Yes |  |

## contact_preferences

| Field | SQL type | Required | Key / Reference |
|---|---|---|---|
| `preference_id` | `VARCHAR(30)` | Yes | PK |
| `customer_id` | `VARCHAR(30)` | Yes | FK ? customers.customer_id |
| `allow_calls` | `BOOLEAN` | Yes |  |
| `allow_sms` | `BOOLEAN` | Yes |  |
| `allow_email` | `BOOLEAN` | Yes |  |
| `preferred_channel` | `VARCHAR(20)` | Yes |  |
| `allowed_start_hour` | `INTEGER` | Yes |  |
| `allowed_end_hour` | `INTEGER` | Yes |  |
| `timezone_name` | `VARCHAR(64)` | Yes |  |
| `do_not_contact` | `BOOLEAN` | Yes |  |
| `updated_at` | `DATETIME` | Yes |  |

## customers

| Field | SQL type | Required | Key / Reference |
|---|---|---|---|
| `customer_id` | `VARCHAR(30)` | Yes | PK |
| `full_name` | `VARCHAR(120)` | Yes |  |
| `age` | `INTEGER` | Yes |  |
| `region` | `VARCHAR(60)` | Yes |  |
| `customer_status` | `VARCHAR(20)` | Yes |  |
| `created_at` | `DATETIME` | Yes |  |

## delinquency_snapshots

| Field | SQL type | Required | Key / Reference |
|---|---|---|---|
| `snapshot_id` | `VARCHAR(30)` | Yes | PK |
| `loan_id` | `VARCHAR(30)` | Yes | FK ? loans.loan_id |
| `snapshot_date` | `DATE` | Yes |  |
| `days_past_due` | `INTEGER` | Yes |  |
| `overdue_amount` | `NUMERIC(14, 2)` | Yes |  |
| `outstanding_balance` | `NUMERIC(14, 2)` | Yes |  |
| `delinquency_bucket` | `VARCHAR(20)` | Yes |  |

## installments

| Field | SQL type | Required | Key / Reference |
|---|---|---|---|
| `installment_id` | `VARCHAR(30)` | Yes | PK |
| `loan_id` | `VARCHAR(30)` | Yes | FK ? loans.loan_id |
| `installment_number` | `INTEGER` | Yes |  |
| `due_date` | `DATE` | Yes |  |
| `due_amount` | `NUMERIC(14, 2)` | Yes |  |
| `installment_status` | `VARCHAR(20)` | Yes |  |

## loans

| Field | SQL type | Required | Key / Reference |
|---|---|---|---|
| `loan_id` | `VARCHAR(30)` | Yes | PK |
| `account_id` | `VARCHAR(30)` | Yes | FK ? accounts.account_id |
| `principal_amount` | `NUMERIC(14, 2)` | Yes |  |
| `annual_interest_rate` | `NUMERIC(6, 3)` | Yes |  |
| `tenure_months` | `INTEGER` | Yes |  |
| `start_date` | `DATE` | Yes |  |
| `maturity_date` | `DATE` | Yes |  |
| `loan_status` | `VARCHAR(20)` | Yes |  |
| `created_at` | `DATETIME` | Yes |  |

## payments

| Field | SQL type | Required | Key / Reference |
|---|---|---|---|
| `payment_id` | `VARCHAR(30)` | Yes | PK |
| `loan_id` | `VARCHAR(30)` | Yes | FK ? loans.loan_id |
| `installment_id` | `VARCHAR(30)` | Yes | FK ? installments.installment_id |
| `payment_amount` | `NUMERIC(14, 2)` | Yes |  |
| `payment_date` | `DATETIME` | Yes |  |
| `payment_status` | `VARCHAR(20)` | Yes |  |
| `payment_method` | `VARCHAR(30)` | Yes |  |
| `created_at` | `DATETIME` | Yes |  |

## promises_to_pay

| Field | SQL type | Required | Key / Reference |
|---|---|---|---|
| `promise_id` | `VARCHAR(30)` | Yes | PK |
| `loan_id` | `VARCHAR(30)` | Yes | FK ? loans.loan_id |
| `customer_id` | `VARCHAR(30)` | Yes | FK ? customers.customer_id |
| `promise_date` | `DATE` | Yes |  |
| `promised_payment_date` | `DATE` | Yes |  |
| `promised_amount` | `NUMERIC(14, 2)` | Yes |  |
| `promise_status` | `VARCHAR(20)` | Yes |  |
| `actual_paid_amount` | `NUMERIC(14, 2)` | Yes |  |
| `created_at` | `DATETIME` | Yes |  |

## Validation and Business Rules

The schema enforces primary-key, foreign-key, and NOT NULL constraints.
Other requirements, such as nonnegative monetary amounts, valid date ordering,
permitted contact hours, status transitions, and financial reconciliation,
require application-level validation or additional database constraints.
The existence of a column does not establish that all such rules are enforced.

## Data Provenance

Records are synthetically generated by modules in `generator/`.
The main dataset was assembled incrementally.
Customer generation has been independently reproduced in two isolated
databases using seed 42 and identical SHA-256 record checksums.
Complete end-to-end dataset reproducibility remains unverified.
