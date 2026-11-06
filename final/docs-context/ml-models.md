# ML models

**Covers:** blueprint Chapters 27–38 — image problem formulation, architectures,
preprocessing, training, evaluation, confidence/explainability, forecast task definition,
feature engineering, baselines, calibration, spatial/temporal forecasting, and combining
the two outputs.
**Status:** design baseline. Every threshold below is an illustrative design example until
locally validated.
**Last updated:** 2026-11-06

---

## 1. Image diagnosis — problem formulation (Chapter 27)

Formulate the image task as **cautious visual triage**, not diagnosis.

| Element | Definition |
|---|---|
| Input | A field photograph plus optional crop and plant-part context |
| Output | Candidate class scores, quality flags, confidence band, abstention state, model version |
| Class set | Supported conditions + healthy + abiotic look-alike + unknown |
| Abstention | Return no assessment when quality is poor, crop is unsupported, or input is outside the validated domain |
| Escalation | Offer expert review for ambiguous, severe or high-impact reports |

The model estimates similarity to supported visual classes. It does not establish pathogen
identity in every case. Write the user-facing wording (Appendix B) before choosing an
architecture.

**Prohibitions**

- Never map an unknown input onto the nearest supported class.
- Never present a ranked class as a confirmed diagnosis.
- Never display an unvalidated percentage confidence.

---

## 2. Architectures (Chapter 28)

| Approach | When to use | Notes |
|---|---|---|
| Transfer learning (MobileNet / EfficientNet) | Default baseline | Lightweight, cheap to serve and quantise |
| Larger classifiers (ResNet, ConvNeXt, ViT) | Only with sufficient field data (e.g. > 5k images per crop) | Compare fairly against the baseline |
| Embedding + few-shot head (CLIP/DINOv2) | Rare classes and fast class expansion | Keeps abstention viable |
| Object detection (YOLO) | Pests with multiple insects, and box labels exist | Needs bounding-box annotation |
| Segmentation | Lesion area or localisation is an operational requirement | Needs pixel masks |
| Edge inference (TFLite/ONNX) | Offline capture at scale | Only after accuracy is settled; test memory, latency, battery |

Rules:

- Start with the simplest architecture that meets the operational objective.
- Do not assume a complex architecture generalises better to field conditions.
- A quality gate is a separate model and is arguably more valuable than the classifier.
- Domain adaptation from public to field data (small field fine-tune, strong augmentation,
  consistency training) matters more than architecture choice.

---

## 3. Preprocessing and augmentation (Chapter 29)

### 3.1 Preprocessing

Resize, colour conversion and normalisation must match the selected backbone **and** the
deployment code. Training and inference preprocessing are generated from one configuration.

### 3.2 Augmentation

Realistic rotations, crops, mild brightness/contrast changes, scale and modest blur.
Augmentations model what a field camera does, not what an image editor can do.

### 3.3 Avoid

Aggressive hue changes, geometric distortions and synthetic artefacts that change how a
symptom appears. These teach the model to ignore the evidence that matters.

### 3.4 Quality gate

Detect blur, low resolution, extreme exposure and absent plant content. The gate is
versioned; its thresholds are configuration, recorded per prediction.

### 3.5 Reproducibility

Record the preprocessing configuration and library versions with the model. A prediction is
not reproducible without them.

**Implementation points**

- Build a visual review tool to inspect augmented samples.
- Test preprocessing on actual low-cost phone images, not benchmark images.

---

## 4. Training workflow (Chapter 30)

```
freeze dataset + split versions
  → establish a simple baseline
  → train with transfer learning
  → tune hyperparameters on validation only
  → inspect errors and class imbalance
  → calibrate outputs and choose abstention criteria
  → evaluate once on the untouched test set
  → register the artefact and record approval status
```

### 4.1 Imbalance

Use class weights or sampling carefully. Report per-class results because aggregate accuracy
can hide minority-class failure. Do not synthesise a class that has no real examples.

### 4.2 Experiment tracking

Record code commit, data version, architecture, hyperparameters, compute environment and
random seed. Retain failed experiments when they inform design decisions.

### 4.3 Registry

A model is servable only when its `model_registry` row is `approved`. Training metrics alone
never promote a model.

**Implementation points**

- Keep predictions append-only; each model run creates a new row.
- Store the dataset version and preprocessing config with every artefact.

---

## 5. Evaluation (Chapter 31)

Evaluation describes field behaviour, not benchmark behaviour.

| Metric | Requirement |
|---|---|
| Macro F1 | Primary aggregate; never the only number |
| Per-class precision/recall | Required for every supported class |
| Confusion matrix | Required, with sample counts |
| Top-k accuracy | Especially top-3, which is what the UI shows |
| Calibration | ECE / reliability diagram |
| Abstention rate | Reported next to every accuracy/F1 figure |
| Subgroups | Crop variety, geography, season, device, lighting, image quality |

### 5.1 Error analysis

Review false positives, false negatives, look-alike conditions and confident mistakes with
an agronomist. Categorise errors; do not only count them.

### 5.2 Robustness

Test blur, shadows, backgrounds, leaf age and capture distance.

### 5.3 Operational acceptance

Set minimum class-level performance and abstention behaviour before alerts or advice rely
on outputs. Report performance **at the shipped abstention threshold**.

**Implementation points**

- Report sample counts beside every metric.
- Use "not measured" when a number cannot be computed; never estimate one.

---

## 6. Confidence and explainability (Chapter 32)

A model score is not automatically a reliable probability.

- **Calibration:** compare predicted confidence with observed correctness on representative
  validation data.
- **Abstention:** set thresholds that allow the model to say it cannot assess the image.
- **Visual explanations:** Grad-CAM and similar methods help inspect image regions but do
  not prove causal reasoning. Treat them as debugging aids.
- **User communication:** explain likely visual match, uncertainty, image quality and next
  step in plain language.
- **Audit:** store the score vector, threshold, model version and explanation metadata.

Rules:

- No unsupported percentage confidence in the UI.
- `not_calibrated` is displayed as a word, never a number.
- The result card always includes "not a diagnosis".

---

## 7. Forecast task definition (Chapter 33)

A forecast is only meaningful with a precise target.

| Field | Definition |
|---|---|
| Prediction unit | Target condition × crop × geography × issue time × horizon |
| Event | First verified case, incidence threshold, escalation, or another operational outcome — choose explicitly |
| Negative | Verified absence within adequate coverage; never "no report" |
| Horizon | Aligned to decisions and input reliability (nowcast by default; 7-day outlook only when validated) |
| Spatial unit | Smallest geography the inputs support without implying false precision |
| Consumer | Extension worker and farmer SMS/WhatsApp outlook |

Rules:

- Write the event definition before feature engineering.
- Keep different event types as separate prediction tasks.
- A forecast row always carries `issue_time`, `valid_from`, `valid_to`, `coverage` and
  `model_version`.

---

## 8. Feature engineering (Chapter 34)

| Feature family | Examples | Availability rule |
|---|---|---|
| Weather windows | Rolling rainfall, temperature ranges, humidity summaries, consecutive wet days | Must exist at `issue_time`; store `source_timestamp` |
| Crop | Crop type, growth stage, planting window, variety, irrigation context | From crop cycle or calendar |
| Seasonal | Week of year, monsoon period, days since planting | Deterministic |
| Historical pressure | Lagged verified cases, nearby verified reports, prior-season occurrence | Verified only |
| Coverage | Active reporters, field visits, data completeness | Required for the no-score gate |

**Leakage rule:** every feature must be computable at `issue_time`. Store the feature
snapshot; never recompute a historical forecast from today's data.

**Implementation points**

- Store the feature-generation timestamp and source lineage with the snapshot.
- Distance-weighted features use a documented, justified decay.
- Include surveillance intensity so the model can distinguish unobserved from negative.

---

## 9. Baselines (Chapter 35)

| Step | Model | When |
|---|---|---|
| 1 | Documented agronomic rules (weather thresholds + crop stage), versioned and approved | Day one |
| 2 | Logistic regression on weather windows + stage + lagged verified reports | After one season |
| 3 | Gradient boosting (LightGBM/XGBoost) | After 2+ seasons |
| 4 | Spatiotemporal models | Only with dense longitudinal data (year 3+) |

Rules:

- Keep the rules model as a permanent fallback and comparison baseline.
- Select on the operational metric with temporal and spatial holdouts, not training loss.
- A more complex model ships only if it beats the baseline on that metric.
- Version expert rules and record who approved them.

---

## 10. Calibration and thresholds (Chapter 36)

Risk bands derive from validated probabilities or a documented, expert-approved score.
Arbitrary thresholds create false confidence.

- Assess reliability diagrams, Brier score and log loss on temporal holdout data.
- Balance false alarms against missed outbreaks; state the cost of each error type.
- Bands (`low`, `moderate`, `high`, `urgent`, `insufficient_data`) have operational meanings
  and approved actions.
- Display `insufficient_data` when coverage or freshness is inadequate.
- Review thresholds when the crop calendar, reporting patterns or calibration change.
- `probability` is `null` until calibration is approved for display.

**Implementation points**

- Show issue and expiry time with every band.
- "Low risk" never means "no disease is present".

---

## 11. Spatial and temporal forecasting (Chapter 37)

- Aggregate reports to the chosen administrative level and document the method.
- Use neighbour influence with transparent distance and time decay only when biologically
  and operationally justified.
- Use lagged observations and seasonal context available at issue time.
- Validate on held-out locations where possible.
- Display modelled risk separately from observed cases and coverage.
- Use stable geographic identifiers and boundary versions.

**Implementation points**

- Never produce farm-level risk from block-level inputs.
- Historical forecasts retain the boundary version used at issue time.

---

## 12. Combining image and forecast outputs (Chapter 38)

The two tracks support one decision journey but remain logically distinct.

| Output | Meaning | Unit |
|---|---|---|
| Photo assessment | Likely visible symptoms in one photograph | One image + crop context |
| Area outlook | Future risk for a crop–threat–area–time combination | Crop × target × geography × horizon |

Rules:

- Show separate cards with separate timestamps, model versions and confidence.
- Use explicit labels: "Photo assessment" and "Area outlook".
- Do not feed unverified image predictions into the forecast as confirmed cases.
- Preserve original report status through the whole workflow.
- A farmer report becomes a regional signal only after quality checks and verification.

---

## 13. Model acceptance gates

- [ ] Field test set frozen before selection; report at the shipped abstention threshold.
- [ ] Per-class metrics, confusion matrix, sample counts and calibration reported.
- [ ] Abstention rate reported beside every accuracy/F1 figure.
- [ ] Feature snapshot persisted for every scored forecast; re-run reproduces the band.
- [ ] Unverified reports excluded from forecast features (tested).
- [ ] `probability` null unless calibration approved.
- [ ] Model registry shows `approved` before serving.
- [ ] No fabricated metric anywhere in reports or UI.

## 14. Traceability

| Concern | Spec |
|---|---|
| Capture and result presentation | `../feature-specs/02-reporting-and-capture.md` |
| Data tables and registry | `../feature-specs/05-data-layer.md` |
| Forecast output and map | `../feature-specs/06-forecast-and-risk-map.md` |
| Dataset rules | `./data-foundation.md` |
| Honesty and leakage rules | `./ai-workflow-rules.md` §4 |
