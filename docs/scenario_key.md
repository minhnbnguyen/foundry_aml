# Scenario answer-key

This is the ground truth behind the data. The uploaded CSVs contain **no**
"is_fraud" column on purpose — a real monitoring system doesn't know the answer,
and neither should your app until the analyst (with AIP's help) works it out.
Keep this doc to narrate the demo and to check that your AIP logic reaches the
right conclusions.

## The alert queue at a glance
- 90 alerts total. **81 are false positives, 9 are true positives (90.0% FP).**
- Your triage step should clear the 81 and surface the 9.

## True positive #1 — Structuring (single subject)  → your rock-solid spine
- Subject: **Marcus Reilly (C9001 / account A9001)**, rideshare driver, declared income $41k.
- Pattern: **11 cash deposits** of $8,200–$9,750 over ~18 days, alternating between
  the Chicago-Loop and Naperville branches (branch-hopping to stay under the radar).
- Total structured: ~$100k against a $41k declared income.
- Alerts: **AL0082, AL0083, AL0084** (STRUCT-CASH, score 88).
- Why it's real: every deposit sits just under the $10k CTR threshold; the pattern
  is deliberate, repeated, cross-branch, and far exceeds the customer's profile.
- Demo line: *"One subject, eleven deposits, all under ten grand, hopping branches —
  the classic structuring signature the CTR threshold was designed to catch."*

## True positive #2 — Layering ring  → your swing-for-the-fences moment
Money flow (all dates June 2026):
```
Meridian Offshore Ltd (Cyprus)
        │  $320,000 WIRE in  (Jun 2)
        ▼
Northgate Consulting LLC  (C9100 / A9100)   ← the source
        │  4 INTERNAL transfers, ~$78k each  (Jun 3–4)
        ├────────────► Katie Brennan  (C9101 / A9101)
        ├────────────► Samuel Osei    (C9102 / A9102)
        ├────────────► Lucas Grant    (C9103 / A9103)
        └────────────► Nadia Farah    (C9104 / A9104)
                             │  each WIRES out ~$75k  (Jun 5–7)
                             ▼
        Apex Trade Services FZE (UAE)  ← common cash-out node
```
- Alerts: **AL0085–AL0090** (6 alerts across 5 accounts: 1 HIGH-RISK-WIRE +
  1 RAPID-MOVE on the source, 1 RAPID-MOVE on each of the 4 mules).
- The tells your AIP should cite:
  1. **Rapid pass-through** — money in and back out within 3–5 days.
  2. **Throughput vs income** — mules declared $29–38k but moved ~$78k in days.
  3. **Recent onboarding** — all four mules opened accounts 2026-04-15, ~7 weeks prior.
  4. **Common counterparty** — all four funnel to the *same* UAE shell.
  5. **High-risk jurisdictions** on both ends (Cyprus in, UAE out).
- The graph payoff: no single alert looks like a ring. Clustering AL0085–AL0090
  by shared counterparty + time proximity reveals it.
- Demo line: *"Six alerts sat in four different analyst queues. The ontology
  clustered them into one case and surfaced a five-account ring funneling
  $300k offshore — a connection no dashboard would have made."*

## The false positives (so you can defend the triage reasoning)
These are the realistic near-misses your AIP should CLEAR, with reasons:
| Alert(s) | Customer | Looks like | Why it's cleared |
|---|---|---|---|
| STRUCT-CASH | Sunrise Diner LLC (C0041) | structuring (daily sub-$10k cash) | licensed cash-intensive business; deposits match receipts |
| STRUCT-CASH | C0005 | structuring ($9,600 cash) | one-off documented used-car sale |
| VELOCITY | Midwest Property Mgmt (C0042) | layering (many transfers out) | property manager returning tenant deposits |
| RAPID-MOVE | Betty Coleman (C0043) | pass-through | retiree moving her OWN savings→checking (same owner) |
| HIGH-RISK-WIRE | Grace Whitfield (C0044) | suspicious inbound | documented brokerage liquidation, legit source |
| ~76 scattered | various normals | assorted | low scores, activity consistent with profile |

Each false positive has a plausible innocent explanation in the linked data —
that's what makes the triage step a genuine reasoning task, not a lookup.

## Suggested demo arc (≈4 min)
1. **Problem (30s)** — 90 alerts, 90% noise, 30-day filing clock, hand-written SARs.
2. **Triage (60s)** — AIP scores the queue, clears the diner + car-sale FPs with
   reasons, flags the real ones. Show the 90% collapse.
3. **The SAR (45s)** — one click drafts the who/what/when/where/why/how-much
   narrative; you edit a line; File SAR writes back + stamps the audit trail.
4. **Close (30s)** — analyst stayed the decision-maker; AIP removed the 90% that
   wasn't judgment. Impact: faster clears, no missed rings, no missed deadlines.
