# Sampling matrix

**Matrix version:** `v1.0-draft`
**Status:** Draft — dimension strata partly blocked on D1/D2. **No cells have been filled.**
**Owner:** Data engineer (TBD) + Agronomist (TBD) + Field operations lead (TBD)
**Last updated:** 2026-11-06
**Authorities:** `final/docs-context/data-foundation.md` §3.1, §3.4, §6;
`final/docs-context/phase-plan.md` §4.2, §4.8;
`final/feature-specs/05-data-layer.md` §4.3.

> **Purpose:** make representativeness a tracked structure, not a hope. A total image count
> says nothing about whether the dataset covers the districts, seasons, devices and
> conditions where the model will run.
>
> **Rule:** progress is reported as **coverage of required cells**, never as a single total.
> A batch of 10,000 images from one district on one phone can leave the matrix almost empty.

---

## 1. Why a matrix

Two failure modes dominate this project:

1. **Domain shift** — the model is trained on clean, well-lit, high-end-phone images and
   fails on farmer submissions.
2. **Reporting bias** — some areas and conditions are over-represented, so the model performs
   unevenly and the evaluation hides it in an aggregate number.

The matrix forces deliberate collection of the hard, rare and ambiguous material:
healthy controls, abiotic look-alikes, early symptoms, poor lighting, low-end devices and
images that the quality gate rejects.

---

## 2. Dimensions and strata

Each dimension is a set of strata. A **cell** is one combination of strata that the programme
requires. Not every combination is required; §4 defines the tiers.

| Dimension | Code prefix | Strata | Status |
|---|---|---|---|
| District / agro-climatic zone | `D` | `D1..Dn` — pilot districts | `TBD — D1` |
| Season | `S` | `S-KHARIF`, `S-RABI`, `S-SUMMER`, `S-PERENNIAL`, `S-OFF` | `TBD — D1` |
| Crop | `C` | Supported crop list | `TBD — D1` |
| Variety | `V` | Crop-specific varieties | `TBD — D1` |
| Plant age / growth stage | `G` | `G-SEEDLING`, `G-VEG`, `G-FLOWER`, `G-FRUIT`, `G-MATURE`, `G-SENESCENT` | `TBD — D1` crop calendar |
| Lighting | `L` | `L-SUN`, `L-SHADE`, `L-OVERCAST`, `L-INDOOR`, `L-MIXED`, `L-FLASH` | Defined; `L-FLASH` discouraged |
| Background | `B` | `B-SOIL`, `B-MULCH`, `B-CROP`, `B-HAND`, `B-STRUCTURE`, `B-MIXED`, `B-PLAIN` | Defined |
| Severity | `SEV` | `SEV-0` none, `SEV-1` first signs, `SEV-2` clear, `SEV-3` advanced, `SEV-4` severe | `TBD — D1` scale |
| Device | `DEV` | `DEV-LOW`, `DEV-MID`, `DEV-HIGH` | Bands `TBD` — device trial |
| Condition class | `T` | Target classes + `T-HEALTHY`, `T-ABIOTIC`, `T-PEST`, `T-UNKNOWN`, `T-MIXED` | `TBD — D1` target list |
| Capture context | `CTX` | `CTX-ENUM` (enumerator), `CTX-FARMER` (self-capture) | Defined |
| Distance / framing | `FR` | `FR-CLOSE`, `FR-MID`, `FR-CONTEXT` | Defined in capture protocol |

**Archive data does not fill field cells.** `CTX-ARCHIVE` is tracked in the dataset register
as a separate source (`DS-002`) and is never counted as field coverage.

---

## 3. Required special strata

These are not optional extras. They are the material that teaches the system to be honest.

| Stratum | Code | Definition | Why it is required |
|---|---|---|---|
| Healthy controls | `T-HEALTHY` | Confirmed healthy plants, same crops, areas, seasons and devices as cases | Without them, every symptom is a positive and the model cannot learn "healthy" |
| Abiotic look-alikes | `T-ABIOTIC` | Nutrient deficiency, water stress, heat stress, injury or other non-pest causes that resemble a target | Prevents every yellow leaf being classified as disease |
| Pest damage | `T-PEST` | Chewing, boring, mining or other pest signs | Separate from pathogen classes; do not collapse into one label |
| Ambiguous cases | `T-MIXED`, `T-UNKNOWN` | Mixed symptoms, insufficient evidence, or a genuinely unclear case | Abstention training data; not noise to discard |
| Hard negatives | `T-HARDNEG` | Visually similar but different condition, healthy plant that looks diseased, wrong crop, non-plant image | Teaches the model what *not* to fire on |
| Rejected images | `Q-REJECT` | Images rejected by the capture self-check or the quality gate | Quality-gate training; measured, retained, never silently dropped |
| Early symptoms | `SEV-1` | First visible signs | The highest-value and most often missed stratum |
| Low-end devices | `DEV-LOW` | Cheapest supported Android | The realistic farmer device |
| Poor lighting | `L-SHADE`, `L-INDOOR`, `L-MIXED` | Non-ideal but real conditions | Domain coverage; do not curate them away |

**Hard negatives are not "negatives" in the disease sense.** They are deliberate near-misses
that must be retained and labelled. They are never deleted to improve apparent accuracy.

---

## 4. Matrix tiers

A full cross-product of every dimension is infeasible and statistically wasteful. Cells are
tiered by what the project must be able to claim.

| Tier | Definition | Requirement |
|---|---|---|
| **A — must hit** | Condition class × severity band × district × season, for every supported crop | Every Tier A cell must reach `n_min` |
| **B — coverage quota** | Lighting × background × device, within each crop | Each stratum must reach its quota; individual combinations are best effort |
| **C — best effort** | Variety × plant age | Reported, not gated; gaps recorded as limitations |
| **D — quality** | Rejected images, hard negatives, ambiguous cases | Quotas per crop; tracked separately from `T-` classes |

### 4.1 Tier A cells

For each supported crop, the required shape is:

```
C-<crop> × T-<condition> × SEV-<0..4> × D-<district> × S-<season>
```

Not every condition occurs in every district or season. A cell that is **biologically
impossible** is marked `not_applicable` with a reason; it is not silently omitted and it is
not counted as met.

### 4.2 Tier B quotas

Within each crop:

- every lighting stratum that occurs in the pilot area has a quota;
- every background stratum that occurs in farmer submissions has a quota;
- `DEV-LOW`, `DEV-MID`, `DEV-HIGH` each have a quota;
- `CTX-FARMER` has a quota separate from `CTX-ENUM`, because self-capture is the deployment
  condition.

### 4.3 Tier D quotas

Per crop, at minimum:

- healthy controls: quota `TBD`;
- abiotic look-alikes: quota `TBD`;
- ambiguous / mixed / unknown: quota `TBD`;
- hard negatives: quota `TBD`;
- rejected images: tracked, no minimum — but the reject rate must be measured.

**All quotas (`n_min`) are `TBD`.** They depend on D1 (crop/target/zone), the target class
count and the frozen test-set design. They must be set **before** collection starts and must
not be revised downward after seeing results.

---

## 5. Cell status vocabulary

| Status | Definition |
|---|---|
| `not_started` | No accepted case |
| `unmet` | Below `n_min` |
| `partial` | At least half of `n_min`, still below `n_min` (proposed default) |
| `met` | At or above `n_min` |
| `exceeded` | Above `n_min`; stop collecting unless it is a rare stratum |
| `not_applicable` | Biologically or operationally impossible; reason recorded |
| `blocked` | Cannot be collected (access, season, permission); owner and review date recorded |

`partial` thresholds are proposed operational defaults and must be confirmed before the
pilot. They are not scientific claims.

---

## 6. Matrix record

The matrix is stored as data, not only as a document. Until the platform exists, it is a
versioned table with the same fields; it is marked **provisional**.

| Field | Type | Requirement |
|---|---|---|
| `matrix_version` | text | `v1.0-draft`, then released version |
| `cell_id` | text | Deterministic from the strata codes |
| `crop_code` | text | `TBD — D1` |
| `condition_code` | text | `T-*` |
| `severity_code` | text | `SEV-*` |
| `district_code` | text | `D-*` |
| `season_code` | text | `S-*` |
| `variety_code` | text | `V-*` or `any` |
| `stage_code` | text | `G-*` or `any` |
| `lighting_code` | text | `L-*` or `any` |
| `background_code` | text | `B-*` or `any` |
| `device_code` | text | `DEV-*` or `any` |
| `context_code` | text | `CTX-*` |
| `tier` | text | `A`, `B`, `C`, `D` |
| `n_min` | integer | `TBD` until set; never zero for a required cell |
| `n_accepted` | integer | Count of accepted cases matching the cell |
| `n_quarantined` | integer | Excluded from `n_accepted` |
| `status` | text | §5 vocabulary |
| `owner` | text | Role responsible for filling the gap |
| `review_date` | date | Next review |
| `note` | text | Reason for `not_applicable` or `blocked`; no PII |

**Matching rule:** a case fills a cell only if all named strata match. `any` means the
dimension is not constrained for that cell. A case may fill more than one cell (for example
a Tier A cell and a Tier B lighting quota), but it counts **once** for case totals.

---

## 7. Template (illustrative, not data)

The rows below show the shape only. Every value is a placeholder; none is a real district,
crop, target or quota.

| cell_id | tier | condition | severity | district | season | lighting | device | n_min | n_accepted | status |
|---|---|---|---|---|---|---|---|---|---|---|
| `C-x_T-x_SEV-1_D-x_S-x` | A | `T-x` | `SEV-1` | `D-x` | `S-x` | `any` | `any` | `TBD` | 0 | `not_started` |
| `C-x_T-HEALTHY_SEV-0_D-x_S-x` | A | `T-HEALTHY` | `SEV-0` | `D-x` | `S-x` | `any` | `any` | `TBD` | 0 | `not_started` |
| `C-x_T-ABIOTIC_any_D-x_any` | D | `T-ABIOTIC` | `any` | `D-x` | `any` | `any` | `any` | `TBD` | 0 | `not_started` |
| `C-x_any_any_any_any_L-SHADE_any` | B | `any` | `any` | `any` | `any` | `L-SHADE` | `any` | `TBD` | 0 | `not_started` |
| `C-x_any_any_any_any_any_DEV-LOW` | B | `any` | `any` | `any` | `any` | `any` | `DEV-LOW` | `TBD` | 0 | `not_started` |
| `C-x_T-HARDNEG_any_any_any_any_any` | D | `T-HARDNEG` | `any` | `any` | `any` | `any` | `any` | `TBD` | 0 | `not_started` |

---

## 8. Setting `n_min`

`n_min` is derived, not guessed. The inputs are:

1. the number of supported target classes (D1);
2. the minimum per-class sample needed for a credible test set at the chosen reporting
   granularity;
3. the expected class imbalance;
4. the number of required cells each case can fill;
5. the frozen test-set size and the geographic holdout (`phase-plan.md` §4.8).

Rules:

- Set `n_min` before the first collection batch.
- Record the derivation and the owner.
- Never lower `n_min` after seeing results to make a cell look met. If the target was
  unrealistic, version the matrix and record why.
- A cell that cannot be filled is recorded as `blocked` or `not_applicable` with a reason,
  not quietly dropped.
- Rare but important strata (early symptoms, abiotic look-alikes, hard negatives) get a floor,
  not a proportional share.

---

## 9. Balancing rules

- No single district, device, background or lighting stratum may dominate the accepted
  dataset beyond a recorded cap (`TBD`).
- `CTX-FARMER` must not be a token sample; it is the deployment condition.
- Healthy controls must come from the same districts, seasons and devices as the disease
  cases. A healthy set from one clean field is not a control.
- Early severity must not be swamped by advanced severity; advanced damage is easier to
  photograph and easier to label.
- Rejected images are reported alongside accepted images, not hidden from the denominator.

---

## 10. Gap handling

When a cell is `unmet`, `blocked` or `not_applicable` at a review:

| Situation | Action | Recorded as |
|---|---|---|
| Season not yet reached | Schedule the collection window | `not_started` with a date |
| District inaccessible | Reallocate to a comparable district or record the limitation | `blocked` + reason |
| Condition absent in the pilot area | Use archive data where permitted, or record the coverage limitation | `not_applicable` or `blocked` |
| Device class unavailable | Procure a device or record the limitation | `blocked` + owner |
| Condition too rare to reach `n_min` | Lower the claim, not the standard; record the shortfall | `unmet` + limitation |
| Matrix target unrealistic | Version the matrix with a documented reason | New `matrix_version` |

**A gap is never filled with a fabricated, duplicate, borrowed or archive image presented as
field data.**

---

## 11. Relationship to splits and evaluation

- Splits group by farm, field, collection event or plant (`phase-plan.md` §4.8). The matrix
  does not override the grouping rule.
- A geographic holdout consumes cells; it must be chosen deliberately, not discovered after
  collection.
- Per-class and per-region reporting follows the matrix: a cell with too few samples is
  reported as insufficient, not merged into an aggregate that hides it.
- The frozen test set is drawn from the same matrix, before model selection.

---

## 12. Change control

- The matrix is versioned. Changes are additive or documented; historical coverage is not
  rewritten.
- Adding a stratum does not retroactively mark old cells as met.
- Removing a stratum requires a recorded reason and an owner.
- Every change records date, owner, reason and affected cells.

| Version | Date | Change | Owner |
|---|---|---|---|
| `v1.0-draft` | 2026-11-06 | Initial dimensions and tiers; all strata and quotas pending D1 | Draft — data engineer (TBD) |

---

## 13. Acceptance criteria

- [ ] Every supported crop has Tier A cells defined.
- [ ] Every required cell has an `n_min` set before collection.
- [ ] Healthy controls, abiotic look-alikes, ambiguous cases, hard negatives and rejected
      images each have a tracked stratum.
- [ ] Archive images cannot satisfy a field cell.
- [ ] A case fills a cell only when all constrained strata match.
- [ ] `not_applicable` and `blocked` cells have a reason and an owner.
- [ ] `n_min` is never lowered after results are seen without a versioned rationale.
- [ ] The matrix can be queried per district, season, crop, condition, severity, lighting,
      background and device.
- [ ] Coverage is reported as cell status, not only as a total count.
- [ ] Geographic holdout cells are recorded before collection.
