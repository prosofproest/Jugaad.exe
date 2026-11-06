# Phase plan — detailed work breakdown

**Project:** PS-03 — AI-Based Early Pest and Disease Outbreak Prediction Network
**Purpose:** expand the seven-phase roadmap into the concrete work each phase contains, so
no phase is just a label. This is the planning-level companion to the status view.
**Status:** planning baseline. No phase beyond Phase 0 has started.
**Last updated:** 2026-11-06

---

## 0. How to use this document

| Document | Answers |
|---|---|
| `progress-tracker.md` §2 | **Where we are now** — phase status, checkboxes, live gates |
| `phase-plan.md` (this file) | **What the work in each phase actually is** — workstreams, deliverables, boundaries |
| `roadmap-and-resources.md` §1 | **Why the phases are ordered this way** — rationale and critical path |
| `feature-specs/` | **The contract for a feature** — requirement IDs and acceptance criteria |

Rules for this document:

1. `progress-tracker.md` is authoritative for status. This file never marks a phase done.
2. Each phase has an **entry condition**, a set of workstreams, **deliverables**, an
   **exit gate**, and an explicit **not in this phase** list.
3. A phase does not start until its predecessor's gate is met. Limited overlap is allowed
   only for workstreams that do not depend on the missing gate, and the overlap is recorded
   as a decision in `progress-tracker.md`.
4. Durations are indicative planning assumptions, not commitments. Re-estimate at every gate.
5. Any change to phase scope, gate criteria or sequencing updates this file **and**
   `progress-tracker.md` in the same change.

---

## 1. Phase list at a glance

| Phase | Core question | Main output | Exit gate | Indicative duration |
|---|---|---|---|---|
| **0 — Discovery** | What exactly are we building, for whom, where, and how will we know it worked? | Decisions D1–D6, partners, crop calendar, pilot protocol | Gate 0: decisions resolved and recorded | 4–6 weeks |
| **1 — Data foundation** | Can we collect, label, store and reproduce trustworthy data? | Permissioned datasets, label handbook, schema, ingestion, frozen test set | Gate 1: permissions + reproducible ingestion + approved label handbook | 3–4 months |
| **2 — Platform MVP** | Can a report survive the field and reach a human verifier? | Offline capture, case management, expert review, audit | Gate 2: offline report synced once, reviewed, audited | 3–4 months |
| **3 — Image AI** | Can the photo assessment be useful and honest? | Quality gate, calibrated triage model, abstention, ONNX serving, result card | Gate 3: field-test performance at the shipped abstention threshold | 3–4 months |
| **4 — Forecasting** | Can we produce a reproducible area outlook without overclaiming? | Rules baseline, feature snapshots, no-score path, risk map, advisories, alerts | Gate 4: reproducible forecast + verified no-score + approved thresholds | 3–4 months |
| **5 — Pilot** | Does it help real decisions in a real season? | Silent-phase evidence, limited alerts, usability findings, issue log | Gate 5: silent evidence reviewed, alert workflow staffed | One epidemic season (4–6 months) |
| **6 — Rollout** | Can someone else operate and sustain it? | Runbooks, monitoring, training, signed launch checklist, named owner | Gate 6: all launch gates met and signed | 2–3 months |

**Total:** ~18 months to limited operational alerts, with deliberate overlap between
engineering phases and the long-running data-collection and pilot workstreams.

---

## 2. Sequencing and dependencies

```
Phase 0  Discovery
   │  Gate 0: D1–D6 resolved
   ▼
Phase 1  Data foundation ──────────────┐
   │  Gate 1: permissions, ingestion,  │  Field collection and labelling
   │          label handbook           │  continue past Gate 1
   ▼                                   │
Phase 2  Platform MVP ◄────────────────┘
   │  Gate 2: offline → verified → audited
   ▼
Phase 3  Image AI ───────────┐
   │  Gate 3: field-test report│  Shared data foundations only.
   ▼                           │  Dependent work waits for Gate 3.
Phase 4  Forecasting ◄─────────┘
   │  Gate 4: reproducible forecast, no-score, approved bands
   ▼
Phase 5  Pilot (timed to the epidemic season)
   │  Gate 5: silent evidence + staffed response
   ▼
Phase 6  Rollout
      Gate 6: launch-readiness checklist signed
```

**Hard dependencies**

| Work | Cannot start until | Why |
|---|---|---|
| Any schema code | D1 (crop/target/zone) | Entity choices, enums and config depend on the supported list |
| Image model training on field data | Permissioned dataset + frozen field test set | R6/R10: no training on undocumented data |
| Forecast implementation | D1, D2, event definition | Target, horizon and labels define the task |
| Operational alerts | Gate 5 | Silent phase must produce evidence first |
| Expansion to a new crop/zone | Evidence + capacity review | Expansion rule in `project-overview.md` §8 |

**Critical path:** data access, expert annotation and verification capacity. A slip in
Phase 0 or Phase 1 moves every later gate.

**On overlap:** the indicative durations assume that long-running work (field collection,
labelling, pilot operations) continues across gate boundaries. Engineering work that
depends on a gate still waits for it. Any other overlap is a recorded decision, not an
assumption.

---

## 3. Phase 0 — Discovery and scope lock

**Objective:** replace assumptions with recorded decisions, named partners and a measurable
pilot design. No code that depends on an unresolved decision may start.

**Entry condition:** repository documentation baseline exists (current state).

### 3.1 Resolve the six blocking decisions (D1–D6)

- **D1 — Crop + 3–5 targets + agro-climatic zone.** Score candidate crops on economic
  importance to smallholders, existing extension presence, visual distinctness of symptoms,
  availability of approved advisory content, and existence of a validated weather-driven
  risk model. Define the class list explicitly: targets, healthy, abiotic look-alike,
  unknown/other. Name the differential look-alikes for each target.
- **D2 — Nowcast or 7-day outlook.** Decide the v1 horizon, issue cadence, validity window
  and what "expired" means. Record the reason: early forecasts need outcome history that
  does not exist yet.
- **D3 — Verifier role, capacity and SLA.** Name who verifies, expected cases/day, triage
  rules, escalation path to a pathologist, workload cap, compensation and review SLA.
- **D4 — Owning/paying institution.** Identify the post-pilot owner and funding path. Record
  data ownership, hosting responsibility and service-life assumptions.
- **D5 — Primary outcome metric.** Pre-register one primary metric, recommended: median lead
  time from first farmer report to verified expert confirmation, versus the existing
  advisory baseline. Define baseline measurement and comparison method.
- **D6 — Legal position on advisory content.** Confirm non-chemical-only guidance, legal
  review route, disclaimer wording and escalation policy.

### 3.2 Partners, governance and ethics

- Draft MoUs/LOIs with extension services, plant clinics, universities and the data owner.
- Agree data-sharing, image ownership, publication rights, retention and deletion.
- Open the DPIA and ethics/IRB process; confirm consent wording in the local language.
- Name the field operations lead, agronomist/pathologist reviewer and data owner.
- Build the stakeholder responsibility matrix (who collects, verifies, approves, responds).

### 3.3 Agronomic groundwork

- Document the crop calendar: planting windows, growth stages, harvest, epidemic window.
- Build the target reference sheet: symptom description, distinguishing features, look-alike
  conditions, severity anchors, and the evidence needed to verify each one.
- Inventory existing advisory sources, their approvers, languages, validity periods and gaps.
- Map the pilot geography: admin levels, boundary versions, smallest defensible spatial unit.

### 3.4 Data asset inventory

- Assess plant-clinic archives, university collections, extension records and public datasets.
- For each asset record: owner, licence, label quality, coverage, date range, format and
  permission status. Separate "usable for pretraining" from "usable for validation".
- Confirm free/low-cost weather (NASA POWER / ERA5-Land) and boundary sources, or record the
  paid-provider justification.

### 3.5 Pilot and evaluation design

- Select candidate sites with a feasible verification process and a comparison design
  (matched control or stepped-wedge); document why the design is credible.
- Define the silent phase, limited-alert phase, alert templates and escalation owners.
- Pre-register D5, the analysis plan, sample-size logic and the decision rule for expansion.
- Time the pilot to the epidemic season, not the funding cycle.

### 3.6 Delivery planning

- Confirm architecture baseline, ADRs and repository layout are still valid for D1–D6.
- Produce low/expected/high budget scenarios and a staffing plan (7–9 people).
- Assign an owner and review date to every risk in `progress-tracker.md` §6.
- Write the Phase 1 data acquisition plan: collection targets, labelling throughput,
  partner responsibilities and dependencies.

### Deliverables

- Decision record for D1–D6 with options, consequence, owner and date.
- Signed or drafted partner agreements and data-permission register.
- Crop calendar, target reference sheet and pilot area map.
- Pilot protocol v1 with pre-registered D5 metric and comparison design.
- DPIA/ethics scope and consent wording.
- Data acquisition plan and budget/staffing scenarios.
- Updated `progress-tracker.md` with decisions and the next-phase entry list.

### Exit gate — Gate 0

- D1–D6 answered and recorded in `progress-tracker.md` §4.
- A named partner and verification route exist for the pilot.
- Crop calendar and epidemic window are documented.
- The pilot protocol and D5 metric are pre-registered.
- No code depending on an unresolved decision has been written.

### Not in this phase

- Production code, real farmer data collection, model training, advisory publishing.
- Any commitment to a crop, zone or alert threshold that has not been signed off.

**Primary owner:** Product lead, with the agronomist and programme lead.

---

## 4. Phase 1 — Data foundation

**Objective:** build a permissioned, reproducible data foundation and a labelling system that
produces trustworthy labels. This phase is the long pole; field collection continues beyond
its gate.

**Entry condition:** Gate 0 met.

### 4.1 Governance and permissions

- Execute MoUs/licences for every dataset; create a dataset register with owner, permitted
  use, retention rule, update schedule and quality check.
- Finalise consent wording for images, context and location; implement consent capture in the
  upcoming identity module (design now, build in Phase 2).
- Complete the DPIA and record the retention/deletion procedure.
- Define the quarantine path and the rule that suspicious records are never silently dropped.
- Write data dictionary v1: every field used in training or forecasting, its type, unit,
  allowed values, source, owner and missing-value meaning.

### 4.2 Image collection network

- Publish the capture protocol: device, distance, angle, lighting, background, plant part,
  severity, multiple images per case, metadata to record.
- Define a sampling matrix across districts, seasons, varieties, plant ages, lighting,
  backgrounds, symptom severity and devices. Include healthy controls, abiotic look-alikes,
  ambiguous cases, rejected images and hard negatives.
- Train enumerators/extension workers; run a pilot collection batch; measure throughput and
  reject rate; revise the protocol.
- Set up secure upload, backup and original-image retention; keep processed derivatives
  separate.
- Track collection progress against the sampling matrix, not just a total count.

### 4.3 Archive acquisition

- Ingest plant-clinic and university archives where permitted.
- Reconcile archive labels to the project taxonomy; flag unmappable records.
- Preserve source links, original labels, reviewer identity and provenance.
- Keep archive data separate from fresh field data in the dataset register.

### 4.4 Labelling system

- Write the labelling handbook: crop-specific taxonomy; whether a class is pathogen identity,
  symptom pattern or pest damage; uncertainty classes (`unknown`, `mixed`, `insufficient
  evidence`); crop-specific severity criteria; provenance; revision history.
- Separate suspected, expert-confirmed and laboratory-confirmed labels.
- Run a reviewer calibration round on a representative subset; measure inter-reviewer
  agreement; adjudicate disagreements; revise unclear definitions.
- Define reviewer training, quality sampling and label-audit cadence.
- Ensure hard negatives and ambiguous images are retained for abstention training.

### 4.5 Data platform and schema

- Implement the schema slices from `feature-specs/05-data-layer.md`: identity, geography,
  crop cycles, observations, media, predictions, forecasts, feature snapshots, advisories,
  reviews, alerts, audit, consent and model registry.
- Use stable IDs, foreign keys, status constraints, source timestamps and append-only
  prediction/review/audit rows. Use PostGIS only where spatial queries are needed.
- Set up migrations (Alembic), object-storage layout, presigned URL rules and backup design.
- Seed only clearly labelled `is_demo` data.

### 4.6 Weather, boundaries and historical records

- Ingest weather variables (temperature, humidity, rainfall, wet-day runs, wind,
  leaf-wetness proxy where available) with source timestamps and freshness metadata.
- Record the spatial-matching method from grid/station to admin unit.
- Load versioned boundary geometry; store the boundary version with every derived record.
- Ingest historical occurrence records with verification tier, event date vs report date,
  source link and dedupe history.
- Make missing/stale data explicit: produce `insufficient_data`, never silent imputation.

### 4.7 Data quality and versioning

- Automated quality report per ingestion batch: file type, dimensions, corruption, duplicates,
  blur, exposure, orientation; tabular units, dates, crop names, geo codes, impossible values.
- Distinguish unknown from zero; record imputation flags where justified.
- Version raw → cleaned → model-ready datasets with reproducible transformation code.
- Maintain a quarantine queue and a data-quality dashboard.

### 4.8 Splits and frozen test set

- Image splits grouped by farm, field, collection event or plant; document the grouping rule
  and seed.
- Forecast splits chronological; verify every feature is available at issue time.
- Create a geographic holdout where feasible.
- Freeze a field-only test set before any model selection; record the freeze date, contents
  and access control.
- Document per-class/per-region reporting requirements and sample-count expectations.

### Deliverables

- Dataset register and permission records.
- Data dictionary v1.
- Capture protocol, sampling matrix and collection progress report.
- Labelling handbook v1, calibration results and agreement measure.
- Migrated database schema, storage layout and backup design.
- Weather/boundary ingestion jobs and snapshots.
- Data-quality reports, quarantine log and dataset versions.
- Split manifests and a frozen field test set.

### Exit gate — Gate 1

- Documented permission for every dataset used.
- Ingestion is reproducible from raw source to model-ready version.
- Label handbook approved by a pathologist.
- Data dictionary and quality checks exist for every field.
- Field test set frozen before model selection.
- Unverified reports are excluded from forecast features (tested).
- Weather gaps produce `insufficient_data`, not imputed values.

### Not in this phase

- Model performance claims, production alerts, advisory publication.
- Training or evaluation on data without documented permission.

**Primary owner:** Data engineer, with the agronomist and field operations lead.

---

## 5. Phase 2 — Platform MVP (reporting and verification loop)

**Objective:** deliver a working, offline-first loop: capture a report in the field, sync it
once, review it as a human, and audit every step. No model is required for this phase to be
useful.

**Entry condition:** Gate 1 met (or explicit, recorded exception for schema-only overlap).

### 5.1 Engineering foundation

- Scaffold `backend/`, `mobile/`, `web/`, `database/` and `deploy/` with the approved stack.
- Set up CI, linting, test runners, migrations, local compose, `dev`/`staging` environments,
  secret management and structured logging.
- Publish the OpenAPI skeleton and error format; define API versioning.
- Add a test matrix that links requirement ID → scenario → expected result → evidence.

### 5.2 Identity, roles, consent and privacy

- Implement phone-OTP registration for farmers; provisioned accounts for extension workers,
  pathologists and admins.
- Four roles only; deny by default; object-level access checks; MFA for pathologist/admin.
- Capture consent in plain language; record consent version and timestamp.
- Add privacy-request handling, retention jobs and account deletion procedures.
- Audit role changes, admin record views and exports with a recorded reason.

### 5.3 Mobile context and capture

- Onboarding, language preference, supported-crop list and approximate-area selection.
- Crop-cycle setup with optional variety, growth stage and notes; "unknown" is first-class.
- Camera/gallery capture with framing, lighting and distance guidance.
- On-device pre-check for blur, exposure, resolution and plant presence; retake without
  losing context; keep the best attempt.
- Record original dimensions, file size, source and pre-check result; compress for upload
  while retaining diagnostic detail.

### 5.4 Offline queue and synchronisation

- Local persistence for crop lists, advisories, recent outlooks and unsent observations.
- Client-generated `client_report_id` plus `Idempotency-Key`; retry with backoff; resume or
  restart uploads safely.
- Distinct queued/syncing/synced/failed states; queue count on Home; Wi-Fi-only preference;
  queue-size warning and no silent drop.
- History reads from cache with a visible stale indicator.
- Test airplane mode, intermittent network, interrupted upload and duplicate retry.

### 5.5 Observation and media backend

- Create observation before upload; presigned upload URLs; validate type, size and corruption.
- Enforce duplicate prevention and append-only observation history.
- Store approximate location only; restrict exact geometry by role.
- Case retrieval, pagination, structured errors, rate limits and idempotent endpoints.
- Request-review endpoint with an auditable state transition.

### 5.6 Expert review portal

- Queue sorted by urgency, geography, crop, target, age and uncertainty; assignment and
  escalation.
- Case detail: original image, crop context, capture date, image quality, model candidates
  (placeholder until Phase 3), prior reviews and forecast context.
- Verification states: confirmed, probable, rejected, duplicate, needs-visit, unresolved.
  `confirmed` requires the pathologist role.
- Evidence notes required for high-impact decisions; label correction with revision history.
- "Needs better image" and "needs field visit" actions.
- Governance: reviewer identity, timestamps, edits and advisory approvals logged.

### 5.7 Admin configuration

- Manage crops, targets, geographies and boundary versions.
- Manage users, roles and partner assignments.
- Configure threshold and alert-policy placeholders without inline numbers in code.
- Export controls: role check, purpose, row limit, PII exclusion, audit.

### 5.8 Audit and telemetry

- Emit append-only audit events for auth, consent, review transitions, exports, admin views,
  config changes and role changes.
- Define metric events without PII: sync success, queue depth, review latency, error rates.

### 5.9 Quality, security and release

- Unit tests for domain rules; integration tests for API/database; E2E for offline capture →
  sync → review → audit.
- Negative cases: unsupported crop, blurry image, duplicate retry, unauthorised role, expired
  session, cross-farmer access.
- Accessibility and usability pass on a low-cost Android device and constrained network.
- Threat model before phase exit; dependency and secret scanning; upload abuse tests.

### Deliverables

- Flutter capture app (field-staff ready), FastAPI monolith, Next.js review portal and admin
  console.
- Migrated schema slices and seed data labelled `is_demo`.
- Test matrix with executed evidence.
- Audit trail and telemetry events.
- Deployment to `staging` with a rollback note.

### Exit gate — Gate 2

- A report can be captured offline, synced exactly once, reviewed and audited on a low-end
  device.
- Duplicate retry produces no duplicate observation.
- Only authorised roles can change verification status; every change is audited.
- No PII or exact farm geometry leaks to unauthorised roles.
- No model is required for the loop to work.

### Not in this phase

- Image inference, forecast accuracy, alert dispatch, advisory approval.
- Automated verification or model-driven status changes.

**Primary owner:** Application engineers, with QA and the security reviewer.

---

## 6. Phase 3 — Image AI (assistive photo assessment)

**Objective:** ship a calibrated, field-tested image triage capability that can abstain and
explain itself. It assists a human; it never diagnoses.

**Entry condition:** Gate 2 met and the field dataset/test set from Phase 1 is available.

### 6.1 Data readiness

- Confirm field-image inventory against the sampling matrix; identify gaps by district,
  season, device, lighting and severity.
- Use public datasets for pretraining/benchmarking only; never for validation.
- Retain hard negatives, ambiguous and rejected images; define the `unknown`/`other` class.
- Fix the preprocessing recipe and augmentation policy before training; match the pretrained
  backbone; avoid hue distortions and synthetic artefacts.
- Reconfirm the frozen field test set and its access control.

### 6.2 Quality gate

- Build a separate quality gate for blur, low resolution, extreme exposure, absent plant
  content and unsuitable distance.
- Define pass/fail reason codes and configuration versioning.
- Evaluate the gate on real low-cost-phone field images, not curated samples.
- Wire it so a failure returns `abstained` with a reason and never blocks saving the report.

### 6.3 Model development

- Establish a simple baseline, then transfer learning (MobileNet/EfficientNet class); compare
  larger models only if data and compute justify it.
- Handle class imbalance with class weights or sampling; report per-class results.
- Track commit, data version, architecture, hyperparameters, environment and seed.
- Inspect errors with experts: false positives/negatives, look-alikes, confident mistakes.
- Build the quality-gate + classifier contract before tuning the classifier.

### 6.4 Calibration, confidence and abstention

- Calibrate scores on representative validation data; otherwise use qualitative bands.
- Choose abstention thresholds on validation using hard negatives; never optimise them on the
  test set.
- Define confidence bands and the wording for each.
- Define unsupported-crop and out-of-domain behaviour.
- Audit the score vector, threshold, model version and explanation metadata.

### 6.5 Evaluation

- Report macro F1, per-class precision/recall, confusion matrix, top-k and calibration
  (ECE/reliability) on the frozen field test set.
- Report the abstention rate and performance **at the shipped threshold**, with sample counts.
- Break down by variety, geography, season, device, lighting and image quality.
- Test robustness: blur, shadow, background, leaf age, distance.
- Record limitations and failure modes explicitly; no aggregate metric without breakdown.

### 6.6 Serving and registry

- Export to ONNX; run CPU inference at pilot scale; measure latency on the target device path.
- Add a model registry entry with version, status, approval, metrics and artefact location;
  refuse to serve an unapproved version.
- Persist an append-only prediction row per run with image snapshot, model version,
  timestamps, threshold and quality flags.
- Version the inference contract so a model change does not silently change the API.

### 6.7 Result experience

- Separate `AssessmentCard` from `OutlookCard`; never merge them.
- Show up to three candidates, qualitative confidence, quality flags, model version and
  generated time.
- Abstention shows the reason, retake path and escalation; no candidate list.
- Unsupported crop shows the supported list and escalation; never a forced class.
- Include "not a diagnosis" wording and a route to expert review.
- Keep all strings externalised for translation.

### Deliverables

- Quality-gate module with reason codes and tests.
- Trained image model, preprocessing config and experiment record.
- Evaluation report on the frozen field test set, including abstention and subgroups.
- ONNX artefact and approved registry entry.
- Versioned inference endpoint and append-only prediction records.
- Assessment result card with abstention, quality flags and escalation.

### Exit gate — Gate 3

- Performance is reported at the shipped abstention threshold on a field-only test set, with
  sample counts and subgroup breakdowns.
- Abstention works on hard negatives and unsupported inputs.
- Quality gate failures return actionable reasons and never block submission.
- No unsupported percentage confidence is displayed.
- The model is registered, approved and version-pinned in served predictions.

### Not in this phase

- Laboratory or confirmed-diagnosis claims.
- Feeding photo assessments into the forecast as confirmed cases.
- On-device inference beyond the agreed quality pre-check (deferred unless separately
  justified).

**Primary owner:** ML engineer, with the agronomist and app engineers.

---

## 7. Phase 4 — Forecasting, risk map, advisories and alerts

**Objective:** produce a transparent, reproducible area outlook with an explicit no-score
state, show it separately from observed reports, and connect approved guidance and alerts.

**Entry condition:** Gate 3 met; D1, D2 and the event definition are recorded.

### 7.1 Task definition and event semantics

- Write the event definition before feature engineering: first verified case, incidence
  threshold, escalation or another operational outcome.
- Fix crop × target × geography × issue time × horizon; define the smallest defensible
  spatial unit.
- Define negative labels as verified absence within coverage, never "no report".
- Define issue cadence, validity and expiry; keep different event types as separate tasks.
- Document the surveillance-bias treatment and how coverage is represented.

### 7.2 Rules baseline

- Implement a versioned, expert-approved agronomic risk index (weather thresholds + crop
  stage) as the day-one forecast.
- Record the approver, source, version and review date.
- Define risk bands and the operational action for each: low, moderate, high, urgent,
  insufficient_data.
- Keep the baseline as the permanent fallback and comparison model.
- Validate against field observations and record disagreements.

### 7.3 Feature pipeline and snapshots

- Weather windows: rolling rainfall, temperature ranges, humidity and consecutive wet days.
- Crop: type, stage, planting window, variety and irrigation context.
- Seasonal: week of year, monsoon period, days since planting, local crop calendar.
- Historical pressure: lagged verified cases, nearby verified reports, prior-season
  occurrence.
- Coverage: active reporters, visits, completeness and data freshness.
- Enforce the leakage rule: every feature must be computable at `issue_time`.
- Persist an immutable feature snapshot per run with lineage and generation timestamp.

### 7.4 Forecast generation and no-score gate

- Scheduled daily job per crop × target × area.
- Gate checks: weather freshness, minimum coverage, calendar/stage availability, boundary
  version match, approved model version.
- If a gate fails, persist a forecast row with `insufficient_data`, a machine reason code and
  coverage; never impute.
- If it passes, compute features, run the model, persist band (probability only when
  calibrated) and drivers.
- Enforce idempotency per `(crop, target, geo, horizon, issue_date)`; forced re-runs retain
  both rows.
- Emit metrics and trigger alert evaluation.

### 7.5 Calibration, thresholds and validation

- Assess reliability diagrams, Brier score and log loss on a temporal holdout; spatial
  holdout where data allows.
- Set band thresholds from validated probabilities or a documented expert-approved score.
- Balance false alarms against missed events using the cost of each error.
- Review thresholds when the crop calendar, reporting patterns or calibration change.
- Record approval and expiry for every threshold change.

### 7.6 Risk map and dashboard

- Separate layers: verified reports, unverified reports, modelled risk, coverage and
  boundaries.
- Filters: crop, target, date/horizon, risk band, verification status, admin level.
- Legend, issue time, expiry, horizon, drivers and plain-language explanation always visible.
- Aggregate to the supported admin unit; suppress small counts; no exact farm points.
- Summary panels: new reports, verified cases, forecast distribution, freshness and backlog.
- Use server-side aggregation or vector tiles when data volume requires it.
- Never merge reports and predictions into one undifferentiated heatmap.

### 7.7 Advisory content

- Structure: crop, target, geography, season, language, validity period, author, approver,
  source.
- Content types: scouting, monitoring, sanitation, crop management and escalation.
- Expert review of wording and crop-stage/regional suitability.
- Version history, expiry display and a validator that rejects unapproved or chemical content.
- Route severe or uncertain cases to a named human.

### 7.8 Alerts and delivery

- Trigger only on validated risk threshold + data freshness + minimum coverage.
- Deduplicate repeated signals for the same area/target; severity-specific cooldowns.
- Channels: SMS/WhatsApp (and push only where justified); per-user preference.
- Include area, crop, target, valid period, reason and next action.
- Never label a forecast as a confirmed outbreak.
- Track delivery status, acknowledgement, feedback and opt-out.

### 7.9 Testing

- Feature leakage tests; no-score path; stale weather; boundary version mismatch.
- Map layer separation; small-count suppression; unauthorised precise geometry access.
- Advisory approval/expiry/validator tests; alert dedupe/cooldown/delivery tests.
- Reproducibility test: recompute a stored forecast from its snapshot.

### Deliverables

- Written task/event definition and spatial-unit decision.
- Expert-approved, versioned rules baseline.
- Feature pipeline with immutable snapshots and lineage.
- Forecast generation job with no-score behaviour and idempotency.
- Calibration and temporal/spatial validation report.
- Risk map, coverage panel and dashboard filters.
- Approved advisory content and validator.
- Alert trigger, dedupe, delivery and feedback.

### Exit gate — Gate 4

- A forecast is reproducible from a stored snapshot.
- The no-score path is verified and visible.
- The map never merges reports and predictions; coverage is always visible.
- Band thresholds and actions are approved by an agronomist with a review date.
- Advisory content is approved, versioned and non-chemical.
- Alert policy and escalation owners are approved.

### Not in this phase

- Farm-level risk precision from coarse inputs.
- Using unverified reports as confirmed forecast labels.
- Chemical advice, generative advisory, or outbreak-confirmation language.

**Primary owner:** ML engineer and backend engineer, with the agronomist and product lead.

---

## 8. Phase 5 — Pilot and field validation

**Objective:** measure whether the system improves a real decision in a real season, without
causing harm. Predictions run silently before any farmer-facing alert.

**Entry condition:** Gate 4 met; pilot sites, partners and staffing are ready; the calendar
aligns with the epidemic window.

### 8.1 Pilot setup

- Confirm sites, participant recruitment, consent and the comparison design (matched control,
  stepped-wedge or pre-registered lead-time baseline).
- Freeze the analysis plan and the D5 metric definition before the first observation.
- Confirm data-protection approvals, support contacts and incident routes.
- Prepare field kits, devices, offline testing and enumerator training.

### 8.2 Silent phase

- Generate predictions without showing them to farmers.
- Compare predictions with field observations and verification outcomes.
- Log false alerts, missed events, abstentions and no-score reasons.
- Measure lead time against the existing advisory baseline.
- Do not promote, retune or declare success on training metrics.

### 8.3 Verification operations

- Run the review queue with the agreed SLA, triage rules and workload cap.
- Track backlog, time-to-review, escalation rate and reviewer load.
- Escalate pathologist-only decisions; record evidence and corrections.
- Hold weekly review of queue health and data coverage; adjust staffing, not verification
  standards.

### 8.4 Limited alert phase

- Enable a small, approved set of alerts only after thresholds and response workflows are
  reviewed.
- Name an escalation owner for every alert type.
- Monitor acknowledgement, feedback, complaints and opt-out.
- Pause or roll back an alert type if a safety or trust issue appears.

### 8.5 Usability and comprehension

- Test task completion, comprehension of uncertainty, coverage, stale data and "not a
  diagnosis" wording with farmers and extension workers.
- Test on low-cost devices, low literacy, local language and constrained networks.
- Observe outdoor capture conditions; fix friction before scale-up.
- Verify accessibility: readable text, large targets, colour-independent severity cues.

### 8.6 Monitoring and incident handling

- Dashboards for data freshness, coverage, prediction distribution, abstention, calibration
  drift, sync success, latency, alert delivery and backlog.
- Define alerting thresholds for stale data and model drift.
- Keep an incident log with owner, impact, action and closure.
- Review privacy and security events; confirm no PII leakage.

### 8.7 Evaluation and iteration

- Report lead time, false-alert burden, missed events, review workload, verified-case rate,
  comprehension, repeat use and opt-out.
- Report limitations, sample sizes and negative results honestly.
- Fix defects and recalibrate thresholds only with recorded approval.
- Reject scope creep: new crops/targets wait for the expansion gate.

### Deliverables

- Silent-phase evidence report.
- Limited-alert report with response and safety review.
- Usability and comprehension findings.
- Verification workload and SLA report.
- Monitoring dashboards and incident log.
- Pilot evidence pack and gate recommendation.

### Exit gate — Gate 5

- Silent-phase evidence has been reviewed.
- The alert response workflow is staffed and escalation owners are named.
- No unresolved safety, privacy or trust issue remains.
- The pilot ran through a meaningful part of the epidemic window.
- Findings are documented, including negative results.

### Not in this phase

- Expansion to new crops or districts.
- Yield-impact claims without a suitable study design.
- Operational scale-up without Gate 6.

**Primary owner:** QA/field researcher and field operations lead, with the product lead.

---

## 9. Phase 6 — Rollout and operational readiness

**Objective:** turn a validated pilot into a service someone can operate, monitor, maintain
and fund. If a launch gate is not met, the affected feature stays silent or non-operational.

**Entry condition:** Gate 5 met and a named operating owner exists (D4 resolved).

### 9.1 Operational readiness

- Write runbooks for report flow, review SLA, forecast generation, alert dispatch, data
  ingestion and incident response.
- Name on-call ownership, escalation contacts and support hours.
- Define service levels for availability, sync success, inference latency and review time.
- Document partner responsibilities and the escalation path for field issues.

### 9.2 Infrastructure and recovery

- Harden `prod`: strict access, private storage, backups and monitoring.
- Test database, object-store, model-artefact and configuration restore; document RTO/RPO.
- Use infrastructure-as-code where practical; document and test rollback.
- Apply migrations safely with a forward plan and rollback note.
- Scale image inference separately from API traffic when load requires it.
- Track recurring operating cost separately from one-time development cost.

### 9.3 Monitoring and model maintenance

- Dashboards for data, model and product metrics with alerting on staleness and drift.
- Keep the model registry as the serving authority; require manual approval.
- Retrain only with governed, verified data and the frozen evaluation suite.
- Retain previous model versions for rollback; never auto-promote on training metrics.
- Set a review cadence for calibration, thresholds and advisory expiry.

### 9.4 Security and privacy closeout

- Complete the threat model and a security review/penetration test.
- Confirm encryption, secret management, dependency patching and least-privilege access.
- Verify DPIA actions, retention/deletion jobs, consent audit and export controls.
- Run an incident-response drill and a data-restore drill.
- Confirm no PII or exact farm coordinates in dashboards, exports or logs.

### 9.5 Training and support

- Train extension staff, reviewers, admins and support on workflows and failure paths.
- Publish farmer-facing onboarding and local-language materials for uncertainty and coverage.
- Prepare an FAQ, escalation script and feedback loop.
- Define how corrections and complaints are triaged and closed.

### 9.6 Expansion governance

- Write evidence-based criteria for adding a crop, target or district: data availability,
  expert labels, advisory support, evaluation evidence and operational capacity.
- Require a gate review and recorded decision before expansion.
- Keep the baseline model and previous versions available for fallback.
- Revisit the risk register and budget at each expansion decision.

### 9.7 Launch review

- Complete the Appendix H launch-readiness checklist.
- Review all gates, open risks, audit posture and operational ownership.
- Obtain sign-off from product, agronomy, engineering, security and the operating owner.
- Confirm the rollback and silence plan if a launch gate fails.

### Deliverables

- Operational runbooks and on-call/escalation map.
- `prod` deployment with tested backup and restore.
- Monitoring dashboards, alert rules and maintenance calendar.
- Security/privacy closeout report and drills.
- Training materials and support scripts.
- Expansion policy and signed launch-readiness checklist.
- Post-pilot review and named operating owner.

### Exit gate — Gate 6

- All launch-readiness gates in Appendix H are met and signed.
- An operating owner and support model are named.
- Monitoring, rollback and incident response are live and tested.
- Expansion criteria are approved.
- Any unmet gate leaves the feature silent or non-operational.

### Not in this phase

- Uncontrolled expansion to new crops, targets or districts.
- Removing abstention, coverage or staleness indicators to simplify operations.

**Primary owner:** Product lead and engineering lead, with the operating institution.

---

## 10. Cross-phase workstreams

These run in every phase and are reviewed at every gate.

| Workstream | What it does | Evidence at each gate |
|---|---|---|
| Decisions and change control | Keep D1–D6 and ADRs current; record scope changes | Decision log updated |
| Data acquisition | Collect, permission and label field data | Dataset register and progress report |
| Verification network | Staff review capacity, SLA and escalation | Queue health and backlog |
| Security and privacy | Threat model, DPIA, access review, incident drills | Open-risk list with owners |
| Quality assurance | Test matrix, negative cases, field-device testing | Executed evidence linked to requirements |
| Documentation | Keep specs, tracker and this plan in sync | No stale status or orphan requirement |
| Risk register | Review likelihood, impact, owner and mitigation | Updated `progress-tracker.md` §6 |
| Stakeholder communication | Partner updates, pilot findings, escalation | Meeting notes and decisions |
| Budget and staffing | Track recurring vs one-time cost; re-estimate | Approved envelope or open decision |

---

## 11. Phase-to-specification map

| Phase | Primary specs | Supporting documents |
|---|---|---|
| 0 — Discovery | `../feature-specs/README.md`; `project-overview.md` | `roadmap-and-resources.md`; `update.md` |
| 1 — Data foundation | `05-data-layer.md` | `data-foundation.md`; `appendices.md` D/F; `code-standards.md` |
| 2 — Platform MVP | `01-design-system.md`, `02-reporting-and-capture.md`, `03-auth-and-roles.md`, `04-expert-review.md`, `05-data-layer.md` | `architecture-context.md`; `ui-context.md`; `code-standards.md`; `operations-and-pilot.md` §1 |
| 3 — Image AI | `02-reporting-and-capture.md`, `05-data-layer.md` | `ml-models.md` §§1–6; `data-foundation.md` §§3–6; `appendices.md` B/F |
| 4 — Forecasting | `06-forecast-and-risk-map.md`, `07-advisory-and-alerts.md`, `05-data-layer.md` | `ml-models.md` §§7–12; `data-foundation.md` §§7–8; `appendices.md` A/C/F |
| 5 — Pilot | `02`, `04`, `06`, `07` | `operations-and-pilot.md` §§1–2, 6–7; `appendices.md` F/H |
| 6 — Rollout | All feature specs | `operations-and-pilot.md` §§3–5, 8–9; `roadmap-and-resources.md`; `appendices.md` H |

---

## 12. Gate review checklist (use for every gate)

At each gate, answer these before moving on:

- [ ] The gate's stated evidence exists and is linked from `progress-tracker.md`.
- [ ] Every blocking decision is recorded, or the phase is explicitly paused.
- [ ] Failure paths are tested, not just the happy path.
- [ ] No rule R1–R10 is weakened; any exception is documented and approved.
- [ ] Data permissions and provenance are current.
- [ ] Security, privacy and audit implications are reviewed.
- [ ] The risk register and budget are re-estimated.
- [ ] The next phase's entry list is written and owned.
- [ ] The demo/synthetic data used in any review is labelled `is_demo`.
- [ ] If the gate fails, the affected feature stays silent or non-operational.

---

## 13. Change control

- This plan is subordinate to `AGENTS.md` and the feature specs.
- A change to a gate criterion, phase boundary or sequence is a scope decision: record it in
  `progress-tracker.md` §4 or the ADR log, then update this file.
- Do not mark a phase complete here. Status lives in `progress-tracker.md`.
- Do not add a phase or pull work forward to satisfy a deadline; record the trade-off and the
  affected gates instead.
