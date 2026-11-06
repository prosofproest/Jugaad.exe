# Reviewer calibration round

**Version:** `v1.0-draft`
**Status:** Draft — **no calibration round has been run, no data labelled, no agreement measured.**
**Owner:** Pathologist (adjudicator) + ML lead (measurement) + Data engineer (sampling and
records)
**Last updated:** 2026-11-06
**Authorities:** `final/docs-context/phase-plan.md` §4.4;
`final/docs-context/data-foundation.md` §4.2, §4.3;
`final/feature-specs/04-expert-review.md` §3 (blinding), §6 (FR-04-21, FR-04-22), §7;
`final/docs-context/progress-tracker.md` D7, D8, D13;
`database/labelling/01-labelling-handbook.md`.

> **Purpose:** prove that two qualified reviewers, working independently under the handbook,
> reach the same label often enough to trust the dataset — and fix the handbook where they do
> not. Calibration is a gate on scaling annotation, not a box-ticking exercise.

---

## 1. When a round is run

1. After the taxonomy is approved (D1) and the handbook is issued as a reviewable draft.
2. Before annotation scales beyond the calibration subset.
3. After any material handbook revision (§8).
4. On a scheduled cadence once production labelling starts
   (`03-reviewer-training-and-audit.md`).

A round is **not** run on an unapproved taxonomy. Doing so would measure agreement on
classes that do not exist.

---

## 2. Subset design

The calibration subset must be **representative of the work reviewers will actually do**, not
a convenient set of clear examples.

### 2.1 Stratification

Stratify by:

| Dimension | Why |
|---|---|
| Crop | The handbook is crop-specific (D1) |
| Condition class | Every supported class, including uncertainty classes |
| Severity band | `SEV-0` to `SEV-4` where applicable |
| Evidence quality | Good, marginal and `insufficient_evidence` |
| Boundary cases | Confusable classes and look-alikes |
| Source | Field, farmer-submitted and archive-mapped, reported separately |
| District / season | If the pilot has more than one |
| Device / lighting / background | If available; otherwise record as a limitation |

### 2.2 Inclusion rules

- Include `healthy`, `abiotic_look_alike`, `unknown`, `mixed_symptoms` and
  `insufficient_evidence`; a calibration set of only positive examples is invalid.
- Include hard negatives and ambiguous images.
- Include at least the boundary cases named in the class cards.
- Do not include the same case twice, and do not leak near-duplicates across reviewers.
- Archive records may be included only under their permission record and only as a separate
  reported stratum.

### 2.3 Size and agreement threshold

**`TBD — D8`.** The repository does not yet have an approved subset size or agreement
threshold. `04-expert-review.md` states that D8 sets both (`FR-04-22`).

Until D8 is recorded, the following is a **proposed planning default, not an approved
decision**:

- at least 30 items per supported condition class, and at least 150–200 items in total;
- the subset is fixed and versioned before labelling begins;
- the same subset is used for the re-round after a handbook revision, so change is
  measurable.

The actual numbers must be recorded as a decision before the round. They are never
back-filled after seeing the results.

---

## 3. Independence and blinding

| Control | Requirement |
|---|---|
| Independent labels | Each reviewer labels the subset alone; no discussion, shared notes or group review |
| Blind to model | No model candidates, scores, forecasts or predictions are visible |
| Blind to other reviewer | Reviewer B does not see Reviewer A's labels or comments |
| Blind to gold | No "correct answer" is shown during labelling |
| Randomised order | Items are presented in a different, recorded order per reviewer to reduce order effects |
| Same information | Both reviewers receive the same image(s), metadata, handbook version and taxonomy version |
| Time-boxed | A reviewer may mark `insufficient_evidence`; no obligation to decide |
| Recorded | Reviewer, start/end time, handbook version, item order and any technical issue are logged |

If blinding is broken, the affected items are excluded from the agreement computation and
the reason is recorded. They are not silently scored.

---

## 4. What is compared

Two labels are compared on three levels, separately:

| Level | Comparison | Why |
|---|---|---|
| 1. Class | `target_code` exact match | Primary agreement |
| 2. Class group | Agreement at the `class_kind` or higher group level (for example any `symptom_pattern`, or target vs non-target) | Distinguishes "different label" from "different kind of judgement" |
| 3. Severity | Severity band, where both reviewers assigned one | Ordinal agreement; `not_assessed` is not a band |

Additional comparisons:

- uncertainty class vs positive class (does one reviewer abstain where the other commits?);
- `label_origin` tier, where it differs;
- reason for `insufficient_evidence`.

A single aggregate number is not a result. Report class-level and stratum-level results with
counts.

---

## 5. Agreement measures

Report all of the following, with confidence intervals where the sample allows:

| Measure | Use | Note |
|---|---|---|
| Observed percent agreement | Overall and per class | Easy to read; inflated by class imbalance |
| Cohen's kappa | Two reviewers, nominal classes | Report alongside percent agreement |
| Fleiss' kappa | Three or more reviewers | Only if the design uses more than two |
| Gwet's AC1 | Two reviewers, skewed prevalence | Proposed robustness check; label as proposed |
| Weighted kappa (linear/quadratic) | Severity, ordinal | State the weighting |
| Per-class agreement / confusion matrix | Class-level diagnosis | Required; aggregate hides a failing class |
| Abstention agreement | `insufficient_evidence` / `unknown` / `mixed_symptoms` | Required — abstention is data |
| Coverage / denominator | Items, missing, excluded | Every rate needs a denominator |

Rules:

- Never report kappa without percent agreement and class counts.
- Never report one aggregate number as "inter-reviewer agreement".
- Never drop a class or a hard case to raise agreement.
- Missing or excluded items are reported, not silently removed.
- If a measure is unstable because a class has too few items, say so; do not invent a value.

**Agreement threshold:** `TBD — D8`. A round that does not meet the approved threshold does
not proceed to scaled annotation; it goes to §7.

---

## 6. Disagreement taxonomy

Every disagreement is classified before adjudication. This is what turns a number into a
handbook fix.

| Code | Meaning | Typical fix |
|---|---|---|
| `definition_ambiguous` | The class card does not say what is included | Rewrite the definition and boundary cases |
| `missing_example` | Reviewers cannot picture the class | Add typical and boundary example images |
| `look_alike_unresolved` | A confusable class is not distinguished | Add a distinguishing feature and a paired example |
| `severity_anchor_unclear` | Bands overlap or are not observable | Re-anchor the crop-specific scale |
| `evidence_insufficient` | The image genuinely cannot support a decision | Legitimately `insufficient_evidence`; retain |
| `metadata_ambiguous` | Crop, part, stage or context is unclear | Fix capture metadata, not the label |
| `reviewer_error` | One reviewer misapplied a clear rule | Retrain/remediate; do not change the handbook |
| `true_biological_ambiguity` | Two conditions genuinely co-occur or are indistinguishable | `mixed_symptoms` or `unknown`; retain |
| `taxonomy_gap` | No class fits | Feed back to D1; do not invent a class |
| `process_error` | Blinding, ordering or tooling failure | Exclude item from measurement; fix process |

---

## 7. Adjudication

1. A **third qualified reviewer** — the pathologist, or a pathologist designated in advance
   — reviews the item and both labels. The adjudicator must not be one of the two primary
   reviewers.
2. The adjudicator sees the item, the handbook, both labels and the disagreement code; they
   do **not** see model output.
3. The adjudicator records one outcome:
   - `label_a`, `label_b`, or a third class;
   - `insufficient_evidence` if the item genuinely cannot be decided;
   - `mixed_symptoms` if both conditions are present;
   - `unmappable`/`taxonomy_gap` if no class fits.
4. The adjudication records: adjudicator, date, outcome, rationale, disagreement code and
   handbook version.
5. If the adjudication changes a class definition, the change goes through the handbook
   revision process (`01-labelling-handbook.md` §8.2); it is **not** applied ad hoc to the
   subset only.
6. If the adjudicator cannot decide, the item becomes `insufficient_evidence` or
   `unmappable` and is retained. It is never forced.
7. Adjudicated labels are training-usable only when they meet the evidence-tier rule. An
   adjudicated `probable` is still `probable`.

### 7.1 Adjudication record fields

| Field | Requirement |
|---|---|
| `adjudication_id` | Stable identifier |
| `item_id` / `observation_id` | What was adjudicated |
| `reviewer_a_label`, `reviewer_b_label` | Original labels, unchanged |
| `disagreement_code` | From §6 |
| `adjudicated_label` | Final class or uncertainty class |
| `adjudicated_severity` | If applicable |
| `rationale` | No PII; cites the handbook rule |
| `adjudicator_id` | Pathologist account reference |
| `adjudicated_at` | UTC |
| `handbook_version` / `taxonomy_version` | Versions in force |
| `handbook_change_required` | `true` / `false` and the proposed change |
| `notes` | No PII |

Original labels are never overwritten. The adjudicated label is a new record linked to both.

---

## 8. Revision loop

```
design subset → independent labels → measure agreement
      → classify disagreements → adjudicate
      → revise unclear definitions / examples / severity anchors
      → re-train reviewers on the revision
      → re-run calibration on the same (or a new, recorded) subset
      → record the result and decide whether to scale
```

Rules:

- A revision is versioned and approved by the pathologist.
- The re-round uses the same item set where possible so improvement is measurable; if a new
  set is used, record why.
- The previous round's results and the revision are retained.
- Scaling annotation requires a recorded pass against the D8 threshold. If D8 is unset,
  scaling is blocked.
- If agreement remains low after a revision, the taxonomy itself may be wrong; escalate to
  D1 rather than lowering the bar.

---

## 9. Calibration record (per round)

| Field | Requirement |
|---|---|
| `round_id` | Stable identifier |
| `handbook_version`, `taxonomy_version` | Versions under test |
| `subset_id`, `subset_size`, `stratification` | What was labelled |
| `reviewers` | Account references; at least two independent |
| `adjudicator` | Pathologist account reference |
| `started_at`, `completed_at` | UTC |
| `items_labelled`, `items_excluded` | Counts and reasons |
| `percent_agreement` | Overall and per class |
| `kappa` / `ac1` / weighted kappa | With method and weighting stated |
| `per_class_results` | Table |
| `abstention_agreement` | Separate result |
| `disagreement_counts` | By code |
| `adjudication_counts` | By outcome |
| `threshold_met` | `true` / `false` / `blocked — D8 unset` |
| `handbook_changes` | Links to revisions |
| `next_action` | Scale, revise, re-train or escalate to D1 |
| `approved_by`, `approved_at` | Pathologist |

No field may be filled with a plausible placeholder. An unmeasured field is blank with a
reason.

---

## 10. What must never happen

- Running calibration on a taxonomy that is not approved.
- Showing model output, forecasts or the other reviewer's labels.
- Reporting a kappa without counts, percent agreement and class-level results.
- Dropping hard cases, uncertainty classes or a whole class to raise agreement.
- Changing the subset after seeing the results without recording why.
- Treating a numeric threshold as met when D8 is unset.
- Adjudicating by majority vote or by the senior reviewer's seniority alone.
- Letting an adjudicator be one of the primary reviewers.
- Applying a definition change only to the calibration items.
- Forcing an adjudicated item into a class when the evidence is insufficient.
- Fabricating an agreement value, subset size or reviewer identity.

---

## 11. Acceptance criteria

- [ ] The subset is stratified, fixed and versioned before labelling, and includes
      uncertainty classes and hard negatives.
- [ ] At least two qualified reviewers label independently and blind.
- [ ] Subset size and agreement threshold are recorded from D8, not invented.
- [ ] Percent agreement, kappa/AC1 (as applicable), weighted kappa for severity, per-class
      results and abstention agreement are reported with denominators.
- [ ] Every disagreement is coded and adjudicated by a third qualified reviewer.
- [ ] Unclear definitions are revised through the handbook revision process.
- [ ] Reviewers are re-trained after a revision and a re-round is recorded.
- [ ] The round record states `threshold_met` and the next action.
- [ ] Items that cannot be decided are retained as `insufficient_evidence` or `unmappable`.
- [ ] Scaling annotation is blocked until a round passes.
