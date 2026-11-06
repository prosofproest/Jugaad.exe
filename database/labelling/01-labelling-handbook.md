# Labelling handbook v1

**Version:** `v1.0-draft`
**Status:** Draft — **not approved, not issued to reviewers, no label has been produced under it.**
**Owner:** Pathologist (taxonomy and label authority — D13), with Agronomist (crop and
severity advice), ML lead (training use) and Data engineer (schema/provenance)
**Last updated:** 2026-11-06
**Authorities:** `final/docs-context/phase-plan.md` §4.4;
`final/docs-context/data-foundation.md` §4, §6, §8.2;
`final/feature-specs/04-expert-review.md` §3–§7;
`final/docs-context/AGENTS.md` R2, R4, R6, R7;
`final/docs-context/progress-tracker.md` D1, D5, D7, D8, D13;
`database/data-dictionary/data-dictionary-v1.md` §7.

> **What this is:** the contract for how a reviewer turns an image and its context into a
> defensible label. It defines class meaning, uncertainty, severity, evidence tiers,
> provenance and revision. It does **not** define the crop or the target list — those are
> **D1**, and no crop-specific class may be written or used until D1 is recorded.

---

## 1. Scope

Applies to:

- field images captured under `../collection/01-capture-protocol.md`;
- farmer-submitted images;
- archive images being mapped under `../archive/02-label-reconciliation.md` (mapping uses
  this handbook, but archive records stay a separate dataset family);
- adjudicated severity and label corrections;
- the calibration subset, quality audits and hard-negative/abstention data.

Does **not** apply to:

- forecast event labels (D5/D7 — a case label is not an event label);
- sentinel-panel negatives (D7 — a visit is not an image label);
- advisory text approval;
- model outputs. **A model output is never a label.**

---

## 2. Before any label can be written

All of the following must exist. Until they do, the handbook is a framework, not an
operational document.

| Prerequisite | Decision | Owner | State |
|---|---|---|---|
| Crop, agro-climatic zone and 3–5 target conditions | D1 | Product lead + agronomist | Unresolved |
| Project taxonomy and class names | D1 (this handbook) | Pathologist + agronomist | Blocked on D1 |
| Event definition | D5 | Agronomist + product lead | Unresolved |
| Review states and evidence requirements | `04-expert-review.md` §4, §7 | Product lead | Draft |
| Double-read size and agreement threshold | D8 | ML lead + pathologist | Unresolved |
| Label schema and audit fields | `05-data-layer.md`; `../data-dictionary/` | Data engineer | Partly specified |
| Reviewer training and competency sign-off | `03-reviewer-training-and-audit.md` | Pathologist | Draft |

**Hard rule:** a `target_code` may not be populated from a crop-specific table that is
marked `TBD — D1` anywhere in this repository.

---

## 3. Label semantics

A label states **"consistent with X"**, not "X is confirmed". It is an expert judgement on
the available evidence, at a recorded time, under a recorded handbook version.

| Rule | Meaning |
|---|---|
| One primary label per image | Plus optional secondary labels only for `mixed_symptoms` |
| Evidence-bounded | The label is no stronger than the evidence in §6 |
| Not a diagnosis | Never phrased as a confirmed outbreak or laboratory result |
| Not a forecast input | A case label does not enter forecast features unless it passes the D7 eligibility rule |
| Not a model output | Reviewer records the label before model candidates are revealed (D7 blinding) |
| Reversible with audit | A later correction appends a new label; the old one is never edited |

---

## 4. Class architecture

### 4.1 Class kinds

Every condition class declares what it refers to. A reviewer must not read a
pathogen-identity class as a symptom class or vice versa.

| `class_kind` | Refers to | Example shape (not a decision) | Minimum evidence to assert |
|---|---|---|---|
| `pathogen_identity` | A named causal agent or disease | A named blight, rust or spot disease | Image consistent with the disease **and** a supporting field/lab observation; expert tier required |
| `symptom_pattern` | A visible pattern with no asserted agent | "yellowing", "leaf spots", "wilting" | Image review note; may remain `probable` |
| `pest_damage` | Damage attributable to a pest | Feeding holes, mining, webbing | Image review note; pest identity only if evidence supports it |
| `non_condition` | `healthy`, `abiotic_look_alike`, `unknown`, `mixed_symptoms`, `insufficient_evidence` | — | Per §5 |

**Rule:** a `symptom_pattern` class is never renamed to a pathogen class to make the
dataset look more specific. The `class_kind` is part of the label and travels with it.

### 4.2 Required class set per crop

For the single supported crop (D1), the taxonomy must contain at least:

- the supported target conditions (3–5, D1);
- `healthy`;
- `abiotic_look_alike`;
- `unknown`;
- `mixed_symptoms`;
- `insufficient_evidence`.

`not_a_plant` and `poor_image` are **rejection reasons**, not condition classes. They are
retained as hard negatives (§9 and `04-abstention-and-hard-negatives.md`).

### 4.3 Class card (mandatory per class)

Each class is defined by a card. A class without a complete card is not usable.

| Card field | Requirement |
|---|---|
| `target_code` | Stable machine code; never reused |
| `display_name` | Reviewer-facing name |
| `class_kind` | `pathogen_identity`, `symptom_pattern`, `pest_damage`, or `non_condition` |
| `definition` | What the class means, in one paragraph |
| `positive_evidence` | What must be visible or recorded to assert it |
| `boundary_cases` | What is included and what is explicitly excluded |
| `look_alikes` | Confusable classes and the distinguishing feature |
| `minimum_evidence_tier` | `suspected`, `expert_confirmed` or `lab_confirmed` (§6) |
| `severity_applicable` | `yes` / `no`, and which crop-specific scale |
| `example_images` | Reference image IDs covering typical, early, advanced and boundary cases |
| `reviewer_notes` | Short guidance; no chemical advice |
| `handbook_version` | Version in which the card was approved |
| `approved_by` / `approved_at` | Pathologist |

### 4.4 Crop-specific taxonomy (blocked on D1)

The table below is the required shape. **No rows may be filled until D1 is recorded and the
pathologist approves taxonomy v1.** Filling it from a plausible guess is a prohibited
practice (R6).

| `target_code` | Display name | `class_kind` | Definition | Positive evidence | Excluded / boundary | Look-alikes | Min. tier | Severity | Example refs | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| `TBD — D1` | `TBD — D1` | `TBD — D1` | `TBD — D1` | `TBD — D1` | `TBD — D1` | `TBD — D1` | `TBD — D1` | `TBD — D1` | `TBD — D1` | `blocked` |

The crop identity itself is also blocked:

| Field | Value |
|---|---|
| `crop_code` | `TBD — D1` |
| Agro-climatic zone | `TBD — D1` |
| Target count | `TBD — D1` (3–5 per `phase-plan.md`) |
| Taxonomy version | `TBD — D1` (must be pinned before any label) |

**Populating rule:** when D1 is recorded, the agronomist drafts the crop-specific cards, the
pathologist approves them, and the approved set becomes `taxonomy_version = v1`. Every label
records that version.

### 4.5 Healthy and abiotic classes

| Class | Definition | Must not be used as |
|---|---|---|
| `healthy` | No visible symptom of any supported target on the assessed plant/part | A default for an unlabelled or ambiguous image |
| `abiotic_look_alike` | Visible damage consistent with a non-pathogen cause (nutrient, water, heat, chemical injury) — cause stated only if evidence supports it | A diagnosis of a specific nutrient deficiency without evidence |

An `abiotic_look_alike` class is required for abstention and hard-negative training. It is
**not** a "none of the above" bin.

---

## 5. Uncertainty classes

Uncertainty is data, not noise. The three classes are distinct and must not be merged.

| Class | Question it answers | Evidence state | Training use | Forecast use |
|---|---|---|---|---|
| `unknown` | "The image is adequate, but the pattern does not match any supported class." | Adequate, unmatched | Abstention/negative-of-target training; never a positive target | Never an event |
| `mixed_symptoms` | "Two or more supported conditions are visible or cannot be separated." | Adequate, multi-condition | Multi-label or abstention training; record each visible condition and which is primary | Never a single-target event |
| `insufficient_evidence` | "The evidence is inadequate to decide." | Inadequate (blur, wrong part, missing context, conflicting evidence) | Abstention training; quality diagnosis | Never an event |

### 5.1 Decision order

```
Is the evidence adequate to decide?
  no  → insufficient_evidence
  yes → does the image show more than one supported condition?
          yes → mixed_symptoms (record primary + secondary)
          no  → does it match a supported class?
                  yes → that class
                  no  → unknown
```

Rules:

- `insufficient_evidence` is decided **before** class matching. A blurred image is not
  `unknown`.
- `unknown` requires adequate evidence. It is not a synonym for "I am unsure".
- `mixed_symptoms` is not a licence to avoid a decision; record every visible condition and
  the primary one.
- `healthy` is a positive assertion of absence of visible symptoms, not a fallback.
- None of these classes may be silently dropped. They are retained for abstention training
  and counted in the dataset.

---

## 6. Suspected, expert-confirmed and laboratory-confirmed labels

Three evidence origins are stored separately. They are **not** interchangeable.

| `label_origin` | Who can set it | Evidence required | Usable as a training label | Usable as field evidence |
|---|---|---|---|---|
| `suspected` | Farmer, collector, extension worker | User/collector observation; no expert review | **No** | No — shows suspicion only |
| `expert_confirmed` | **Pathologist** (D13) | Image review note **plus** a field observation or other structured evidence; `confirmed` or `probable` per `04-expert-review.md` §7 | Yes, with its `verification_tier` | Yes, per D7 eligibility |
| `lab_confirmed` | Pathologist recording a laboratory result | A laboratory result reference and the test performed | Yes, strongest tier | Yes, per D7 eligibility |

Rules:

- A `suspected` label is never promoted to `expert_confirmed` without a recorded review.
- `lab_confirmed` requires a real laboratory reference; a plausible-looking result is a
  prohibited fabrication. If no laboratory result exists, the label stays
  `expert_confirmed`.
- The agronomist may advise on crop and severity but **cannot** set or approve a label
  (D13).
- `label_origin` and `verification_tier` are both stored. A label is never inferred from the
  other field.
- A model score, a forecast, or another reviewer's label is never evidence for a label.

### 6.1 Relationship to verification tiers

| `verification_tier` | Typical `label_origin` | Note |
|---|---|---|
| `confirmed` | `expert_confirmed` or `lab_confirmed` | Pathologist role + structured evidence |
| `probable` | `expert_confirmed` | Eligible for forecast features with its tier (D7) |
| `unverified` | `suspected` | Never a training or forecast label |
| `rejected`, `duplicate`, `needs_visit`, `unresolved` | — | Not condition labels; reason recorded |

A `probable` decision may still carry `expert_confirmed` origin. "Probable" is a
verification tier, not a statement that no expert reviewed it.

---

## 7. Crop-specific severity criteria

### 7.1 Principles

- Severity uses **crop-specific visual criteria** agreed with the agronomist.
- A generic percentage scale is **not** used unless validated for that crop and symptom
  (`data-foundation.md` §4.4).
- Severity describes what is visible on the assessed plant/part at the recorded time.
- Severity is not a diagnosis and does not change the class.
- Field severity and adjudicated severity are separate values; the field value is never
  overwritten.

### 7.2 Ordinal framework (draft, pending validation)

| Band | Label | Draft anchor | Not this |
|---|---|---|---|
| `SEV-0` | none / healthy | No visible symptom on the assessed plant/part | Not "unknown" |
| `SEV-1` | first signs | Few early lesions or initial damage, no clear spread | Not a single ambiguous speck |
| `SEV-2` | clear symptoms | Distinct symptoms, limited spread on the assessed part | Not plant-wide |
| `SEV-3` | advanced | Substantial affected tissue or clear spread on the plant | Not dieback |
| `SEV-4` | severe | Necrosis, dieback or plant-level loss | Not a laboratory measure |

These bands are **proposed** and must be validated per crop before the handbook is issued as
v1.1. The numeric boundaries are `TBD — D1`.

### 7.3 Crop-specific anchor table (blocked on D1)

| Field | Requirement | Value |
|---|---|---|
| Crop | One supported crop | `TBD — D1` |
| Assessed unit | Leaf, compound leaf, plant, row | `TBD — D1` |
| Incidence basis | Plants affected / plants assessed | `TBD — D1` |
| Severity basis | Lesion count, % leaf area, or validated scale | `TBD — D1` |
| Band boundaries | Explicit anchors per condition | `TBD — D1` |
| Parts assessed | Which plant parts count | `TBD — D1` |
| Severity applicability | Which classes use severity | `TBD — D1` |
| Validation evidence | Agronomist/pathologist agreement round | `TBD — D1` |

### 7.4 Severity recording rules

- Record severity for the class that is actually labelled; do not record severity for
  `insufficient_evidence`.
- `unknown` and `mixed_symptoms` may carry severity only when the affected tissue can be
  assessed; otherwise `not_assessed`.
- Do not compute severity from the photograph after the fact and overwrite the field value.
- A reviewer may record an **adjudicated** severity with a reason; the field value is kept.
- Severity is never used to infer the class, and class is never used to infer severity.

---

## 8. Provenance and revision history

### 8.1 Label record (append-only)

| Field | Requirement |
|---|---|
| `label_id` | Stable identifier |
| `observation_id` / `image_id` | What is labelled |
| `target_code` | Class, including uncertainty classes |
| `class_kind` | From the class card |
| `label_origin` | `suspected`, `expert_confirmed`, `lab_confirmed` |
| `verification_tier` | `confirmed`, `probable`, `unverified`, … |
| `severity` | Band or `not_assessed` |
| `severity_basis` | Crop-specific scale and version |
| `reviewer_id` | Account reference; personal data, role-gated |
| `reviewed_at` | UTC |
| `evidence_type` | `image_note`, `field_observation`, `lab_result` |
| `evidence_ref` | Link to the evidence |
| `handbook_version` | Handbook used |
| `taxonomy_version` | Taxonomy used |
| `label_status` | `active`, `superseded`, `adjudicated`, `ambiguous` |
| `supersedes_label_id` | Previous label, if a correction |
| `adjudication_id` | Adjudication record, if any |
| `notes` | No PII; no chemical advice |

Rules:

- Labels are append-only. A correction writes a new row and marks the old `superseded`.
- The full history is retained; no label is silently deleted.
- The handbook version and taxonomy version travel with every label.
- Reviewer identity is stored as an account reference and is visible only to authorised
  roles.
- Source and provenance for archive labels follow `../archive/03-archive-provenance.md`.

### 8.2 Handbook revision history

| Version | Date | Change | Reason | Affected classes | Re-labelling required | Approved by |
|---|---|---|---|---|---|---|
| `v1.0-draft` | 2026-11-06 | Framework drafted; crop-specific tables blocked on D1 | Phase 1 §4.4 | All | Not applicable — no labels yet | Not approved |

Revision rules:

1. Every change is versioned and dated.
2. A definition change states which existing labels are affected.
3. If the change alters class meaning, a re-labelling or re-audit is scheduled; in-place
   relabelling is prohibited.
4. A class is never retired without recording what happens to its labels.
5. A revision is approved by the pathologist; severity anchor changes also require the
   agronomist's sign-off.
6. Reviewers are re-trained on any material revision (`03-reviewer-training-and-audit.md`).

---

## 9. Hard negatives and ambiguous images

- Hard negatives and ambiguous images are **retained**, never deleted to tidy the dataset.
- They are labelled with the relevant uncertainty/rejection class and marked for
  abstention training.
- Full definitions, quotas, storage and use rules are in
  `04-abstention-and-hard-negatives.md`.
- They are never counted as positive target examples and never used as forecast negatives.
  "Forecast negative" is a sentinel-panel concept (D7), not an image label.

---

## 10. Boundary and difficult cases

| Case | Required handling |
|---|---|
| Two conditions visible | `mixed_symptoms`; record primary + secondary; do not average severity |
| Symptoms present but cause unclear | `symptom_pattern` class, not a pathogen class |
| Image shows a different crop | `crop_unknown` / rejection; retained as hard negative |
| No plant in image | Rejection reason `not_a_plant`; retained as hard negative |
| Blur / wrong part / missing context | `insufficient_evidence`; retain; consider retake |
| Healthy but odd colour | `healthy` only if no symptom; otherwise `abiotic_look_alike` or `insufficient_evidence` |
| Two reviewers disagree | Adjudication (`02-reviewer-calibration.md`); never majority-vote silently |
| Archive label conflicts with image | Quarantine `label_conflict`; pathologist decides |
| Lab result conflicts with image | Record both tiers and the conflict; do not overwrite the image judgement |

---

## 11. Prohibited practices

- Forcing an image into a positive class to avoid an uncertainty label.
- Using `healthy` as a default for "no supported target visible".
- Treating `unknown`, `mixed_symptoms` or `insufficient_evidence` as errors to be cleaned.
- Copying a model output, forecast or another reviewer's label into a decision.
- Promoting `suspected` to `expert_confirmed` without a review.
- Inventing a laboratory result, reviewer, date, class or severity threshold.
- Using a generic percentage severity scale on an unvalidated crop.
- Overwriting or deleting a label, or editing an original image.
- Deleting hard negatives or ambiguous images.
- Using an archive label as a field label.
- Writing chemical names, doses, mixtures or intervals in reviewer notes.
- Recording a crop-specific class while D1 is unresolved.

---

## 12. Acceptance criteria

- [ ] Every class has a complete class card with `class_kind`, definition, positive
      evidence, boundary cases, look-alikes and example images.
- [ ] The crop-specific taxonomy is filled only after D1 and approved by the pathologist.
- [ ] `unknown`, `mixed_symptoms`, `insufficient_evidence`, `healthy` and
      `abiotic_look_alike` are defined and used according to §5.
- [ ] Every label records `label_origin` and `verification_tier` separately.
- [ ] `suspected` labels are never used for training.
- [ ] Severity uses a validated crop-specific scale, not a generic percentage.
- [ ] Every label records `handbook_version`, `taxonomy_version`, reviewer, date, evidence
      type and full revision lineage.
- [ ] Corrections are append-only and the previous label is retained.
- [ ] Hard negatives and ambiguous images are retained and marked for abstention training.
- [ ] No label is produced by a model or copied from a model output.
- [ ] A revision records affected classes and whether re-labelling is required.
- [ ] The handbook is approved by the pathologist before it is issued to reviewers.
