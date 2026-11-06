# Phase 0 — Discovery and scope lock package

**Status:** Decision package complete; Gate 0 is decision-complete and awaiting external
signatures. No production code, farmer data, model training or advisory publishing has
started.
**Owner:** Product lead, with the agronomist and programme lead.
**Started:** 2026-11-06 · **Gate 0 calendar target:** 2026-11-20 (proposed).
**Canonical live status:** [`../progress-tracker.md`](../progress-tracker.md).
**Working decision record:** [`../phase-0-decisions.md`](../phase-0-decisions.md).

> **Honesty boundary.** This package records decisions, designs, templates and planning
> assumptions. It does not claim that any partner has signed, that any dataset is cleared,
> that any farmer data has been collected, or that any model has a measured performance
> number. External names, signatures and measured baselines remain `TBD` until a human
> records the evidence.

---

## 1. What is in this package

| Deliverable | File | State |
|---|---|---|
| Phase 0 index and Gate 0 status | `README.md` | Complete |
| D1a — first validated crop/target allowlist | [`d1a-allowlist-decision.md`](d1a-allowlist-decision.md) | Recorded; agronomist sign-off pending |
| D3b — verifier capacity, triage and SLA | [`d3b-verifier-capacity-sla.md`](d3b-verifier-capacity-sla.md) | Recorded; partner staffing confirmation pending |
| D4 — owning/paying institution policy | [`d4-owning-institution.md`](d4-owning-institution.md) | Policy decided; named counterparty (D4a) pending |
| D5 — primary outcome metric | [`d5-primary-metric.md`](d5-primary-metric.md) | Pre-registered |
| D7–D12 — phase-gated interim rules | [`../phase-0-decisions.md`](../phase-0-decisions.md) §7 | Rules recorded; numeric values at their gates |
| Partner and data-permission register | [`partner-and-data-permission-register.md`](partner-and-data-permission-register.md) | Draft; zero agreements executed |
| Crop calendar and epidemic window | [`crop-calendar.md`](crop-calendar.md) | Documented; agronomist sign-off pending |
| Target reference sheet | [`target-reference-sheet.md`](target-reference-sheet.md) | Documented; agronomist sign-off pending |
| Pilot area map and site register | [`pilot-area-map.md`](pilot-area-map.md), [`pilot-sites.csv`](pilot-sites.csv) | Candidate sites only; no boundary geometry cleared |
| Pilot protocol v1 | [`pilot-protocol-v1.md`](pilot-protocol-v1.md) | Pre-registered draft |
| Pre-registration manifest | [`preregistration.json`](preregistration.json) | Generated from the frozen document hashes |
| DPIA/ethics scope | [`ethics-and-consent-scope.md`](ethics-and-consent-scope.md) | Draft; not approved |
| Consent wording v1 | [`consent-wording-v1.md`](consent-wording-v1.md) | English draft + Kannada draft; certified translation pending |
| Data acquisition plan | [`data-acquisition-plan.md`](data-acquisition-plan.md) | Planning baseline |
| Budget and staffing scenarios | [`budget-and-staffing-scenarios.md`](budget-and-staffing-scenarios.md) | Planning estimates; no committed figures |
| Risk owner and review-date review | [`risk-register-review.md`](risk-register-review.md) | Applied to tracker §6 |

---

## 2. Decisions at a glance

| ID | Decision | State | Blocks |
|---|---|---|---|
| D1 | Open crop catalogue + validated-target allowlist (ADR-011) | Decided 2026-11-06 | — |
| D1a | Tomato, Eastern Dry Zone, 4 targets + healthy + abiotic + unknown | Recorded 2026-11-06 | Gate 3 |
| D2 | Nowcast over the last 10 days | Decided 2026-11-06 | — |
| D3 | Extension-worker-first verification; `can_confirm` for confirmation | Decided 2026-11-06 | — |
| D3b | Two `can_confirm` holders per area; 24 h triage / 48 h confirmation SLA | Recorded 2026-11-06 | Gate 0 staffing |
| D4 | Public extension/plant-health owner; grant-funded pilot → institutional operations | Policy decided 2026-11-06; named counterparty D4a pending | Gate 0 signature |
| D5 | Median lead time from first report to verified expert confirmation | Pre-registered 2026-11-06 | Gate 5 |
| D6 | Non-chemical, expert-approved, versioned advisory with expiry | Decided 2026-11-06 | — |
| D7 | First verified case event; sentinel absence negatives; `unverified` never eligible | Interim rule 2026-11-06 | Gate 4 |
| D8 | Calibrated abstention + measured floors before opening the frozen test set | Interim rule 2026-11-06 | Gate 3 |
| D9 | Coverage formula + suppression; numeric thresholds after Phase 1 data profile | Interim rule 2026-11-06 | Gate 4 |
| D10 | Per-entity retention/deletion matrix; interim periods | Interim rule 2026-11-06 | Gate 2 |
| D11 | Separate reporter/subject identity; 7-day offline cap | Decided 2026-11-06 | Gate 2 |
| D12 | Deterministic, advisory-only client pre-check; server gate authoritative | Decided 2026-11-06 | Gate 2 |
| D13 | English + Kannada with persisted choice | Decided 2026-11-06 | — |
| D14 | Qualitative confidence band + abstention; severity is expert-set | Decided 2026-11-06 | — |
| D15 | In-app mandatory; email for staff; SMS optional; others deferred | Decided 2026-11-06 | — |

**Gate 0 closure still needs:** a named counterparty and signed/drafted MoU under D4a, the
partner verification route confirmed in writing under D3b, and human sign-off on the
crop/target and crop-calendar documents. Those are external acts, not repository edits.

---

## 3. What Phase 0 deliberately did not do

- No production code, database schema, model training or advisory publication.
- No real farmer data, images or locations.
- No invented partner names, signatures, dataset sizes, model metrics or baselines.
- No commitment to an alert threshold that depends on D8/D9 measurement.
- No claim that the allowlist is commercially or agronomically validated; it is a
  defensible **proposal** for the pilot, subject to expert sign-off.

---

## 4. How to validate this package

The package has a deterministic documentation contract. It checks required files, decision
fields, cross-document consistency, link resolution, the pre-registration hash, the absence
of executed agreements without evidence, and the absence of chemical advice in alert
templates.

```bash
# From the repository root
python scripts/validate_phase0.py

# Or run the unittest suite directly
python -m unittest discover -s tests/phase0 -v
```

The validator uses only the Python standard library. It does not require the backend
dependencies, a database or network access.

---

## 5. Next actions after this package

1. Hold the decision workshop and obtain the signatures listed in
   [`partner-and-data-permission-register.md`](partner-and-data-permission-register.md)
   §5.
2. Record the named counterparty (D4a) and the named `can_confirm` holders (D3b).
3. Replace the candidate site codes in [`pilot-sites.csv`](pilot-sites.csv) with confirmed
   hobli names and boundary version.
4. Re-run `python scripts/validate_phase0.py` after any change to D1a, D5 or the pilot
   protocol, and update [`preregistration.json`](preregistration.json) only through a
   recorded amendment.
5. Start Phase 1 only when Gate 0 is signed; do not start Phase 2 code before Gate 1.
