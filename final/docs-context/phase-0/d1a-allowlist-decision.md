# D1a — First validated crop/target allowlist

**Decision ID:** D1a
**Status:** `[x]` Recorded 2026-11-06 — agronomist sign-off required at the Gate 0 workshop.
**Owner:** Agronomist / pathologist, with the ML lead.
**Needs by:** Gate 0 for the release scope; Gate 3 for a served image model.
**Parent decision:** D1 — open crop catalogue with a validated-target allowlist
([ADR-011](../adr/0011-open-crop-catalogue.md)).
**Changes:** `progress-tracker.md` §4, `phase-0-decisions.md` §3, `crop-calendar.md`,
`target-reference-sheet.md`, `pilot-protocol-v1.md`, `data-acquisition-plan.md`.

> **What this decision does and does not mean.** It fixes the first `crop × target` set the
> project will collect, label and assess. It does not claim the set is agronomically
> complete, that the image model will meet any performance floor, or that the weather model
> is validated. Those are later gates. The scores below are **provisional workshop inputs**,
> not measured field evidence.

---

## 1. Decision

**Crop:** tomato (*Solanum lycopersicum* L.).
**Zone:** Karnataka Eastern Dry Zone (agro-climatic Zone 5).
**Pilot district cluster:** Kolar, Chikkaballapura and Bengaluru Rural districts; the final
taluks/hoblis are confirmed against the licensed boundary layer (DS-007) and recorded in
[`pilot-sites.csv`](pilot-sites.csv).

**Allowlist (4 target conditions + 3 residual classes):**

| Class ID | Display name | Kind | Assessment eligible | Forecast eligible at v1 |
|---|---|---|---|---|
| `tomato_late_blight` | Tomato late blight | Pathogen: *Phytophthora infestans* | Yes | Yes, after the rules baseline is approved |
| `tomato_early_blight` | Tomato early blight | Pathogen: *Alternaria solani* | Yes | Yes, after the rules baseline is approved |
| `tomato_septoria_leaf_spot` | Tomato Septoria leaf spot | Pathogen: *Septoria lycopersici* | Yes | Yes, after the rules baseline is approved |
| `tomato_leaf_curl` | Tomato leaf curl symptom complex | Virus complex (TYLCV/ToLCV), whitefly-transmitted | Yes | No — no validated weather-driven model in v1 |
| `healthy` | Healthy tomato foliage | Reference class | Yes | Not a forecast target |
| `abiotic_lookalike` | Abiotic or management look-alike | Nutrient, water, heat, salt, herbicide or mechanical injury | Yes | Not a forecast target |
| `unknown_other` | Unknown / other | Insufficient evidence or a condition outside the allowlist | Yes (abstain) | Not a forecast target |

The residual classes are mandatory. A model may not collapse `abiotic_lookalike` or
`unknown_other` into the nearest disease class (R2). `unsupported_crop` and
`unsupported_target` remain API states outside this class list.

---

## 2. Why tomato and this zone

### 2.1 Candidate scoring

Criteria and weights were agreed for the decision workshop. Scores are 0–5 and are
**provisional expert judgements**, not measured statistics. They are recorded so the choice
can be challenged and revised, not presented as evidence.

| Criterion | Weight | Tomato | Potato | Rice | Maize |
|---|---:|---:|---:|---:|---:|
| Economic importance to smallholders | 25% | 5 | 4 | 5 | 4 |
| Existing extension / plant-clinic presence | 20% | 4 | 4 | 4 | 3 |
| Visual distinctness and class separability | 15% | 3 | 4 | 1 | 3 |
| Approved non-chemical advisory content available | 15% | 4 | 4 | 4 | 3 |
| Validated weather-driven risk model exists | 10% | 4 | 5 | 3 | 2 |
| Breadth of distinct photographable targets (3–5) | 15% | 5 | 1 | 4 | 2 |
| **Weighted total** | **100%** | **4.25** | **3.65** | **3.70** | **3.00** |

Tomato wins on breadth and on the combination of a validated late-blight model with three
additional photographable conditions. Potato scores highest on the single best-validated
model but cannot supply 3–5 distinct leaf-level conditions without stretching the class
definitions. Rice is a strong future expansion candidate once image separability is
demonstrated.

### 2.2 Zone rationale

- Tomato is grown across the Eastern Dry Zone in Kharif, Rabi and summer windows, giving
  more than one observation window per year.
- The zone has an established extension and Krishi Vigyan Kendra presence and is close to
  Bengaluru plant-health expertise for escalation.
- Kannada is the working language, matching D13.
- The Rabi window (November–February) provides a cool, humid epidemic window suitable for a
  late-blight/early-blight/Septoria nowcast.
- The zone boundary and district cluster are small enough for a six-site pilot with two
  `can_confirm` holders per area (D3b).

**Assumption to verify:** the final district/taluk list must match the notified agro-climatic
zone map, not a convenience sample. The agronomist records the source and version at
sign-off.

---

## 3. Differential look-alikes (named)

The class list is only usable if reviewers can separate these conditions. The target
reference sheet carries the full descriptions; this table fixes the named differentials.

| Target | Must be distinguished from |
|---|---|
| Late blight | Early blight; Septoria leaf spot; bacterial spot/speck; leaf mould; nutrient deficiency; leafminer damage; ozone injury |
| Early blight | Late blight; Septoria leaf spot; target spot (*Corynespora cassiicola*); bacterial spot/speck; spider-mite stippling; magnesium deficiency |
| Septoria leaf spot | Early blight; late blight; bacterial speck/spot; leaf mould; pesticide or fertilizer burn |
| Tomato leaf curl | Physiological leaf roll; herbicide drift (for example 2,4-D-type injury); whitefly/psyllid feeding damage; magnesium deficiency; tomato mosaic virus; cucumber mosaic virus; drought/heat curling |
| Healthy | Senescent lower leaves; mechanical damage; low-light etiolation |
| Abiotic look-alike | Any of the above diseases when no pathogen sign is present; pattern across the field, soil, irrigation or weather history is the discriminator |

**Rule:** if the reviewer cannot name the distinguishing feature, the case is
`unknown_other`, not the closest disease.

---

## 4. Release conditions for this allowlist

This allowlist is recorded, but a target may not be **served** until all of the following are
true for that target:

- [ ] The agronomist has signed the target reference sheet and severity anchors.
- [ ] Approved, versioned, non-chemical advisory content exists for the target (D6).
- [ ] The field test set has been frozen before model selection (Gate 1).
- [ ] The abstention rule and floors are pre-registered before the frozen test set is opened
      (D8, Gate 3).
- [ ] Per-class recall, calibration and abstention are reported at the shipped threshold.
- [ ] The model registry entry is approved and version-pinned.
- [ ] The forecast rules baseline is approved for the target, or the target is marked
      `forecast_eligible: false`.

`tomato_leaf_curl` is image-assessment eligible but **not** forecast eligible in v1. The UI
must not imply a weather-driven leaf-curl outlook.

---

## 5. Consequences

| Option | Consequence |
|---|---|
| **Tomato allowlist (chosen)** | Four distinct conditions; strong public pretraining data; one validated weather model (late blight) carries the forecast track; leaf curl remains image-only |
| Potato late blight only | Strongest single forecast model, but fails the 3–5-condition scope and gives a thin image triage product |
| Rice blast / BLB / brown spot | Large farmer base, but visual separability is weaker and the pilot would need a different zone and advisory set |
| Open catalogue without an allowlist | Rejected: it would force unsupported claims and violate R2/R6 |

**Risks created:** look-alike confusion (R-11), advisory gaps for leaf curl (R-05), and
over-narrow geography (R-10). Mitigations are in the target sheet, the labelling handbook and
the pilot protocol.

---

## 6. Change control

Any change to the crop, zone, class list or target eligibility is a scope decision. It must
be recorded in [`../progress-tracker.md`](../progress-tracker.md) §4 as a new dated decision,
the pre-registration manifest must be regenerated, and the validator re-run. No change may be
made silently after the first pilot observation.

**Sign-off**

| Role | Name | Decision | Date |
|---|---|---|---|
| Agronomist / pathologist | TBD at workshop | Pending | — |
| ML lead | TBD at workshop | Pending | — |
| Product lead | TBD at workshop | Pending | — |
