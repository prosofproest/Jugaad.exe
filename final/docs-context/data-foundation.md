# Data foundation

**Covers:** blueprint Chapters 18–24 — data strategy, image dataset collection, labelling,
cleaning/preprocessing, splitting and leakage prevention, weather/environmental data, and
historical/regional observations.
**Status:** design baseline. Every dataset requires documented permission before use.
**Last updated:** 2026-11-06

---

## 1. Why this document exists

Both AI tracks are only as trustworthy as the data under them. The image model learns from
field photographs; the forecast model learns from weather, crop context and **verified**
regional observations. Neither can be rescued later by a better architecture.

Two failure modes dominate:

1. **Domain shift** — a model trained on clean laboratory leaves fails on farmer photos.
2. **Reporting bias** — "no report" is mistaken for "no disease".

This document states how data is collected, labelled, cleaned, split and governed so that
those failures are prevented structurally, not caught after deployment.

---

## 2. Data strategy (Chapter 18)

### 2.1 Data families

| Family | Examples | Primary use |
|---|---|---|
| Field images + quality labels | Farmer photos, extension photos, clinic archives | Image triage, quality gate |
| Crop and crop-cycle context | Crop, variety, growth stage, planting date, irrigation | Both tracks |
| Weather observations and forecasts | Rainfall, temperature, humidity, wind, leaf-wetness proxy | Area outlook |
| Historical occurrence records | Extension records, plant clinics, field surveys | Forecast features, baselines |
| Farmer and extension observations | Submitted reports, verification outcomes | Verification layer, surveillance |
| Geographic boundaries | Versioned administrative units and codes | Aggregation, maps, privacy |
| Expert advisories and follow-up | Approved non-chemical guidance, field outcomes | Advisory layer, evaluation |

### 2.2 Data quality dimensions

Every dataset is assessed on: **completeness, accuracy, timeliness, consistency,
representativeness, provenance and permission**. A dataset that is complete but lacks
provenance is not usable.

### 2.3 Governance

Each dataset has a named owner, permitted use, update schedule, retention rule and quality
checks. Any dataset used for training or evaluation must carry a written permission record
before it enters the pipeline. No exceptions for "just a baseline".

### 2.4 Data dictionary

A data dictionary exists before complex modelling. It states, per field: name, type, unit,
allowed range, source, nullability, and whether the value is an observation, a derivation
or an adjudicated label.

**Implementation points**

- Create the data dictionary in Phase 1, before the first model.
- Track missingness and source reliability explicitly; never fill a gap silently.
- Quarantine suspicious records rather than deleting them.

---

## 3. Image dataset collection (Chapter 19)

### 3.1 Representativeness

The dataset must represent the environment in which it will be used. A dataset of clean,
centred leaves on plain backgrounds will not represent farmer submissions.

Collect across, at minimum:

- devices (low-cost Android and mid-range);
- districts and seasons;
- crop varieties and plant ages;
- lighting (bright sun, shade, overcast, indoor);
- backgrounds (soil, mulch, other crops, hands);
- capture distance and framing;
- symptom severity, from first signs to advanced damage.

### 3.2 Metadata per image

Crop, plant part, date, approximate location, growth stage, image source, capture device
class, quality flags and verification status where known. Metadata is data, not an
afterthought: the split, the evaluation and the audit all depend on it.

### 3.3 Ethical collection

- Explain why images are collected and obtain consent.
- Avoid identifiable people, faces, documents or unrelated personal information.
- Strip EXIF GPS unless exact location is explicitly consented and needed.
- Never publish raw farmer images without permission.

### 3.4 Sampling strategy

Include healthy controls, common target conditions, pest damage and abiotic look-alikes.
Deliberately seek examples from under-represented conditions. Keep **hard negatives** and
**ambiguous images** — they are what teach the system to abstain.

### 3.5 Capture protocol

A standard capture protocol is issued to field collectors and extension workers:

- two or three leaves per plant, plus a whole-plant context shot;
- fill the frame with the affected area, hold steady, use daylight;
- avoid flash glare and deep shadow;
- record stage and symptom spread before photographing;
- never substitute a stock or borrowed image.

**Implementation points**

- Retain originals securely; store processed derivatives separately and regenerably.
- Log the protocol version with each collection batch.

---

## 4. Image labelling protocol (Chapter 20)

### 4.1 Taxonomy

Labels are crop-specific. Each class states whether it refers to pathogen identity, a
visible symptom pattern, or pest damage. A label of "late blight" means "consistent with
late blight", not "laboratory-confirmed late blight".

Minimum class set per supported crop:

- supported target conditions;
- `healthy`;
- `abiotic_look_alike` (nutrient, water, heat, chemical injury);
- `unknown` / `insufficient_evidence`.

### 4.2 Review process

- A labelling handbook defines each class with example images and boundary cases.
- A qualified reviewer labels a representative subset independently.
- Disagreements are adjudicated by a second qualified reviewer.
- Inter-reviewer agreement is measured and reported; unclear definitions are revised.

### 4.3 Uncertainty

Allow `unknown`, `mixed_symptoms` and `insufficient_evidence`. Do not force every image
into a positive class. Abstention labels are required data, not noise.

### 4.4 Severity

Severity uses crop-specific visual criteria agreed with an agronomist. A generic
percentage scale is not used unless it has been validated for that crop and symptom.

### 4.5 Provenance

Store reviewer, date, evidence type, label confidence, and full revision history. A label
is never overwritten without an audit record.

**Implementation points**

- Separate suspected reports from expert-confirmed and laboratory-confirmed labels.
- A model output is never used as a label.
- Measure agreement before scaling annotation.

---

## 5. Cleaning and preprocessing (Chapter 21)

Cleaning preserves traceability. Nothing is discarded silently and no label changes
without a recorded reason.

### 5.1 Image checks

File type, dimensions, corruption, duplicates (content hash and perceptual hash), blur,
exposure, orientation and plant presence. Failed checks route to quarantine, not deletion.

### 5.2 Tabular checks

Units, date ranges, crop names, geographic codes, impossible values (negative rainfall,
stage after harvest), duplicate reports and inconsistent timestamps.

### 5.3 Missing values

Distinguish **unknown** from **zero**. Apply imputation only where justified, and store an
imputation flag plus the method. Weather gaps are never imputed for a scored area outlook;
they force `insufficient_data`.

### 5.4 Normalisation

Standardise units, time zones (UTC in storage), crop taxonomy and administrative
identifiers. Keep the original value alongside the normalised value where interpretation
matters.

### 5.5 Versioning

Store raw, cleaned and model-ready dataset versions with reproducible transformation code.
A model records the dataset version it was trained on.

**Implementation points**

- Every ingestion batch produces an automated data-quality report.
- Keep a quarantine path for suspicious records with an owner and a resolution.

---

## 6. Splitting and leakage prevention (Chapter 22)

### 6.1 Image splits

Group by **farm, field, collection event or plant** so images from one source never cross
training and test partitions. Random image-level splits overstate performance when
near-duplicates exist.

### 6.2 Forecast splits

Use chronological training and testing. Every feature must be available at the forecast
`issue_time`. Never compute a historical forecast from today's data or today's boundary
version.

### 6.3 Geographic holdout

Where feasible, hold out one or more locations to test spatial transfer. Report the result
per region, not only in aggregate.

### 6.4 Frozen test set

Freeze an untouched field test set before model selection and threshold tuning. The test
set is opened once, at the shipped abstention threshold.

### 6.5 Reporting

Publish per-class and per-region metrics, sample counts and uncertainty intervals where
feasible. A single aggregate number is not an evaluation.

**Implementation points**

- Document every split seed, grouping rule and holdout list.
- Public datasets are for pretraining and benchmarking only; they are never the field
  validation set.

---

## 7. Weather and environmental data (Chapter 23)

### 7.1 Candidate variables

Temperature (min/max/mean), relative humidity, rainfall, consecutive wet days, wind and a
leaf-wetness proxy where a defensible source exists.

### 7.2 Spatial matching

Associate a forecast grid cell or station with the selected administrative area and record
the matching method and distance. Document known microclimate limitations of a coarse grid.

### 7.3 Temporal aggregation

Generate lagged windows and rolling summaries that exist at `issue_time`. Store the window
definition, the aggregation function and the source timestamps.

### 7.4 Missing and stale data

Flag missing observations, provider outage and stale forecasts. Never substitute a default
value silently. Stale weather produces `insufficient_data`, never a lowered band.

### 7.5 Provider governance

Document licence, update frequency, historical depth, spatial resolution, quality notes
and service limits. Store `source_timestamp` and `fetched_at` for every ingest.

**Implementation points**

- Validate candidate weather features with local agronomic expertise before use.
- Record the provider version and grid resolution with every feature snapshot.

---

## 8. Historical records and regional observations (Chapter 24)

### 8.1 Sources

Extension records, plant clinics, field surveys, farmer submissions and approved
institutional datasets. Each source carries a permission record and a reliability note.

### 8.2 Verification tiers

Store `confirmed`, `probable`, `unverified` and `rejected` separately. Forecast features use
verified records only; `unverified` is never promoted by a model.

### 8.3 Spatio-temporal features

Lagged verified counts, distance-weighted nearby verified reports and previous-season
occurrence. Distance and time decay are documented and biologically justified; otherwise
they are not used.

### 8.4 Bias correction

Include surveillance intensity or reporting coverage as a feature or an explicit
uncertainty indicator. An unobserved area is not a negative observation.

### 8.5 Deduplication

Merge duplicate reports only through a review decision (`duplicate`), retaining source
links and the full audit history. Never merge counts by heuristic alone.

**Implementation points**

- Never treat no report as a confirmed disease-free observation.
- Preserve the distinction between **event date** and **report date**.
- Keep the boundary version used at the time of each historical record.

---

## 9. Traceability to code and specs

| Concern | Spec / code |
|---|---|
| Tables, constraints, storage | `../feature-specs/05-data-layer.md` |
| Upload and quality flow | `../feature-specs/02-reporting-and-capture.md` |
| Verification states | `../feature-specs/04-expert-review.md` |
| Forecast inputs and snapshots | `../feature-specs/06-forecast-and-risk-map.md` |
| Model training and evaluation | `./ml-models.md` |
| Honesty rules for datasets | `./ai-workflow-rules.md` §4 |

## 10. Acceptance criteria for the data foundation

- [ ] A data dictionary exists for every field used in training or forecasting.
- [ ] Every dataset has an owner, permission record, retention rule and quality check.
- [ ] Image splits are grouped by farm/field/event and documented.
- [ ] Forecast splits are chronological and leakage-tested.
- [ ] A field test set is frozen before model selection.
- [ ] Weather gaps produce `insufficient_data`, not imputed values.
- [ ] Unverified reports are excluded from forecast features (tested).
- [ ] Hard negatives and ambiguous images are retained for abstention training.
