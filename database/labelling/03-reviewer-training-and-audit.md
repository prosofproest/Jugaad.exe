# Reviewer training, quality sampling and label audit

**Version:** `v1.0-draft`
**Status:** Draft — **no reviewer trained, no competency signed off, no audit run.**
**Owner:** Pathologist (training and label authority — D13), with Field operations (roster)
and Data engineer (sampling and records)
**Last updated:** 2026-11-06
**Authorities:** `final/docs-context/phase-plan.md` §4.4;
`final/docs-context/data-foundation.md` §4.2, §5;
`final/feature-specs/04-expert-review.md` §2, §6, §7, §13, §14;
`final/docs-context/AGENTS.md` R4, R6;
`final/docs-context/progress-tracker.md` D3, D7, D8, D13;
`database/labelling/01-labelling-handbook.md`,
`database/labelling/02-reviewer-calibration.md`.

> **Rule:** a reviewer is authorised to label only after competency is signed off against the
> current handbook version. A label from an unauthorised reviewer is not a training label.

---

## 1. Roles and authority

| Role | May label | May adjudicate | May train/sign off | Constraint |
|---|---|---|---|---|
| `extension_worker` | `probable`, `needs_visit`, `duplicate`, `unresolved` | No | No | Cannot set `confirmed`; escalates |
| `pathologist` | `confirmed`, all correction and taxonomy decisions | Yes | Yes | Sole label/taxonomy authority (D13) |
| `agronomist` | No | No | Advises on crop/severity only | **Cannot** set or approve a label |
| `data engineer` | No | No | No | Builds sampling and records |
| `admin` | No | No | No | Cannot set verification status |

A reviewer may not review their own submitted case where a conflict of interest exists.

---

## 2. Training curriculum

Training is role-specific. It uses the approved handbook and real, permissioned examples —
never fabricated examples presented as real.

| Module | Content | Assessment |
|---|---|---|
| M1 — Why labels matter | Two outputs; label vs diagnosis; R2/R4/R6; consequence of a wrong label | Short written check |
| M2 — Label semantics | "Consistent with"; class vs evidence tier; model output is never a label | Scenario questions |
| M3 — Class kinds | Pathogen identity vs symptom pattern vs pest damage | Class-kind sorting exercise |
| M4 — Crop-specific taxonomy | Every class card for the supported crop (D1); definitions and boundaries | Class-card quiz |
| M5 — Uncertainty | `unknown` vs `mixed_symptoms` vs `insufficient_evidence`; decision order | Boundary-case set |
| M6 — Severity | Crop-specific scale; field vs adjudicated; `not_assessed` | Severity anchor exercise |
| M7 — Evidence tiers | `suspected` vs `expert_confirmed` vs `lab_confirmed`; what counts as evidence | Evidence-tier scenarios |
| M8 — Blinding and process | Decision before model reveal; double-read; queue; locks; audit | Process checklist |
| M9 — Provenance | Handbook/taxonomy version; append-only correction; reviewer identity handling | Record-keeping check |
| M10 — Hard negatives and ambiguity | Retain, do not delete; abstention is data | Labelling exercise |
| M11 — Privacy and safety | No PII in notes; no chemical advice; escalation | Signed acknowledgement |

### 2.1 Training set requirements

- Examples are drawn from permissioned data and labelled by a pathologist.
- Cover every class, every uncertainty class, every severity band and the boundary cases.
- Include hard negatives and ambiguous images; a training set of clear positives is invalid.
- Include examples where the correct answer is `insufficient_evidence`.
- Archive examples, if used, are labelled as archive and never presented as field examples.

### 2.2 Competency sign-off

A reviewer is authorised only when all of the following are recorded:

- [ ] Completed every module for their role.
- [ ] Passed the class-card and uncertainty assessments against the **current** handbook
      version.
- [ ] Completed a supervised labelling set with an agreed pass standard (`TBD — D8`).
- [ ] Demonstrated correct use of `insufficient_evidence` and `unknown`.
- [ ] Demonstrated correct evidence tier and severity recording.
- [ ] Signed the privacy and no-chemical-advice acknowledgement.
- [ ] Signed off by a pathologist, with date and handbook version.

The sign-off is version-bound. A material handbook revision triggers re-training before the
reviewer continues (or before their next shift, if the change is narrow and documented).

---

## 3. Quality sampling

### 3.1 Purpose

Detect label drift, handbook ambiguity and reviewer error **before** they contaminate a
training or evaluation set. Auditing is not performance ranking.

### 3.2 Sampling design

| Sample | What is checked | Frequency | Size |
|---|---|---|---|
| Random recent decisions | Class, uncertainty, severity, evidence tier | Weekly (proposed) | `TBD — D8` |
| Stratified by class | Every class, including uncertainty classes | Monthly (proposed) | At least `TBD` per class |
| Boundary/hard cases | Look-alikes, `mixed_symptoms`, `insufficient_evidence` | Monthly (proposed) | Oversampled |
| New reviewers | First decisions after sign-off | First `TBD` decisions | 100% until cleared |
| After a revision | Decisions using the new handbook version | First `TBD` decisions | 100% until cleared |
| High-consequence labels | `confirmed`, `lab_confirmed`, corrections | Continuous | `TBD` sample |
| Archive mappings | Separate audit under `../archive/02-label-reconciliation.md` | Per batch | `TBD` |

Proposed frequencies and sizes are **planning defaults**, not decisions. The approved values
must be recorded before the audit programme starts; `TBD — D8` covers the statistical
parameters.

### 3.3 Sampling rules

- The sample is drawn by the data engineer, not chosen by the reviewer.
- Selection is recorded (seed, strata, date range) so it is reproducible.
- No reviewer audits only their own labels.
- The auditor is a pathologist or a reviewer designated by the pathologist.
- The auditor sees the original label, evidence and handbook version; not model output.
- Disagreements follow the calibration adjudication process
  (`02-reviewer-calibration.md` §7).
- A failed audit does not delete a label; it triggers correction, retraining or a handbook
  revision.

---

## 4. Label-audit cadence

| Cadence | Activity | Output | Owner |
|---|---|---|---|
| Per batch / per shift | Automated checks: required fields, version, evidence tier, uncertainty use | Batch exception report | Data engineer |
| Weekly (proposed) | Random sample audit | Audit report; corrections opened | Pathologist |
| Monthly (proposed) | Stratified audit across all classes and severity bands | Class-level pass/fail; drift signals | Pathologist + ML lead |
| Quarterly (proposed) | Calibration re-round or targeted re-audit | Agreement result; handbook change list | Pathologist + ML lead |
| On every handbook revision | Re-training and audit of first decisions | Sign-off and audit result | Pathologist |
| Annual (proposed) | Full handbook, taxonomy and severity review | New handbook version or reaffirmation | Pathologist + agronomist |
| On demand | Triggered by a spike in corrections, disputes or a field complaint | Targeted audit | Pathologist |

Cadence is operational and may change; the approved cadence and sample sizes must be recorded
and versioned. A cadence is never claimed as run when it was not.

---

## 5. Metrics

Reported with denominators and never used as a league table:

- labels audited / labels produced (coverage of the audit);
- exact-match agreement between reviewer and auditor, per class;
- correction rate and reason code;
- uncertainty-class usage rate (is `insufficient_evidence` being over- or under-used?);
- evidence-tier distribution;
- severity disagreement and direction;
- handbook clarifications raised per audit;
- time-to-correct a failed audit;
- retraining completions.

No target value is asserted here. Targets and thresholds are `TBD — D8` or set by the
programme and recorded.

---

## 6. Drift and remediation

| Signal | Response |
|---|---|
| One class repeatedly disagreed | Review the class card; add examples; retrain |
| Uncertainty class over-used | Check for unclear definitions or pressure to decide |
| Uncertainty class under-used | Check for forced labels; audit boundary cases |
| Severity disagreement clustered at a band edge | Re-anchor the crop-specific scale |
| One reviewer's corrections above the audit norm | Coaching and supervised re-labelling; not public ranking |
| A taxonomy gap recurs | Escalate to D1; do not invent a class |
| Archive mapping drift | Re-run reconciliation under a new version |

Remediation is documented. A repeated failure after retraining is escalated to the
pathologist and may result in the reviewer losing label authority for that class until
re-signed off.

---

## 7. Records

| Record | Requirement |
|---|---|
| Training completion | Reviewer, module, date, handbook version |
| Competency sign-off | Reviewer, assessor, result, date, handbook version |
| Supervised set result | Set ID, items, outcome |
| Audit sample | Seed, strata, date range, item IDs, auditor |
| Audit result | Label, auditor label, agreement, reason, correction link |
| Retraining | Trigger, module, date, sign-off |
| Revocation | Reason, effective date, classes affected |

Reviewer training records are personal data: store account references and role, not unnecessary
personal details, and restrict access.

---

## 8. What must never happen

- Letting an untrained reviewer label training data.
- Signing off competency against an outdated handbook without re-training.
- Letting a reviewer choose their own audit sample.
- Auditing only easy or positive cases.
- Deleting a label because an audit disagreed with it.
- Publishing a reviewer ranking.
- Using an audit result as a label without adjudication.
- Recording a cadence or metric that was not actually run.
- Fabricating a competency sign-off, reviewer identity or audit result.
- Letting the agronomist approve a label.
- Using model output to judge whether a reviewer is correct.

---

## 9. Acceptance criteria

- [ ] Every reviewer has a recorded, version-bound competency sign-off before labelling.
- [ ] Training covers every class, all uncertainty classes, severity, evidence tiers, hard
      negatives and privacy/safety.
- [ ] Training examples are permissioned and pathologist-labelled; no fabricated examples
      presented as real.
- [ ] The audit sample is drawn independently, stratified and reproducible.
- [ ] Audit frequency and sample size are recorded, not implied.
- [ ] Disagreements are adjudicated, not deleted.
- [ ] Corrections are append-only and linked to the audit.
- [ ] Drift signals lead to a handbook revision or retraining, not a lowered standard.
- [ ] Reviewer records are minimised and access-controlled.
- [ ] No reviewer ranking is produced.
- [ ] The audit cadence is reported honestly, including missed or incomplete rounds.
