# Enumerator training and pilot collection

**Version:** `v1.0-draft`
**Status:** Draft — no training delivered, no pilot run.
**Owner:** Field operations lead (TBD) + Agronomist (TBD) + Data engineer (TBD)
**Last updated:** 2026-11-06
**Authorities:** `final/docs-context/phase-plan.md` §4.2;
`final/docs-context/data-foundation.md` §3, §5;
`final/feature-specs/03-auth-and-roles.md` §3.

> **Rule:** nobody collects field data for the project until they are trained, assessed and
> signed off. A pilot batch is a measurement exercise, not a production collection.
>
> **Entry condition:** no real farmer data may be collected before the dataset permission
> record, consent wording and DPIA are in place. Until then the pilot is a **dry run** with
> synthetic or staff-owned test images.

---

## 1. Objectives

The training and pilot exist to answer four questions with evidence:

1. Can collectors apply the capture protocol consistently?
2. What is the realistic throughput per collector-day?
3. What proportion of images and cases is rejected, and why?
4. Which parts of the protocol, app or training fail in the field and must change?

They do **not** exist to produce a large dataset, to hit a total count, or to make the
protocol look successful.

---

## 2. Roles

| Role | Responsibility |
|---|---|
| Field operations lead | Owns training delivery, pilot logistics, collector sign-off |
| Agronomist | Owns symptom, severity and condition content; **cannot** set verification status |
| Pathologist | Reviews sampled cases and verification decisions; sole role that can set `confirmed` |
| Data engineer | Owns app, upload, quality gate, metrics and the tracking sheet |
| Trainer | Delivers modules; may be the field lead with agronomist support |
| Supervisor | Spot-checks captures; signs off collector competency; ratio `TBD` |
| Collector (enumerator / extension worker) | Captures cases; records metadata; follows the protocol |
| Privacy/legal owner | Approves consent script and handles incidents |

---

## 3. Training curriculum

Each module has a short assessment. Pass criteria are `TBD` until the pilot sets a baseline;
the default is "demonstrated correctly on two consecutive attempts".

| # | Module | Content | Assessment |
|---|---|---|---|
| M1 | Why this data matters | Domain shift, reporting bias, abstention, why honesty beats volume; R1–R10 in plain language | Short oral check |
| M2 | Consent and privacy | What consent is asked, what it means, how to withdraw, what not to photograph, how to explain the service is not a diagnosis | Role-play + scenario quiz |
| M3 | Capture protocol | Shot list S1–S5, distance, angle, lighting, background, plant part, multiple images per case | Practical capture of a set of plants |
| M4 | Severity and symptoms | Crop-specific severity criteria, how to record before photographing, what "not sure" means | Agronomist-scored practical |
| M5 | Metadata | Every required field, allowed values, unknown vs zero, why wrong metadata is worse than missing metadata | Metadata exercise with deliberate errors |
| M6 | Offline app and upload | Local queue, sync, retry, storage, battery, what to do on failure | Simulated offline capture and upload |
| M7 | Quality self-check and re-takes | The before-upload checklist, when to re-take, how re-takes are counted | Practical with seeded bad images |
| M8 | Field ethics and safety | Permission to enter, no pressure to consent, no chemical advice, handling bystanders and children, incident reporting | Scenario quiz |
| M9 | Pilot procedure and feedback | How the pilot is run, what is measured, how to report a protocol problem | Signed acknowledgement |

### 3.1 Non-negotiable training messages

- The service gives an **assessment**, not a diagnosis.
- The project **never** gives chemical advice — no product names, doses, mixtures or intervals.
- "No report" is not evidence of absence.
- An unclear case is recorded as unclear; it is not forced into a class.
- A bad image is re-taken; it is not deleted to hide a failure.
- Consent is voluntary; a farmer can refuse without losing anything.
- Personal data never goes into notes or image frames.

---

## 4. Competency sign-off

A collector is signed off only when all of these are recorded:

- [ ] All modules attended.
- [ ] Practical capture assessment passed by the agronomist or trainer.
- [ ] Metadata exercise passed with no required-field errors.
- [ ] Consent role-play passed.
- [ ] Offline/upload simulation passed.
- [ ] First `N` supervised cases accepted (`N` `TBD`, proposed 5–10).
- [ ] Signed acknowledgement of the protocol version and the no-chemical-advice rule.

### 4.1 Training record

| Field | Type | Requirement |
|---|---|---|
| `collector_id` | uuid | Linked to the user account |
| `training_version` | text | Curriculum version delivered |
| `protocol_version` | text | Capture protocol version taught |
| `modules_completed` | text[] | Module codes |
| `assessment_results` | jsonb | Per-module result |
| `supervised_cases` | integer | Count accepted under supervision |
| `signed_off_by` | uuid | Supervisor |
| `signed_off_at` | timestamptz | UTC |
| `revalidation_due` | date | `TBD` cadence |
| `notes` | text | No PII |

Training records are retained and audited. A collector whose protocol version is out of date
is not assigned new cases until re-trained.

---

## 5. Pilot collection batch

### 5.1 Purpose

Measure the protocol under realistic conditions and revise it **before** scaling collection.
The pilot is deliberately small and instrumented.

### 5.2 Entry criteria

- [ ] D1 crop/target/zone decided, or the pilot is explicitly a dry run.
- [ ] Dataset permission recorded for the pilot area (`01-dataset-register.md`).
- [ ] Consent wording approved and capture live.
- [ ] DPIA signed (`04-dpia.md`).
- [ ] Capture protocol `v1.0-draft` approved for pilot.
- [ ] Sampling matrix `v1.0-draft` approved; `n_min` set for pilot cells.
- [ ] App build with offline queue and metadata fields.
- [ ] Secure upload and storage live (`04-secure-upload-and-retention.md`).
- [ ] Quality gate reachable and logging results.
- [ ] Quarantine queue reachable (`06-quarantine-policy.md`).
- [ ] Training complete for all pilot collectors.

If any of the first four is missing, the pilot runs only on **synthetic or staff-owned test
images** and is labelled a dry run. It does not produce operational data.

### 5.3 Scope parameters (to be set before the pilot)

| Parameter | Value | Owner |
|---|---|---|
| Pilot districts | `TBD — D1` | Field ops |
| Pilot crops | `TBD — D1` | Agronomist |
| Number of collectors | `TBD` | Field ops |
| Number of supervisor-days | `TBD` | Field ops |
| Duration | `TBD` — long enough to cover at least two lighting conditions and one full week | Field ops |
| Target cases | `TBD` — derived from pilot cells, not a round number | Data engineer |
| Device mix | At least one `DEV-LOW` and one `DEV-MID` | Field ops |
| Weather window | Record actual conditions; do not wait only for ideal weather | Field ops |

### 5.4 What the pilot records

Every case follows the capture protocol. In addition, the pilot records:

- attempt counts per shot type;
- time per case (capture start to submit);
- time per image;
- upload success, retry count and failure reason;
- app crashes and battery/storage events;
- supervisor spot-check result;
- whether the case filled a matrix cell;
- collector's free-text note on protocol problems (no PII).

---

## 6. Metrics

All metrics are computed from app events, server records, quality-gate results and the
quarantine log — not from memory or a separate tally.

### 6.1 Throughput

| Metric | Definition |
|---|---|
| Cases per collector-day | Accepted cases ÷ collector-days worked |
| Median time per case | Capture start → confirmed submit |
| Median time per image | Capture → upload confirmed |
| Images per accepted case | Submitted images ÷ accepted cases |
| Accepted images per hour | Accepted images ÷ field hours |
| Upload success rate | Confirmed uploads ÷ attempted uploads |
| Sync failure rate | Cases with a failed sync event ÷ cases attempted |
| Silent losses | Cases queued but never uploaded and never reported. **Must be zero.** |

### 6.2 Reject and quality

| Metric | Definition |
|---|---|
| Capture re-take rate | Re-takes ÷ (submitted shots + re-takes) |
| System reject rate | Images with quality result `fail` ÷ submitted images |
| Case reject rate | Cases with no usable image ÷ submitted cases |
| Metadata incompleteness rate | Cases missing a required field ÷ submitted cases |
| Duplicate rate | Exact or perceptual duplicates ÷ submitted images |
| Quarantine rate | Quarantined records ÷ ingested records |
| Quarantine reason mix | Count by `reason_code` (`../governance/06-quarantine-policy.md`) |
| Privacy re-take rate | Re-takes for people/documents ÷ submitted shots |

### 6.3 Representativeness

| Metric | Definition |
|---|---|
| Matrix cells touched | Cells with ≥ 1 accepted case ÷ required pilot cells |
| Matrix cells met | Cells at `n_min` ÷ required pilot cells |
| Device coverage | Accepted cases per `DEV-*` class |
| Lighting coverage | Accepted cases per `L-*` stratum |
| Severity coverage | Accepted cases per `SEV-*` band |
| Farmer-context share | `CTX-FARMER` cases ÷ accepted cases |
| Special-stratum counts | Healthy, abiotic, ambiguous, hard negative, rejected |

### 6.4 Cost and operability

| Metric | Definition |
|---|---|
| Cost per accepted case | Total pilot cost ÷ accepted cases, where cost data exists |
| Cost per accepted image | Total pilot cost ÷ accepted images |
| App crash rate | Crashes ÷ collector-days |
| Device availability | Collector-days with a working device ÷ planned collector-days |

If cost data is not collected, record `not_measured`; do not estimate a number.

---

## 7. Decision rules for revising the protocol

Thresholds (`R_max`, `T_min`, `M_max`) are **`TBD`** and must be set before the pilot starts.
They must not be chosen after seeing the results.

| Observation | Decision |
|---|---|
| System reject rate above `R_max` | Revise the shot that dominates rejects; re-train; re-pilot |
| One reason code dominates rejects | Fix the specific cause (lighting, focus, framing, metadata) before scaling |
| Throughput below `T_min` | Simplify the shot list or the metadata form; do not lower quality standards silently |
| Metadata incompleteness above `M_max` | Redesign the form or training; do not backfill by guessing |
| A required cell is unreachable | Record `blocked`; adjust the matrix with a documented reason |
| Silent losses > 0 | **Stop the pilot.** Fix the queue before any further collection |
| Privacy re-takes > 0 | Re-train on the privacy rule; review the capture guidance |
| Hard negatives or ambiguous cases not found | Add deliberate collection prompts; they do not appear by accident |
| Collector disagreement on severity | Agronomist revises the severity criteria and re-trains |

### 7.1 Protocol revision

- A revision produces a new version (`v1.1`, `v1.2`, …).
- The change log records what changed, why, and which metric triggered it.
- Material changes require re-training and a new competency sign-off.
- Old cases keep their original `protocol_version`.
- The pilot may run more than one revision; each revision's metrics are reported separately.

| Version | Date | Trigger | Change | Approved by |
|---|---|---|---|---|
| `v1.0-draft` | 2026-11-06 | Initial draft | None yet | Not approved |

---

## 8. Pilot report

The pilot concludes with a short report containing:

1. Scope: districts, crops, dates, collectors, devices, weather.
2. Throughput: §6.1 metrics with denominators.
3. Rejects: §6.2 metrics and the reason distribution.
4. Representativeness: §6.3 matrix coverage.
5. Operability: app, upload, battery, storage, connectivity.
6. Failure modes observed in the field.
7. Protocol changes made and the reasons.
8. Training changes made and the reasons.
9. Remaining gaps and blocked cells.
10. Recommendation: scale, revise again, or stop.

The report contains **no personal data**. Case-level examples require permission and must be
de-identified.

---

## 9. What the pilot must not do

- Collect real farmer data without permission, consent and a signed DPIA.
- Count re-takes, duplicates or rejected images as accepted progress.
- Hide a failed upload or a lost case.
- Change `n_min` or the matrix to make coverage look better.
- Give chemical advice, even if a farmer asks.
- Use a stock or borrowed image to fill a missing stratum.
- Treat the pilot as the production dataset. Pilot data is versioned separately and its
  limitations are recorded.

---

## 10. Acceptance criteria

- [ ] Every collector has a training record and a competency sign-off before collecting.
- [ ] Training covers consent, privacy, severity, metadata and offline behaviour.
- [ ] The no-chemical-advice rule is assessed, not only mentioned.
- [ ] Pilot metrics are computed from system records with explicit denominators.
- [ ] Silent case losses are measured and are zero.
- [ ] Reject rate and reason distribution are reported.
- [ ] Matrix coverage is reported, not only total cases.
- [ ] The protocol is revised with a versioned change log before scale-up.
- [ ] Material protocol changes trigger re-training.
- [ ] A dry run is used when permission, consent or DPIA is not in place.
