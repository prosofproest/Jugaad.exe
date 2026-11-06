# AI-Based Early Pest and Disease Outbreak Prediction Network

**Project code:** PS-03 — Agritech & AI
**Document type:** Summary of the 50+ page project report and implementation blueprint
**Repository note:** this is the condensed report. The operational documents that implement
it live in [`docs-context/`](docs-context/AGENTS.md), the feature contracts in
[`feature-specs/`](feature-specs/README.md), and the chapter-to-file map in
[`README.md`](README.md). Where this summary and `update.md` differ on v1 scope,
`update.md` wins.

---

## 1. One-line definition

An explainable, offline-tolerant AI decision-support platform that provides **per-image crop symptom triage** and **geographically localised pest and disease early warning**, backed by expert verification and approved local advisories.

---

## 2. Purpose and vision

Develop a **farmer-centred early-warning platform** that combines crop images, weather, historical records and regional observations to:

- assess possible visible symptoms on an individual plant;
- estimate local pest and disease risk for a defined crop, area and time window;
- communicate uncertainty honestly;
- recommend safe, locally approved preventive next steps.

**Vision:** a trusted, accessible, locally relevant service that turns fragmented agricultural observations into useful early awareness.

**Mission:** deliver two distinct forms of intelligence — image-based symptom triage and time-bound outbreak risk estimation — connected through shared case management, verified observations and responsible advisory delivery.

---

## 3. The central design rule

The system produces **two separate outputs that must never be conflated**:

| | Photo assessment | Area outlook |
|---|---|---|
| **Question** | What might be visible on *this* plant? | How likely is *this threat* in *this area* over *this window*? |
| **Unit of prediction** | One photo + crop context | Crop × target × geography × horizon |
| **Output** | Candidate classes, quality flags, confidence band, abstention state, model version | Risk band, probability (only if calibrated), drivers, coverage, issue/expiry times |
| **Must never claim** | Laboratory confirmation | Confirmed outbreak |

Neither output replaces field inspection or expert diagnosis. The platform must be able to **abstain** and show **insufficient data**.

---

## 4. Problem statement

- Farmers lack timely, reliable, local information on pest and disease threats.
- Reports are scattered across farms and extension offices; expert capacity is limited.
- Images alone cannot predict regional outbreaks; weather alone cannot confirm disease presence.
- No integrated workflow exists to capture observations, provide cautious image triage, combine contextual data for local risk, and route uncertain cases to experts.
- Technical difficulty: imperfect labels, rare events, uneven reporting, and data that drifts over time.

---

## 5. Objectives

**Primary**

1. Mobile workflow for crop context and image reporting.
2. Image quality checks + multi-class visual triage model.
3. Forecast pipeline for selected crop–threat–area–horizon combinations.
4. Separate map layers for reported cases and forecast risk.
5. Approved preventive guidance and expert escalation.
6. Offline capture, queued upload and safe synchronisation.

**Outcome measures**

- Image: macro F1, per-class recall, calibration.
- Forecast: PR-AUC, Brier score, calibration.
- Operational: false alerts per area/time, median time to expert review, sync success rate.
- User: comprehension, task completion, repeat use, alert usefulness.

---

## 6. Scope

**In the first release**

- One or two priority crops chosen with local partners.
- A small set of common, recognisable target conditions.
- Healthy, abiotic look-alike and unknown classes.
- Photo submission, quality feedback, case history.
- Weather/context ingestion and a baseline risk score.
- Expert review and a basic regional map.
- Local-language text for key workflows.

**Excluded initially**

- All-crop universal diagnosis.
- Unverified farm-level outbreak certainty.
- Autonomous chemical selection or dosage advice.
- Drone/satellite analytics unless separately justified.
- Complex spatiotemporal deep learning before data sufficiency.

**Expansion rule:** add a crop or target only when data, expert labels, local advisory support and evaluation evidence exist.

---

## 7. Stakeholders and personas

**Stakeholders:** farmers, extension workers, plant pathologists/agronomists, agricultural institutions, technology/operations team, programme administrators.

**Personas**

| Persona | Core need |
|---|---|
| Smallholder farmer | Short, local-language, low-data flow with a clear next action; no probability jargon |
| Progressive farmer / farm manager | Crop-cycle history, multiple fields, trends, exportable records |
| Extension worker | Fast case review, location + crop context, verification recording, approved advice |
| Plant pathologist | Original image quality, metadata, alternatives, provenance, label correction |
| District administrator | Aggregated map, time filters, coverage, verified trends, alert audit |

---

## 8. Use cases

1. **Submit a symptom report** — crop/field selection, capture, optional symptom questions, case reference, offline queue.
2. **Inspect a forecast** — risk band, horizon, data freshness, reasons, approved prevention guidance.
3. **Verify a report** — expert queue, image + context review, status and evidence recording.
4. **Monitor an area** — filter map by crop, target, date, verification status; export aggregates.

Failure paths must be designed too: unsupported crop, blurry image, unavailable weather feed.

---

## 9. Requirements

**Functional**

- *Farmer:* account/language, crop-cycle setup, camera + gallery, quality feedback, separate photo assessment / area outlook views, advisory access, expert-review request, offline save/sync.
- *Expert:* review queue, case detail, verification status, label correction, evidence notes, advisory selection, map/case filters.
- *Admin:* user/role management, crop/target/geography configuration, threshold/alert policy, audit, monitoring, export controls.

**Non-functional**

- Responsive capture and form entry; defined inference latency targets.
- Resilience to provider outages; safe retries; stale-data status shown.
- Readable text, large touch targets, localisation, colour-independent severity cues.
- Modular components, automated tests, versioned APIs, model registry.
- Independent scaling of image inference and forecast generation.
- Measurable SLOs for availability, sync success and latency; tested on low-cost Android devices and constrained networks.

---

## 10. System architecture

**Layers**

1. **Client** — farmer mobile app, expert web portal, admin dashboard.
2. **Application** — auth, consent, case management, API validation, workflow orchestration, notifications.
3. **AI** — image quality gate, image classifier, forecast feature pipeline, risk model, calibration, explanation.
4. **Data** — relational records, geospatial data, image object storage, weather snapshots, audit logs, model artefacts.
5. **Integration** — weather provider, boundary datasets, map provider, notification gateway, advisory repositories.

**Principles**

- Modular monolith first; split services only as load and ownership grow.
- Image and forecast services independently versioned.
- Every external feature stores its source timestamp.
- Every displayed prediction has data lineage.

---

## 11. Technology stack

| Area | Recommendation |
|---|---|
| Mobile | Flutter or React Native (Android-first) |
| Backend | Python FastAPI or Django REST (pick one, standardise validation) |
| ML training | PyTorch or TensorFlow |
| ML deployment | ONNX Runtime or TensorFlow Lite |
| Database | PostgreSQL + PostGIS |
| Maps | MapLibre or Leaflet |
| Operations | Containers, managed object storage, metrics, logs, backups, model registry |

Selection criteria: team skills, hosting constraints, maintainability. Avoid premature microservices.

---

## 12. Product surfaces

### Farmer mobile app
Home (crops, local outlook, report button, recent cases, alert prefs) → crop context (optional variety/stage/area) → capture (framing/lighting guidance, retake) → result (separate image and forecast cards, uncertainty, next steps, escalation) → history (status, sync state, reviewer response).

### Expert review portal
Queue sorted by urgency/geography/crop/target/age/uncertainty → case detail with original evidence and model limitations → verification states (confirmed, probable, rejected, duplicate, needs-visit) → feedback capture (corrected class, severity, field observations, optional lab confirmation) → full governance logging.

### Regional dashboard and GIS
Separate layers for verified reports, unverified reports, forecast risk, boundaries and coverage. Filters by crop, target, date, risk band, verification status, admin level. Summary panels for new reports, verified cases, forecast distribution, freshness and backlog. Aggregate locations and suppress small counts.

---

## 13. Data strategy

**Data families**

- Field images + image quality labels
- Crop and crop-cycle context
- Weather observations and forecasts
- Historical occurrence records
- Farmer and extension observations
- Geographic boundaries and environmental context
- Expert advisories and follow-up outcomes

**Quality dimensions:** completeness, accuracy, timeliness, consistency, representativeness, provenance, permission.

**Governance:** every dataset needs an owner, permitted use, update schedule, retention rule and quality checks. Create a data dictionary before complex modelling.

---

## 14. Image data and labelling

**Collection diversity:** devices, districts, seasons, varieties, plant ages, lighting, backgrounds, distances, severity. Include healthy controls, common diseases, pest damage and abiotic look-alikes.

**Metadata:** crop, plant part, date, approximate location, growth stage, image source, verification status.

**Ethics:** explain purpose, obtain consent, exclude identifiable people.

**Labelling handbook**

- Crop-specific taxonomy; clarify whether classes mean pathogen identity, symptom pattern or pest damage.
- Qualified reviewers on a representative subset; adjudicate disagreements.
- Allow *unknown*, *mixed symptoms*, *insufficient evidence*.
- Crop-specific severity criteria.
- Store reviewer, date, evidence type, label confidence, revision history.
- Separate suspected / expert-confirmed / lab-confirmed.
- Measure inter-reviewer agreement.

---

## 15. Data cleaning and splitting

**Cleaning:** validate file type, dimensions, corruption, duplicates, blur, exposure, orientation; validate units, dates, crop names, geo codes, impossible values; distinguish unknown from zero; standardise units/time zones/taxonomy; version raw → cleaned → model-ready; quarantine suspicious records; never discard silently.

**Leakage prevention**

- Image split: group by farm, field, collection event or plant.
- Forecast split: chronological; features must exist at issue time.
- Geographic holdout where feasible.
- Freeze an untouched final test set before model selection.
- Document split seeds and grouping rules.
- Report per-class and per-region metrics with sample counts.

---

## 16. Weather and environmental data

- **Candidate variables:** temperature, relative humidity, rainfall, consecutive wet days, wind, leaf-wetness proxy.
- **Spatial matching:** associate grid/station to admin area; document the method.
- **Temporal aggregation:** lagged windows and rolling summaries available at prediction time.
- **Missing/stale data:** flag explicitly; never silently substitute.
- **Provider governance:** licence, update frequency, historical depth, quality, service limits.
- Validate features with local agronomic expertise; coarse grids do not describe every microclimate.

---

## 17. Historical records

- Sources: extension records, plant clinics, field surveys, farmer submissions, approved institutional datasets.
- Verification tiers stored separately: confirmed, probable, unverified, rejected.
- Features: lagged counts, distance-weighted nearby reports, prior-season occurrence.
- **Bias correction:** include surveillance intensity or reporting coverage as a feature or uncertainty indicator.
- Deduplicate carefully while retaining source links and audit history.
- **Never treat no report as a confirmed disease-free observation.**
- Preserve the distinction between event date and report date.

---

## 18. Database design

**Core entities**

- User and role
- Growing area and approximate geometry
- Crop cycle and crop-stage history
- Observation and image asset
- Image prediction and model metadata
- Forecast and feature snapshot
- Advisory and approval history
- Expert review and verification evidence
- Alert and delivery status
- Audit event and consent record

**Integrity:** stable IDs, foreign keys, status constraints, source timestamps, model versions, append-only prediction history.

**Geospatial:** store approximate geometry or admin codes with explicit precision and access control. Use PostGIS only where spatial queries are needed. Restrict precise location fields.

---

## 19. Backend API design

- **Observation:** create, upload image, retrieve case, request review.
- **Forecast:** query by crop, target, geography, horizon; return issue time, validity, risk band, coverage.
- **Advisory:** retrieve approved guidance by crop, target, language, location.
- **Review:** create/update with role protection and audit trail.
- **Reliability:** idempotency keys, pagination, validation, rate limits, structured errors.
- Publish OpenAPI docs; never expose internal model infrastructure to mobile clients.

---

## 20. Image diagnosis

**Formulation:** cautious visual triage, not pathogen identification.

- **Input:** field photo + optional crop/plant-part context.
- **Output:** candidate scores, quality flags, confidence band, abstention state, model version.
- **Classes:** supported conditions + healthy + abiotic look-alikes + unknown/other.
- **Abstain** when quality is poor, crop unsupported, or input outside reliable domain.
- **Escalate** ambiguous, high-severity or high-impact cases.
- Write user-facing wording before choosing an architecture.

**Architectures**

- Start with transfer learning (MobileNet / EfficientNet).
- Compare ResNet / ConvNeXt only if data and compute justify.
- Object detection only if locating insects/regions is a defined need with bounding-box labels.
- Segmentation only if affected-tissue area or lesion localisation is required with masks.
- Edge inference only after testing memory, latency, battery and update constraints.

**Preprocessing and augmentation**

- Identical preprocessing in training and inference; match the pretrained backbone.
- Realistic rotations, crops, mild brightness/contrast, scale, modest blur.
- Avoid aggressive hue changes, distortions, synthetic artefacts.
- Quality gate: blur, low resolution, extreme exposure, absent plant content.
- Record preprocessing config and library versions with the model.

**Training workflow**

1. Freeze dataset and split versions.
2. Establish a simple baseline.
3. Transfer-learning training.
4. Tune on validation only.
5. Inspect errors and class imbalance.
6. Calibrate outputs and set abstention criteria.
7. Evaluate once on the untouched test set.

Handle imbalance with class weights/sampling; always report per-class results. Track code commit, data version, architecture, hyperparameters, environment and seed.

**Evaluation**

- Macro F1, per-class precision/recall, confusion matrix, top-k accuracy, calibration.
- Subgroups by variety, geography, season, device, lighting, quality.
- Error analysis with experts: false positives/negatives, look-alikes, confident mistakes.
- Robustness: blur, shadows, backgrounds, leaf age, distance.
- Set minimum class-level performance and abstention behaviour before outputs drive alerts.

**Confidence and explainability**

- Calibrate scores on representative validation data; otherwise use qualitative bands.
- Allow abstention via thresholds.
- Grad-CAM and similar are debugging aids, not proof of causal reasoning.
- Explain likely visual match, uncertainty, image quality and next step in plain language.
- Audit score vector, threshold, model version and explanation metadata.
- Never display unsupported percentage confidence.

---

## 21. Outbreak forecasting

**Task definition**

- Prediction unit: target organism/condition × crop × geography × issue time × horizon.
- Event definition: first verified case? incidence threshold? escalation? another operational outcome?
- Negative labels: absence of a report is not necessarily a negative event.
- Horizon aligned to decisions and input reliability (e.g. 7-day outlook if evidence supports).
- Spatial unit: smallest geography the inputs can support without false precision.
- Write target definitions before feature engineering; keep different event types as separate tasks.

**Feature engineering**

- Weather windows: rolling rainfall, temperature ranges, humidity, consecutive wet periods.
- Crop: type, growth stage, planting window, variety, irrigation context.
- Seasonal: week of year, monsoon period, days since planting, local crop calendar.
- Historical pressure: lagged verified cases, nearby reports, prior-season occurrence.
- Coverage: active reporters, field visits, data completeness.
- Prevent future information leakage; store feature-generation timestamp and lineage.

**Baselines (in order of escalation)**

1. Documented expert rules (versioned, with approver).
2. Statistical baselines — logistic regression, seasonal averages, time series.
3. Tree models — Random Forest, XGBoost, LightGBM.
4. Spatiotemporal neural models — only when data volume and quality support them.

Choose the simplest model that meets the operational objective and passes local validation. Keep the baseline as fallback.

**Calibration and thresholds**

- Assess reliability diagrams, Brier score, log loss on temporal holdout.
- Balance false alarms against missed outbreaks using the cost of each error.
- Risk bands (low / moderate / high / urgent) must have operational meanings and approved actions.
- Show a no-score state when coverage or freshness is inadequate.
- Review thresholds when crop calendar, reporting patterns or calibration change.
- Show issue time and expiry time. Low risk ≠ no disease present.

**Spatial and temporal forecasting**

- Aggregate reports to the chosen admin level; document the method.
- Neighbour influence only with transparent distance/time decay and biological justification.
- Use lagged observations and seasonal context available at issue time.
- Test on held-out locations where possible.
- Display modelled risk separately from observed cases and coverage.
- Never infer farm-level precision from district-level inputs.
- Use stable geographic identifiers and boundary versions.

---

## 22. Combining the two outputs

- Image output = likely visible symptoms in one photo.
- Forecast output = future risk for a crop–threat–area–time combination.
- A farmer report becomes a regional signal only after quality checks and verification.
- UI shows separate cards with separate timestamps, model versions and confidence descriptions.
- **Unverified image predictions never enter the forecast as confirmed cases.**
- Use explicit labels such as "photo assessment" and "area outlook".

---

## 23. Risk map

- Content: verified reports, unverified reports, modelled risk, coverage.
- Aggregation: admin boundaries or grid cells matched to input resolution.
- Privacy: no exact farm coordinates for unauthorised users.
- Temporal controls: issue date, horizon, historical report period.
- Performance: vector tiles or server-side aggregation at scale.
- Always show a legend, issue time, horizon and plain-language explanation.
- **Never merge reported cases and predicted risk into one undifferentiated heatmap.**

---

## 24. Advisory engine

- Structure: crop, target, geography, season, language, validity period, author, approver, source.
- Action types: scouting, monitoring, sanitation, crop-management practices, escalation.
- Agronomists review wording and suitability for crop stage and region.
- **No invented pesticide names, rates, mixtures, waiting periods or legal-use instructions.**
- Version history and expiry display.
- Start with non-chemical prevention and monitoring; route severe/uncertain cases to experts.

---

## 25. Alerts

- Trigger on validated risk threshold + data freshness + minimum coverage.
- Deduplicate repeated signals for the same area and target.
- Severity-specific cooldowns to prevent fatigue.
- Channels: push, SMS or approved messaging, per user preference.
- Allow acknowledgement, feedback and preference changes.
- Include area, crop, target, valid period, reason and next action.
- **Never label a forecast as a confirmed outbreak.**

---

## 26. Offline-first engineering

- Cache crop lists, advisories, recent forecasts, unsent observations.
- Upload queue with client-generated IDs, retry count, sync status.
- Compress images while retaining diagnostic detail.
- Show last-updated time; label cached forecasts as stale after expiry.
- Observations append-only; expert verification changes preserved.
- Test airplane mode, intermittent network, interrupted uploads.
- Idempotency keys prevent duplicate submissions.

---

## 27. Security, privacy and responsible AI

**Security**

- Secure authentication, session management, RBAC.
- Encryption in transit and at rest; private image storage.
- Validate uploads, rate-limit APIs, protect secrets, patch dependencies.
- Audit sensitive access, reviews, exports and model configuration changes.
- Backups, tested restoration, incident response ownership.
- Complete a threat model before production; no provider secrets in the app.

**Privacy and responsible AI**

- Data minimisation; consent in plain language.
- Approximate location by default; restrict exact farm coordinates.
- Evaluate fairness across geography, device, season and farmer groups.
- Human oversight and a correction path.
- Defined retention and deletion procedures.
- No PII in public dashboards.

---

## 28. Testing strategy

- **Unit/integration:** input rules, feature engineering, model service contracts, DB writes, notifications.
- **End-to-end:** report creation, upload, inference, expert review, alert delivery, offline sync.
- **Security:** authorisation boundaries, upload handling, data leakage, secrets.
- **Usability:** realistic outdoor and constrained-network conditions.
- **Model:** spatial/temporal holdouts, subgroup metrics, calibration, error analysis.
- Maintain a test matrix linking requirement → scenario → expected result → evidence.
- Include negative and failure cases.

**Example test cases**

- Supported crop image with valid network.
- Blurry image triggers retake request.
- Unsupported crop never forces a diagnosis.
- Offline save then sync after reconnect.
- Upload retry creates no duplicate observation.
- Only authorised experts change review status.
- Forecast returns issue/expiry times.
- Stale weather feed returns insufficient-data state.
- Map layers distinguish verified reports from predictions.
- Expired cached forecast marked stale.
- Cross-farmer access denied; invalid file type rejected; private image URL expires.
- Sensitive exports role-restricted and audited.

---

## 29. Pilot and deployment

**Pilot**

- Choose representative sites with extension partners and feasible verification.
- **Silent phase:** predictions without farmer-facing alerts, compared with field observations.
- **Limited alert phase:** small approved set after thresholds and response workflows are reviewed.
- Track lead time, false alerts, missed events, review workload, comprehension, reliability.
- Expand only when evidence and operational capacity justify it.
- Document baseline conditions and comparison method; no yield claims without a proper study design.

**Deployment**

- Separate development, staging and production.
- Package services, automate tests, run migrations safely, controlled rollout.
- Scale image inference independently of API traffic.
- Back up DB, object metadata, model artefacts and configuration.
- Test restore procedures and document RTOs.
- Infrastructure-as-code where practical; documented, tested rollback.

---

## 30. Monitoring and maintenance

- **Data:** missingness, freshness, duplicates, source changes, geography coverage.
- **Model:** prediction distribution, abstention rate, verified performance, calibration drift.
- **Product:** latency, error rates, upload backlog, sync success, notification delivery.
- **Feedback loop:** complaints, expert corrections, field outcomes.
- Retrain only with governed, verified data and the frozen evaluation suite.
- Retain previous model versions for rollback.
- Never auto-promote a model on training metrics alone.

---

## 31. Team

| Role | Responsibility |
|---|---|
| Product lead | Scope, user research, milestones, stakeholder communication, acceptance |
| Agronomist / pathologist | Target selection, taxonomy, labels, risk rules, advisory approval |
| Data engineer | Ingestion, storage, data quality, geospatial processing, lineage |
| ML engineer | Image and forecast modelling, evaluation, calibration, monitoring |
| Application engineers | Mobile, backend, portal, APIs, offline sync |
| QA and field researcher | Test strategy, usability studies, field pilot, issue reporting |

One accountable owner per deliverable; regular field feedback sessions.

---

## 32. Roadmap

| Phase | Focus |
|---|---|
| 0 — Discovery | Crop, target, geography, stakeholders, event definitions, pilot success measures |
| 1 — Data foundation | Data access, image collection, labels, weather ingestion, database |
| 2 — Platform MVP | Mobile reporting, case management, expert portal, offline queue |
| 3 — Image AI | Field-image model with quality gate and abstention |
| 4 — Forecasting | Rules baseline, feature pipeline, model, calibration, risk map |
| 5 — Pilot | Silent evaluation, limited alerts, field verification, usability refinement |
| 6 — Rollout | Operational readiness, monitoring, training, controlled expansion |

Data access and expert annotation are critical-path. Do not promise reliable forecasts before sufficient historical evidence exists.

---

## 33. Budget and risk

**Budget areas:** people; data acquisition (field visits, enumerators, expert labelling, lab confirmation, licences); infrastructure (compute, GPU, DB, storage, maps, monitoring, backups); operations (connectivity, devices, training, translation, support); risk reserve.

Prepare low / expected / high scenarios; track recurring operating cost separately from one-time development cost.

**Key risks and mitigations**

| Risk | Mitigation |
|---|---|
| Data scarcity | Start with rules and a reporting network; don't overstate capability |
| Domain shift | Diverse field data; evaluate by district, season, device |
| Reporting bias | Track surveillance intensity and verification status |
| False alarms | Calibrate thresholds, cooldowns, feedback |
| Missed events | Review false negatives; maintain extension escalation |
| Unsafe advice | Expert-approved local content; no autonomous chemical prescriptions |

Maintain a live risk register with owner, likelihood, impact and mitigation status; review at every milestone.

---

## 34. Success metrics

| Level | Metrics |
|---|---|
| Technical | Image macro F1, per-class recall, forecast PR-AUC, Brier score, calibration, latency |
| Operational | Report-to-review time, backlog, verified case rate, notification delivery, sync success |
| User | Task completion, comprehension, repeat use, alert usefulness, opt-out rate |
| Agricultural | Lead time, inspection prioritisation, outcome indicators where credible |
| Equity | Performance and adoption by geography, device and user segment |

Set a baseline before pilot; report limitations and sample sizes alongside claimed impact.

---

## 35. Demonstration scenario

1. Farmer selects a supported crop and area, photographs a leaf, submits.
2. App flags blur and requests a retake.
3. A clearer image receives a possible symptom match with medium confidence.
4. Local outlook separately shows moderate risk for a supported target over 7 days, with weather and crop stage as drivers.
5. Farmer receives scouting guidance and can request expert review.
6. Report appears as unverified in the expert queue.
7. Extension worker records confirmed / probable / unresolved.
8. Dashboard updates the verified-report layer without conflating it with the forecast layer.

Demo data must be clearly labelled as demonstration data; fabricated predictions must never be presented as real warnings.

---

## 36. Launch-readiness gates (Appendix H)

**Agronomy and data**

- Crop and target scope approved by local experts.
- Label handbook and verification workflow active.
- Data permissions and provenance documented.
- Weather and boundary data freshness monitored.

**AI and product**

- Image and forecast models evaluated separately.
- Calibration and abstention behaviour tested.
- Risk map distinguishes reports, predictions and coverage.
- Advisories approved and versioned.
- Offline queue and stale-data handling tested.

**Operations and governance**

- Consent, privacy and retention procedures active.
- Security review completed.
- Alert thresholds and escalation owners approved.
- Monitoring, rollback and incident response ready.
- Pilot findings reviewed and documented.

If a gate is not met, keep the affected feature in non-operational or silent pilot mode.

---

## 37. Open decisions required before build

1. Pilot **crop(s)** and **target organism list**, including look-alikes.
2. **Geography** and the smallest defensible spatial unit.
3. **Event definition** for the forecast (first verified case / incidence threshold / escalation).
4. **Weather provider** — licence, resolution, history, latency — and **boundary dataset**.
5. **Advisory source and approver**, plus local-language content.
6. **Thresholds and risk-band meanings** — all document examples are design placeholders.

---

## 38. Key takeaways

- The highest-value first step is **not** the most complex model — it is a dependable **reporting and verification workflow** that produces trustworthy data.
- **Trust, usability and field outcomes** are first-class success criteria.
- **Uncertainty and data coverage** must be visible in the interface.
- **Human review** is mandatory for ambiguous or high-impact cases.
- **No report ≠ disease-free**; surveillance intensity must be modelled and displayed.
- **Never** claim laboratory confirmation, autonomous chemical advice, or farm-level precision from coarse inputs.
- **Abstain** rather than force a result.

---

*This summary condenses the 55-chapter blueprint and Appendices A–H. All example thresholds, payloads and sample outputs in the source document are design illustrations until locally validated.*
