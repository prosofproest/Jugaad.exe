# D5 — Primary outcome metric (pre-registered)

**Decision ID:** D5
**Status:** `[x]` Pre-registered 2026-11-06 before any pilot observation.
**Owner:** Product lead, with the independent evaluator.
**Needs by:** Gate 0 for the protocol; Gate 5 for the silent-phase evidence.
**Pre-registration manifest:** [`preregistration.json`](preregistration.json).
**Protocol:** [`pilot-protocol-v1.md`](pilot-protocol-v1.md).

> **No baseline number is asserted here.** The baseline is measured from partner records or a
> concurrent control. If it cannot be measured, the result is reported as "not measured",
> not replaced by an assumed value (R6).

---

## 1. Primary metric

**Name:** Median verified-confirmation lead time (MVCLT).

**Definition:** the median elapsed time from the **first eligible farmer report** for a case
to the **first verified expert confirmation** of that case, in hours, for the pilot allowlist
and zone.

**Direction:** lower is better. The intervention is compared with the existing advisory
baseline or the concurrent control, not with zero.

### 1.1 Measurement

| Element | Definition |
|---|---|
| Unit of analysis | One case (one farmer report of one crop × target concern), not one image and not one reviewer action |
| Start timestamp | `first_report_at`: the client capture timestamp if the report syncs within 7 days; otherwise the server receipt timestamp. The rule is fixed before analysis. |
| End timestamp | `first_verified_confirmation_at`: the audit timestamp when a holder of `can_confirm` sets the case to `confirmed` |
| Eligible case | Tomato in a pilot site; target on the D1a allowlist; required consent complete; not a duplicate; not a test/demo record |
| Excluded | `unsupported_crop`, `unsupported_target`, consent-missing, duplicate, demo/synthetic, internal test accounts |
| Censoring | A case without confirmation at the analysis cutoff is censored at the cutoff for the sensitivity analysis |
| Primary analysis set | Confirmed cases with a valid start and end timestamp |
| Secondary process metric | Proportion of eligible cases confirmed within 48 hours |
| Missing data | Report the count and reason; no silent imputation |

### 1.2 Why this metric

- It is the decision the product exists to improve: how long a farmer waits for a trustworthy
  answer.
- It is measurable from append-only timestamps, not from self-reported satisfaction.
- It is hard to game: confirming faster by lowering the evidence standard is visible in the
  review audit and the false-confirmation audit sample.
- It does not require a yield trial or a claim that the service prevented loss.

---

## 2. Baseline measurement

The baseline is the existing advisory route for the same crop, zone and season. It is
measured in one of two pre-registered ways, in this order:

1. **Retrospective record abstraction.** Partner extension/plant-clinic registers for the most
   recent comparable season (Rabi 2025–26 if available) are abstracted for:
   report/complaint date, first expert contact, confirmation date, outcome and missing fields.
   Two abstractors work independently on a 10% sample; disagreements are adjudicated and the
   agreement measure is reported.
2. **Concurrent control.** If records are incomplete, matched control hoblis continue the
   existing advisory route during the pilot. The same definitions and timestamps are used.

**Baseline report must state:** source, date range, inclusion rules, number of records,
missingness, abstraction agreement, and whether the baseline is retrospective or concurrent.
No baseline median is written into this document until that report exists.

---

## 3. Comparison and analysis plan

| Item | Pre-registered choice |
|---|---|
| Primary estimand | Difference in median MVCLT (control/baseline minus intervention), in hours |
| Effect measure | Median difference with 95% bootstrap confidence interval (10,000 resamples, stratified by site) |
| Secondary effect | Hazard ratio from a Cox proportional-hazards model with site and crop stage as covariates; report the proportional-hazards check |
| Hypothesis test | Two-sided, alpha = 0.05; the confidence interval is the primary evidence, the p-value is supporting |
| Subgroups | Pre-specified only: district, crop stage, target, image-quality pass/fail, verification tier. No post-hoc subgroup claims. |
| Multiplicity | Primary metric only for the expansion decision; secondary metrics are descriptive with confidence intervals |
| Sensitivity analyses | (a) all eligible cases with censoring at 30 days; (b) exclude cases confirmed by the same person who collected the report; (c) per-protocol sites only |
| Reporting | Median, IQR, n, censoring count, missingness, confidence interval; never a single aggregate without the site breakdown |
| Negative result | Reported as a negative result; no re-analysis to find a favourable cut-point |

**Interpretation rule.** A result is **supportive** only if the 95% confidence interval for
the median improvement excludes zero **and** the direction favours the intervention. A
point estimate alone is not evidence. The expansion decision also requires the safety and
capacity conditions in the pilot protocol.

---

## 4. Sample-size logic

The calculation is a planning device, not a claim about the true effect. It assumes
log-normal time-to-confirmation and a two-sided two-sample comparison of log medians.

| Assumption | Value |
|---|---|
| Baseline median | 96 h (planning assumption; replaced by the measured baseline) |
| Target median | 72 h (a 24-hour improvement) |
| Standard deviation of log time | 0.80 |
| Power | 80% |
| Alpha | 0.05 (two-sided) |
| Allocation | 1:1 |
| Calculated n | ~122 confirmed cases per arm |
| Inflated for 20% missing/attrition | ~150 confirmed cases per arm |

**Sensitivity:** a 24-hour improvement from a 120-hour baseline needs ~202 per arm; a
48-hour improvement from a 96-hour baseline needs ~31 per arm. The evaluator records the
measured baseline before the pilot and confirms the feasible n. If the pilot cannot reach the
required n, the report states that it is underpowered and presents confidence intervals
without an expansion claim.

---

## 5. Pre-registration and amendments

- The protocol and this metric are frozen before the first eligible report.
- The SHA-256 hashes are recorded in [`preregistration.json`](preregistration.json).
- Any amendment is dated, numbered, reasoned and signed by the product lead and evaluator
  **before** the affected analysis is run. Amendments after seeing outcome data are
  reported as deviations and cannot support the primary claim.
- The validator recomputes the hashes; a mismatch fails the Phase 0 check until the manifest
  is updated through a recorded amendment.

**Sign-off**

| Role | Name | Decision | Date |
|---|---|---|---|
| Product lead | TBD at workshop | Pending | — |
| Independent evaluator | TBD at workshop | Pending | — |
| Agronomist | TBD at workshop | Pending | — |
