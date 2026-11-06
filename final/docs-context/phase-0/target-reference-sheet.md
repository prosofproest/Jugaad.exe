# Target reference sheet — tomato, Eastern Dry Zone

**Status:** `[x]` Documented 2026-11-06 — agronomist/pathologist sign-off required.
**Scope:** the D1a allowlist: four target conditions plus `healthy`, `abiotic_lookalike` and
`unknown_other`.
**Owner:** Agronomist / pathologist.
**Use:** labelling handbook, reviewer training, model class definitions and advisory
approval. This sheet describes **what evidence supports a label**; it is not a treatment
guide and contains no chemical content (R5).

> **Rule.** The photograph is evidence, not proof. A reviewer may set `confirmed` only when
> the recorded evidence meets the standard below. If the distinguishing feature is absent or
> the image is ambiguous, the outcome is `unknown_other` or `needs_visit`, never the nearest
> disease.

---

## 1. Severity anchors

Severity is an **expert-review field**, not a model claim (D14). Reviewers record one anchor
per case, with the affected plant part and the assessment method.

| Anchor | Label | Leaf/plant description | Operational meaning |
|---|---|---|---|
| 0 | None | No visible symptoms on the inspected leaves | Healthy or pre-symptomatic; do not call disease |
| 1 | Trace | < 10% leaf area affected; a few lower leaves; no fruit symptoms | Scouting; no escalation unless the target is late blight |
| 2 | Mild | 10–25% leaf area affected; several leaves; plant vigour maintained | Monitor and sanitation; advisory retrieval |
| 3 | Moderate | 26–50% leaf area affected; lower/middle canopy; some defoliation | Escalate if spreading; field visit may be needed |
| 4 | Severe | > 50% leaf area affected or fruit affected; clear defoliation | High-priority review; advisory approver notified |
| 5 | Critical | Plant death, widespread collapse, or entire field affected | Safety/trust escalation; do not rely on a single photo |

Severity is recorded only when the label is `confirmed` or `probable`. It is never inferred
from the model score.

---

## 2. Class definitions

### 2.1 `tomato_late_blight` — tomato late blight

| Field | Description |
|---|---|
| Cause | *Phytophthora infestans* (oomycete) |
| Typical symptoms | Irregular water-soaked, grey-green to brown lesions on leaves; pale green to brown expanding margins; white fuzzy growth on the underside in humid conditions; dark lesions on stems and fruit |
| Distinguishing features | Water-soaked rather than dry concentric lesions; white sporulation on the lower surface; rapid spread across the canopy; cool, humid weather context; lesions often start at leaf tips/margins |
| Look-alikes | Early blight; Septoria leaf spot; bacterial spot/speck; leaf mould; nutrient deficiency; leafminer damage; ozone injury |
| Severity anchors | Anchor 1–2 for a few lesions; 3–4 for expanding canopy lesions; 5 for collapse |
| Evidence to verify | Clear image of the lesion margin and, if possible, the underside; crop stage; cool/humid weather context; rapid progression over 2–3 days; reviewer records the alternative considered. Laboratory isolation is optional, not required for a `confirmed` field label. |
| Forecast eligibility | Yes — after the rules baseline is approved and versioned |

### 2.2 `tomato_early_blight` — tomato early blight

| Field | Description |
|---|---|
| Cause | *Alternaria solani* (fungus) |
| Typical symptoms | Dark brown to black spots with concentric rings ("target board"), often with a yellow halo; usually starts on older lower leaves; lesions may coalesce; stem and fruit lesions possible |
| Distinguishing features | Concentric rings and a yellow halo; dry, papery lesion centre; lower-canopy start; warm, humid but not necessarily cool conditions |
| Look-alikes | Late blight; Septoria leaf spot; target spot; bacterial spot/speck; spider-mite stippling; magnesium deficiency |
| Severity anchors | Anchor 1–2 for a few lower-leaf lesions; 3 for coalescing lesions; 4–5 for extensive defoliation or fruit damage |
| Evidence to verify | Clear image showing the concentric ring pattern and halo; lower-canopy location; no white sporulation; reviewer records whether Septoria or late blight was considered. |
| Forecast eligibility | Yes — after the rules baseline is approved and versioned |

### 2.3 `tomato_septoria_leaf_spot` — tomato Septoria leaf spot

| Field | Description |
|---|---|
| Cause | *Septoria lycopersici* (fungus) |
| Typical symptoms | Small, circular spots with a grey/white centre and a dark margin; tiny dark dots (pycnidia) in the centre with a hand lens; yellowing around spots; lower leaves first |
| Distinguishing features | Small circular spots with pale centres and dark borders; pycnidia visible with magnification; no concentric target rings; splash-dispersed during wet weather |
| Look-alikes | Early blight; late blight; bacterial speck/spot; leaf mould; pesticide or fertilizer burn |
| Severity anchors | Anchor 1–2 for scattered spots; 3 for many coalescing spots; 4–5 for extensive defoliation |
| Evidence to verify | Close image with a scale reference; visible pale centre/dark margin; hand-lens note if pycnidia seen; lower-canopy distribution; reviewer records the alternative considered. |
| Forecast eligibility | Yes — after the rules baseline is approved and versioned |

### 2.4 `tomato_leaf_curl` — tomato leaf curl symptom complex

| Field | Description |
|---|---|
| Cause | Tomato leaf curl virus complex (for example TYLCV/ToLCV), transmitted by whitefly; the label is a **symptom complex**, not a confirmed virus species |
| Typical symptoms | Upward curling or cupping of leaves; yellowing of margins and interveinal areas; stunting; reduced leaf size; thickened or distorted leaves; whitefly presence may be visible |
| Distinguishing features | Upward curling with yellow margins and stunting; whitefly activity; symptoms on new growth; field pattern may follow vector pressure |
| Look-alikes | Physiological leaf roll; herbicide drift (for example 2,4-D-type injury); whitefly/psyllid feeding damage; magnesium deficiency; tomato mosaic virus; cucumber mosaic virus; drought/heat curling |
| Severity anchors | Anchor 1 for a few curled leaves; 2–3 for widespread curling/stunting; 4–5 for severe stunting or plant loss |
| Evidence to verify | Image of new growth and the whole plant; note whether curling is upward or downward; note whitefly presence; ask about herbicide use nearby; record the alternative considered. Laboratory PCR is optional and is recorded as a separate test, not implied by the image label. |
| Forecast eligibility | **No** — no validated weather-driven model in v1; image assessment only |

### 2.5 `healthy` — healthy tomato foliage

| Field | Description |
|---|---|
| Definition | No visible symptom of the allowlisted targets or a named look-alike on the inspected leaves |
| Typical appearance | Uniform green leaves; normal shape and venation; no lesions, curling, stunting or pest signs |
| Look-alikes | Senescent lower leaves; mechanical damage; low-light etiolation; early, invisible infection |
| Severity | Anchor 0 |
| Evidence to verify | Multiple leaves and, where possible, the whole plant; date and growth stage; reviewer records that the crop is in the allowlist and the image is adequate. A single healthy leaf does not prove the field is healthy. |
| Forecast eligibility | Not a forecast target |

### 2.6 `abiotic_lookalike` — abiotic or management look-alike

| Field | Description |
|---|---|
| Definition | Visible symptoms caused by nutrient, water, temperature, salt, herbicide or mechanical factors, with no pathogen sign |
| Typical patterns | Nutrient deficiency: uniform chlorosis, interveinal patterns, older/newer leaf specificity; water stress: wilting, marginal scorch, leaf roll; heat/sunscald: bleached or papery patches; salt injury: marginal burn; herbicide: distortion, strapping, drift pattern; mechanical: tears, abrasion |
| Distinguishing features | A pattern across the field or soil/irrigation history; no sporulation, pycnidia, concentric rings or vector signs; symptoms often uniform on a leaf age class |
| Look-alikes | All four target diseases, especially leaf curl and early blight |
| Severity | Anchor 0–3 usually; record the affected area and the likely abiotic driver as a note, not a disease label |
| Evidence to verify | Whole-plant or field context; soil/irrigation/fertilizer history; recent weather; herbicide use nearby; no pathogen sign; agronomist review for ambiguous cases. |
| Forecast eligibility | Not a forecast target |

### 2.7 `unknown_other` — unknown or other

| Field | Description |
|---|---|
| Definition | The image is usable but the evidence does not meet any allowlisted class, or the condition is outside the allowlist |
| Use when | Symptoms are ambiguous; the crop is not tomato; the target is not on the allowlist; the image is too poor; a look-alike cannot be separated; the reviewer lacks confidence |
| Behaviour | Abstain; show the reason; offer retake or expert review; never force the nearest class (R2) |
| Severity | Not recorded |
| Evidence to verify | Not applicable until a reviewer requests more evidence; the case remains `unresolved` or `needs_visit` |
| Forecast eligibility | Not a forecast target |

---

## 3. Differential diagnosis matrix

| Feature | Late blight | Early blight | Septoria | Leaf curl | Abiotic look-alike |
|---|---|---|---|---|---|
| Lesion colour | Water-soaked grey-green to brown | Dark brown with yellow halo | Pale centre, dark margin | Yellowing, no necrotic spot | Variable, often uniform |
| Lesion shape | Irregular, expanding | Concentric rings | Small circular | Curling/distortion | Marginal or interveinal |
| White growth underneath | Often | No | No | No | No |
| Pycnidia | No | No | Yes (hand lens) | No | No |
| Leaf curling | Sometimes | No | No | Upward cupping | Variable, often downward or marginal |
| Field pattern | Rapid spread, cool/wet | Lower leaves, warm/humid | Splash pattern, wet | Vector/edge pattern | Soil/irrigation/equipment pattern |
| Key discriminator | Water-soaked margin + sporulation | Concentric rings + halo | Pale centre + dark margin | Upward curl + whitefly/stunting | Context + no pathogen sign |

---

## 4. Verification evidence standard

A `confirmed` label requires all of the following in the review record:

- [ ] The crop is tomato and the target is on the D1a allowlist.
- [ ] The image passes the quality gate or the reviewer records why it is still usable.
- [ ] The distinguishing feature in §2 is visible or supported by a field observation.
- [ ] At least one named look-alike was considered and excluded, with a reason.
- [ ] The reviewer records crop stage, affected plant part and severity anchor.
- [ ] The reviewer identity, timestamp, model version (if any) and evidence note are stored.
- [ ] A second opinion is recorded for P0 cases, late blight, or any case that changes a
      previous label.

**Not sufficient:** a model score, a single leaf photo with no context, a farmer's verbal
guess, or "it looks like the picture".

---

## 5. Photo capture requirements for label quality

- Whole leaf and close-up of the lesion margin; underside if late blight is suspected.
- Upper, middle and lower canopy where possible.
- Include a scale reference (hand, coin, ruler) without capturing faces or documents.
- Daylight or even lighting; avoid deep shadow, flash glare and motion blur.
- Record crop stage, variety if known, planting date, recent weather and recent field
  operations.
- Do not upload images of people, identity documents or unrelated personal information.

---

## 6. Advisory status

Approved, versioned, non-chemical advisory content must exist for a target before it is
served. The content covers scouting, monitoring, sanitation, airflow, irrigation management,
removal of severely affected material, and escalation to an extension worker. It does **not**
name or recommend any chemical, dose, mixture, interval or pre-harvest interval (R5).

At the time of this sheet, advisory content is **not approved**. That is a Gate 3/4
dependency, not a reason to relax the target definition.

---

## 7. Sign-off and revision

| Role | Name | Decision | Date |
|---|---|---|---|
| Agronomist / pathologist | TBD at workshop | Pending | — |
| `can_confirm` holder | TBD at MoU | Pending | — |
| Advisory approver | TBD at MoU | Pending | — |

Revision history is append-only. A change to a class definition, severity anchor or
verification standard requires a new version, reviewer retraining, and a pre-registration
amendment if the pilot has started.
