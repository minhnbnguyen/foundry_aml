# Data dictionary — synthetic AML dataset

All data is fictional and randomly generated (seed 42). No real people or real
financial records. Five tables model the slice of the operational world the
workflow needs. Column choices are deliberate — each exists because either a
monitoring rule keys off it or the AIP reasoning needs it.

## Volumes
| Table | Rows | Notes |
|---|---|---|
| customers | 50 | 40 normal + 5 false-positive generators + 5 ring/structuring subjects |
| accounts | 51 | one retiree holds two (checking + savings) |
| transactions | 1,243 | edge-style: each row is one movement of money |
| alerts | 90 | 81 false positives, 9 true positives → 90.0% FP rate |
| counterparties | 5 | external endpoints where bank visibility ends |

## customers.csv
| Column | Meaning | Why it's here |
|---|---|---|
| customer_id | PK (C####) | links to accounts, alerts |
| full_name | fictional name | subject identity |
| customer_type | Individual / Business | mules are individuals; cash-intensive FPs are businesses |
| date_onboarded | account-relationship start | **recent onboarding is a mule tell** |
| kyc_risk_rating | Low / Medium / High | baseline risk the analyst starts from |
| occupation | stated job | context for "does the activity fit the profile" |
| pep_flag | Y/N politically exposed | escalates scrutiny |
| home_branch | branch | branch-hopping is a structuring tell |
| annual_declared_income | KYC income | **throughput >> income is the core layering signal** |

## accounts.csv
| Column | Meaning |
|---|---|
| account_id | PK (A####) |
| customer_id | FK → customers |
| account_type | Personal Checking / Savings / Business Checking |
| date_opened | account age |
| current_balance | snapshot balance |

## transactions.csv  (edge model: one row = one money movement)
| Column | Meaning |
|---|---|
| transaction_id | PK |
| txn_date | date of movement |
| from_account_id | source account (blank if cash-in / external inbound) |
| to_account_id | destination account (blank if cash-out / external outbound) |
| external_party | named external source/destination or "CASH DEPOSIT" etc. |
| external_country | jurisdiction of the external party (blank if domestic/internal) |
| amount | USD |
| channel | CASH / WIRE / ACH / CARD / INTERNAL |
| description | free-text memo |

Why edge-style rather than a per-account ledger: with `from_account_id →
to_account_id`, an internal transfer is a single traversable link between two
`Account` objects. That is what lets the ontology follow the money A → B → C
through the ring. Cash-in has no `from`; cash-out and external wires have no `to`.

## alerts.csv
| Column | Meaning |
|---|---|
| alert_id | PK (AL####) |
| date_generated | when the monitoring system fired it |
| account_id / customer_id | what it fired on |
| rule_code | STRUCT-CASH / RAPID-MOVE / HIGH-RISK-WIRE / VELOCITY |
| rule_description | human-readable rule text |
| system_score | 0–100 rules-engine score (note: high score ≠ true positive) |
| status | starts "New"; your Actions move it to Cleared / Escalated |

Design note: `system_score` deliberately does **not** cleanly separate true from
false positives (a legit diner scores 71; a real structuring case scores 88 but
so do some noise alerts). If score alone worked, you wouldn't need the workflow.
That gap is the whole reason the AIP triage assistant earns its place.

## counterparties.csv
| Column | Meaning |
|---|---|
| counterparty_id | PK |
| name | external entity |
| cp_type | Shell / Trade / Investment / Business |
| country | jurisdiction |
| risk_flag | Low / High |

Only external endpoints live here. Mules are **customers**, not counterparties —
that is what keeps the ring inside your graph and traversable.
