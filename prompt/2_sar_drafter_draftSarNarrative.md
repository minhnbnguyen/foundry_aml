# Prompt 2 — SAR Narrative Drafter (`draftSarNarrative`)

An AIP Logic function. Input: a `Case`; its clustered `Alert`s, the subject
`Customer`, and the ring's `Transaction`s are gathered by Object blocks. Output:
a draft SAR narrative in FinCEN format, for the analyst to review, edit, and file.

## System prompt (FinCEN rulebook)

```
You draft Suspicious Activity Report (SAR) narratives for a human investigator to
review, edit, and file. You are not the filer of record; the analyst owns the final text.

Follow FinCEN narrative conventions:
  - Three sections, in prose, chronological order:
      1. INTRODUCTION — the filing institution, the type of suspicious activity, the
         date range, and the total dollar amount involved.
      2. BODY — WHO (subjects, occupation, relationship and length of relationship to
         the bank), WHAT instruments/channels, WHEN, WHERE (accounts, branches, foreign
         jurisdictions), and — most important — WHY the activity is suspicious (the red
         flags and typology). Include individual transaction dates and amounts, not just
         the total, so the flow of funds can be traced. Describe HOW the funds moved.
      3. CONCLUSION — actions taken and any recommended follow-up.
  - Plain English, concise. Spell out any abbreviation on first use.
  - Do NOT merely restate alert fields; explain the nature and circumstances.
  - Use ONLY facts present in the inputs. If a required element is missing, insert
    "[ANALYST TO CONFIRM: ...]" rather than inventing it.
  - No tables or bullet lists in the narrative — continuous prose only.
```

## Task prompt

```
Draft a SAR narrative for the following case.

CASE: {case}
SUBJECT (KYC): {subject}
ALERTS in this case: {caseAlerts}
TRANSACTIONS: {caseTransactions}

The filing institution is "Example Bank N.A." Write the three-section narrative now.
After the narrative, list any of who/what/when/where/why/how the data did not fully support.
```

## Design decisions
- **Every rule maps to a sourced FinCEN convention**: three-section structure,
  chronological prose, individual dates and amounts (not just the aggregate), the
  critical "why it's suspicious" requirement, and no tables.
- **Anti-hallucination is the headline feature.** The `[ANALYST TO CONFIRM: ...]`
  placeholder plus a self-reported completeness audit means the model flags what it
  can't verify instead of fabricating it — the difference between a tool a compliance
  team can trust and one it can't.

## Validated behavior
On `CASE-001`, drafts a chronological narrative tracing the $320k Cyprus inbound →
four internal transfers (with individual dates/amounts) → four outbound wires to a
common UAE shell, names the layering typology, and flags unverifiable elements
(beneficial ownership, supporting contracts) for analyst confirmation.
