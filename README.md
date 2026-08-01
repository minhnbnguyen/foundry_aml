# AML Investigation & SAR Automation Workflow

An operational workflow built in **Palantir Foundry / AIP** that helps anti-money-laundering
(AML) analysts triage alert noise and draft regulatory filings — while keeping the human
analyst as the accountable decision-maker.

> **Demo video:** [add your unlisted YouTube link]
>
> **Note on this repo:** most of the build lives inside Foundry (ontology, AIP Logic
> functions, write-back Actions, a Workshop app) and is not "clone-and-run." This repo is a
> documented showcase: the synthetic dataset and its generator, the AIP prompts, the data
> model, and the design rationale. Screenshots and the demo video show the working app.

---

## The problem

Banks are legally required to file a **Suspicious Activity Report (SAR)** when they detect
potential money laundering. But transaction-monitoring systems generate large volumes of
alerts, and **roughly 85–95% are false positives** — legitimate activity that trips a static
rule. Analysts spend most of their time clearing noise, and every genuine case requires
hand-writing a SAR narrative against a **30-day filing deadline**.

Two costs define the problem: the analyst time wasted on false positives, and the regulatory
risk of a missed or late filing.

## Who it's for

The **AML investigator** — the analyst who works the alert queue, decides what to escalate,
investigates cases, and writes the filings.

## What I built

A two-page workflow that closes the operational loop:

1. **Triage** — an AI assistant reads each alert's customer profile and transactions and
   recommends *clear* or *escalate*, with cited reasoning.
2. **Cluster** — escalated alerts are grouped into a single `Case`; the ontology reveals when
   separate alerts are actually one laundering ring.
3. **Draft** — an AI function drafts the SAR narrative in FinCEN format from the case data.
4. **File** — the analyst reviews, edits, and files; the decision writes back to the ontology
   with an audit trail.

## Architecture

```
Synthetic CSVs → Foundry datasets → Ontology (objects + links)
                                          │
                    ┌─────────────────────┼─────────────────────┐
              AIP Logic: assessAlert            AIP Logic: draftSarNarrative
              (triage recommendation)           (FinCEN SAR narrative)
                    │                                     │
              Write-back Actions ──────────────► Workshop app (2 pages)
              (Triage Alert, Open Case, File SAR)   analyst clicks through the loop
```

**Ontology (the core):** the domain is modeled as objects and links, split into the
*operational world* (`Customer`, `Account`, `Transaction`, `Counterparty`) and the
*investigation workflow* (`Alert`, `Case`, `SAR`), bridged by the `Alert`. The links matter:
because money laundering is a network problem, modeling `Transaction` as an edge between
accounts lets the graph traverse a laundering chain and surface a ring.

See [`docs/data_dictionary.md`](docs/data_dictionary.md) for the full object/field model.

## Design decisions (the "why")

- **Synthetic data only.** No real financial or personal data. The generator plants a
  realistic laundering ring and a structuring case inside ~90% false-positive noise.
- **Human-in-the-loop by design.** The AI does everything *around* the decision — gathers
  evidence, spots the pattern, drafts the filing — but never makes it. A SAR is a legal
  filing and "suspicious" is a judgment call, so the analyst stays accountable. Every AI step
  in the app is followed by a human commit button.
- **Anti-hallucination guardrails.** The SAR drafter inserts `[ANALYST TO CONFIRM: ...]` for
  anything not in the data and self-reports completeness gaps, rather than inventing facts.
- **Mules modeled as customers, not counterparties.** Real laundering rings often run through
  accounts at the same bank, so modeling the mules as `Customer` objects keeps the ring
  *traversable* in the graph. `Counterparty` is reserved for the external endpoints where the
  bank's visibility ends — a nod to the real single-institution visibility limit that
  information-sharing regimes (e.g. FinCEN 314(b)) exist to address.

## The scenario in the data

- **90 alerts, 90% false positives** — matching the industry benchmark.
- **Structuring case:** one subject, 11 branch-hopping cash deposits just under $10k.
- **Layering ring:** a $320k wire from a high-risk jurisdiction → fanned across four
  recently-onboarded mule accounts → funneled out to one common offshore shell within days.

Ground truth and demo narration notes: [`docs/scenario_key.md`](docs/scenario_key.md).

## Repo contents

```
aml-sar-workflow/
├── README.md
├── data/
│   ├── generate_aml_data.py     # reproducible generator (seed 42)
│   ├── customers.csv            # 50 customers
│   ├── accounts.csv             # 51 accounts
│   ├── transactions.csv         # 1,243 transactions (edge model)
│   ├── alerts.csv               # 90 alerts (81 false positive, 9 true)
│   └── counterparties.csv       # 5 external endpoints
├── prompts/
│   ├── 1_alert_triage_assessAlert.md
│   └── 2_sar_drafter_draftSarNarrative.md
├── docs/
│   ├── data_dictionary.md
│   └── scenario_key.md
└── screenshots/                 # ontology graph, triage output, ring cluster, SAR draft
```

## Regenerate the data

```bash
python3 data/generate_aml_data.py
```

Deterministic (seed 42), so alert IDs and the planted ring stay stable across runs.

## Tech

Palantir Foundry, AIP (AIP Logic, Ontology, Actions, Workshop), Python (synthetic data),
FinCEN SAR narrative conventions.
