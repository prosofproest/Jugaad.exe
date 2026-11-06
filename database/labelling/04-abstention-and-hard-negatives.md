# Hard negatives and ambiguous images for abstention training

**Version:** `v1.0-draft`
**Status:** Draft — **no hard-negative or ambiguous-image set has been assembled.**
**Owner:** Pathologist (label and adjudication), ML lead (abstention use), Data engineer
(retention and schema), Field operations (capture)
**Last updated:** 2026-11-06
**Authorities:** `final/docs-context/phase-plan.md` §4.2, §4.4, §6.4, §6.5;
`final/docs-context/data-foundation.md` §4.3, §5, §10;
`final/docs-context/AGENTS.md` R2, R3, R4, R6;
`final/docs-context/progress-tracker.md` D7, D8;
`database/labelling/01-labelling-handbook.md`,
`database/governance/06-quarantine-policy.md`.

> **Rule:** an image that is hard, ambiguous or not the target is **required data**. It is
> the evidence that teaches the system to abstain. It is never deleted to make the dataset
> look cleaner or more accurate.

---

## 1. Why these images are retained

An image model that only sees clear positives learns to force a class. Abstention is a
product requirement (R2), not an error path, so the data that triggers abstention must be
collected and labelled deliberately:

- hard negatives teach the boundary between a target and its look-alikes;
- ambiguous images teach the model and the reviewer where evidence is insufficient;
- out-of-scope inputs teach the system to refuse rather than guess;
- `insufficient_evidence` examples expose capture-quality problems.

Retaining them supports the abstention threshold, OOD detection and honest reporting.

---

## 2. Definitions

| Term | Definition | Not this |
|---|---|---|
| **Hard negative** | A valid image that is plausibly confusable with a supported target but is not that target | Not a corrupt file |
| **Ambiguous image** | A valid image where competent reviewers disagree or the evidence genuinely cannot decide | Not a lazy `unknown` |
| **Out-of-domain image** | A valid image outside the supported crop, target, device or capture condition | Not a positive class |
| **Uncertainty label** | `unknown`, `mixed_symptoms` or `insufficient_evidence` | Not a rejection reason |
| **Forecast negative** | A verified absence from a scheduled sentinel-panel visit (D7) | **Not** an image label |

**The distinction matters:** an image hard negative is not a forecast negative, and a
forecast sentinel visit is not an image label. The two must never be mixed.

---

## 3. Hard-negative categories

| Code | Category | Examples | Retained as |
|---|---|---|---|
| `HN-HEALTHY` | Healthy tissue | No visible symptom on the supported crop | `healthy` |
| `HN-ABIOTIC` | Abiotic look-alike | Nutrient, water, heat, chemical injury | `abiotic_look_alike` |
| `HN-OTHER-CONDITION` | Another condition on the supported crop | A non-target disease or pest | The actual class if defined; else `unknown` |
| `HN-OTHER-CROP` | A different crop | Non-supported crop | `crop_unknown` / out-of-domain |
| `HN-NON-PLANT` | Not a plant | Soil, tool, hand, building | Rejection reason `not_a_plant` |
| `HN-POOR-IMAGE` | Valid subject, unusable evidence | Blur, wrong part, extreme exposure | `insufficient_evidence` |
| `HN-LOOK-ALIKE` | A named confusable class | Class-specific look-alike from the class card | The look-alike class |
| `HN-ARCHIVE-NEAR` | Archive image close to a field condition | Archive look-alike | Archive record, separate family |

A hard negative keeps its **true** label, not a synthetic "negative" label. "Hard negative"
is a sampling/training role recorded in a separate field, not a class.

---

## 4. Ambiguous-image handling

| Situation | Label | Retention |
|---|---|---|
| Genuine disagreement between qualified reviewers | `label_status = ambiguous`; adjudicate | Retain; adjudicated label is new record |
| Genuinely insufficient evidence | `insufficient_evidence` | Retain; mark for abstention |
| Two conditions co-occur | `mixed_symptoms`; primary + secondary | Retain; multi-label |
| Adequate image but no class fits | `unknown` | Retain; feed taxonomy gap to D1 |
| Out of supported crop/domain | out-of-domain label / rejection reason | Retain as hard negative |
| Adjudicator cannot decide | `insufficient_evidence` or `unmappable` | Retain; never force |

Ambiguous images are not a temporary state to be cleaned away. The adjudicated outcome is
recorded and the original labels are retained.

---

## 5. Retention and storage

- Hard negatives and ambiguous images are stored in the same private object store as other
  permissioned images, with their labels and provenance.
- They are never deleted because a validator, a reviewer or a cleaning job dislikes them.
- If a record is deleted, it follows the approved retention/deletion procedure
  (`../governance/05-retention-and-deletion.md`) with an audit record — never a side effect
  of dataset cleaning.
- Archive hard negatives stay in the archive family and are never mixed into field data.
- The dataset register records counts separately from positive examples.

### 5.1 Proposed fields

| Field | Type | Requirement |
|---|---|---|
| `hard_negative` | boolean | `true` for retained hard negatives |
| `hard_negative_code` | text | From §3 |
| `hard_negative_reason` | text | Why it is confusable; no PII |
| `label_status` | text | `active`, `ambiguous`, `adjudicated`, `superseded` |
| `abstention_role` | text | `insufficient_evidence`, `unknown`, `mixed`, `out_of_domain`, `hard_negative`, `none` |
| `ambiguity_reason` | text | From the disagreement taxonomy, when ambiguous |
| `adjudication_id` | uuid | Link to the adjudication record |
| `retain_for_abstention` | boolean | Must be `true` until an approved deletion |
| `dataset_family` | text | `field` or `archive`; never merged |

---

## 6. Use in training and evaluation

| Use | Allowed | Rule |
|---|---|---|
| Positive target training | No | A hard negative is not a target |
| Abstention/negative-of-target training | Yes | Keep the true label; do not relabel as "negative" |
| OOD detection | Yes, if the OOD design uses them | Record the method and version |
| Threshold selection | Yes, on validation, never on the frozen test set | `06-forecast-and-risk-map.md` / `ml-models.md` |
| Frozen field test set | Only as field test items, never as archive items | Archive records are never in the field test set |
| Reported abstention metrics | Yes | Report with denominators and at the shipped threshold |
| Forecast features | No | An image hard negative is not a forecast negative |
| Evidence of absence | No | A hard negative is not a "no outbreak" observation |

Rules:

- Do not balance the dataset by deleting hard negatives.
- Do not relabel a hard negative as a positive to increase class counts.
- Do not use the same hard negative in both training and the frozen test set.
- Do not use archive hard negatives as field evaluation evidence.
- Do not select the abstention threshold on the test set; use validation.

---

## 7. Collection and quotas

Hard negatives and ambiguous images must be **collected deliberately**, not only encountered
by accident.

| Source | Requirement |
|---|---|
| Sampling matrix | Hard negatives and ambiguous cases are a special stratum (`../collection/02-sampling-matrix.md`) |
| Enumerator guidance | Capture look-alikes, healthy controls and difficult cases when encountered |
| Farmer submissions | Retain rejected and ambiguous cases; do not discard after review |
| Archive intake | Retain unmappable and conflicting records in the archive family |
| Quality gate | Failed-quality images are retained as `insufficient_evidence`, not deleted |

Quotas per class and per hard-negative code are `TBD — D1/D8`. They must be set before the
collection target is declared met; a total image count does not substitute for coverage.

---

## 8. Metrics

- hard negatives retained, by code and by dataset family;
- ambiguous items, by reason and adjudication outcome;
- `insufficient_evidence` rate and trend;
- out-of-domain rate;
- abstention rate at the shipped threshold (reported on validation and field test);
- abstention performance on hard negatives and unsupported inputs;
- deleted hard negatives / ambiguous items (should be zero except approved deletion).

Every rate is reported with its denominator. No target is asserted here.

---

## 9. What must never happen

- Deleting a hard negative or ambiguous image to clean the dataset.
- Relabelling a hard negative as a positive target.
- Creating a synthetic "negative" class that hides the true label.
- Treating an image hard negative as a forecast negative.
- Mixing archive hard negatives into field data or the frozen field test set.
- Using the frozen test set for threshold tuning.
- Dropping `insufficient_evidence` images after a failed quality gate.
- Reporting an abstention rate without the threshold and denominator.
- Fabricating a hard-negative quota or retention count.

---

## 10. Acceptance criteria

- [ ] Hard-negative and ambiguous-image definitions are recorded and understood by reviewers.
- [ ] Every hard negative keeps its true label plus a hard-negative code.
- [ ] Ambiguous images are adjudicated and retained; original labels are preserved.
- [ ] `unknown`, `mixed_symptoms` and `insufficient_evidence` are retained and counted.
- [ ] Hard negatives are never used as positive targets or forecast negatives.
- [ ] Archive hard negatives remain in the archive family.
- [ ] Quotas are set before coverage is declared met; `TBD` is recorded where unset.
- [ ] Abstention is evaluated on hard negatives and unsupported inputs with denominators.
- [ ] No hard negative or ambiguous image is deleted outside the approved deletion process.
- [ ] The abstention threshold is selected on validation, not the frozen test set.
