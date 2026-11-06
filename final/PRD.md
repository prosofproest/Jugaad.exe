# Product Requirements Document (PRD)

**Product:** PS-03 — AI-Based Early Pest and Disease Outbreak Prediction Network
**Document type:** Product Requirements Document
**Version:** 1.1
**Status:** Draft for review — full-stack build: backend API + web + mobile (initial scaffold exists)
**Owner:** Product lead
**Last updated:** 2026-11-06

**Source of truth**

| Concern | Authoritative document |
|---|---|
| Technical design and implementation contracts | `TRD.md` |
| Working rules, hard stops, vocabulary | `docs-context/AGENTS.md` |
| v1 scope and users | `docs-context/project-overview.md` |
| Feature contracts and requirement IDs | `feature-specs/01`–`07` |
| Phase work and gates | `docs-context/phase-plan.md`, `docs-context/progress-tracker.md` |
| Original blueprint / realism audit | `totalcontent.md`, `summary.md`, `update.md` |

This PRD states the product requirements. It does not override the feature specs. If this
document and a feature spec conflict, the feature spec wins; if either conflicts with
`docs-context/AGENTS.md`, `AGENTS.md` wins.

---

## 1. Executive summary

PS-03 is an explainable, offline-tolerant decision-support platform for crop health. It
serves two deliberately separate outputs:

| Output | Question it answers | Unit of prediction |
|---|---|---|
| **Photo assessment** | What might be visible on *this* plant? | One image + crop context |
| **Area outlook** | How likely is *this threat* in *this area* over *this window*? | Crop × target × geography × horizon |

Neither output is a laboratory confirmation. Neither output is a confirmed outbreak. The
platform abstains when evidence is insufficient and shows data coverage wherever risk is
displayed.

v1 is narrow on purpose: one crop, one agro-climatic zone, a small target list, a
rules-based weather-risk model, assistive image triage, extension-worker verification, and
SMS/WhatsApp delivery. Breadth is added only when data, expert labels, approved advisory
content and evaluation evidence exist.

**Delivery surfaces.** v1 is a full-stack product, not a document set. It ships three
coordinated deliverables:

| Surface | Role |
|---|---|
| **Backend API** (FastAPI) | Owns cases, media, inference, review, forecasts, advisories, alerts, audit |
| **Web frontend** (Next.js) | Conversational capture for any signed-in user, expert review portal, district dashboard, admin |
| **Mobile frontend** (Flutter, Android-first) | Conversational capture plus offline field capture, queue and history |

The **chat** is the shared entry point on web and mobile: the user attaches or takes an
image, adds optional context and sends it, and the system replies with a structured photo
assessment. The chat is a wrapper around the assessment pipeline (spec `08`), not a new
model and not a free-form diagnosis bot. The expert portal and district dashboard remain
separate web surfaces; the mobile app remains the offline-first field surface.

**The key product inversion:** lead with the reporting and verification network plus a
rules-based risk model, and treat the image model as assistive triage. This produces a
useful service earlier and avoids overclaiming forecast capability before historical
evidence exists.

---

## 2. Problem and opportunity

### 2.1 Problem

- Farmers lack timely, local, trustworthy information about pest and disease threats.
- Reports are fragmented across farms, extension offices and plant clinics.
- Expert capacity is limited and unevenly distributed.
- Images alone cannot establish a regional outbreak; weather alone cannot confirm disease.
- Existing tools rarely separate *observed evidence* from *modelled risk*, so users
  over-trust weak signals.
- Rural connectivity makes cloud-only workflows unreliable in the field.

### 2.2 Opportunity

A dependable reporting → verification → advisory loop can turn scattered field observations
into useful early awareness. The durable asset is not a single model; it is the verified
local data, the review network and the trust built by honest uncertainty communication.

### 2.3 Product principles

1. **Observe, verify, then model.** Human verification is the backbone, not an afterthought.
2. **Abstain rather than guess.** "No assessment" and "insufficient data" are valid results.
3. **No report is not evidence of absence.** Coverage and surveillance intensity are
   first-class product elements.
4. **Separate the two outputs everywhere.** No shared "risk" number, no merged map layer.
5. **Offline-first.** Saving a field report never depends on a live server round-trip.
6. **No chemical advice.** Advisory content is expert-approved and non-chemical; severe or
   uncertain cases escalate to a human.
7. **Traceability by default.** Every displayed output has a model version, timestamps, a
   snapshot and an audit trail.
8. **Privacy by default.** Approximate location, minimal data, no PII in dashboards.

---

## 3. Goals and non-goals

### 3.1 Product goals

| ID | Goal |
|---|---|
| G-01 | Let a field user capture a crop observation offline and sync it safely once. |
| G-02 | Give extension workers an efficient queue to verify reports with evidence and audit. |
| G-03 | Provide an assistive photo assessment with quality feedback, confidence band, top-3 candidates and abstention. |
| G-04 | Provide an area outlook from an expert-approved, versioned weather-risk model, with an explicit no-score state. |
| G-05 | Keep observed reports, modelled risk and coverage visibly separate on the map. |
| G-06 | Deliver approved non-chemical guidance and alerts through channels farmers actually use. |
| G-07 | Produce trustworthy, permissioned local data that improves both tracks over time. |
| G-08 | Prove value against a pre-registered lead-time metric during a real epidemic season. |

### 3.2 Non-goals for v1

- Universal, all-crop diagnosis.
- Laboratory confirmation or confirmed-outbreak claims.
- Farm-level risk precision from coarse district-level inputs.
- Autonomous chemical selection, dosage or legal-use instructions.
- Generative AI advisory.
- Drone, satellite or IoT analytics.
- Complex spatiotemporal deep learning before data sufficiency.
- Automated model promotion or automated verification.
- Multi-crop, multi-zone or multi-language expansion.

### 3.3 Success definition

v1 succeeds if it demonstrates a functioning reporting → verification → advisory loop and
measurable decision value during the pilot, without a safety, privacy or trust failure.
Model accuracy alone is not success.

---

## 4. Users and stakeholders

### 4.1 Primary personas

| Persona | Core need | Primary surface |
|---|---|---|
| **Smallholder farmer** | Short, local-language, low-data flow with a clear next action; no probability jargon | Mobile, SMS/WhatsApp |
| **Progressive farmer / farm manager** | Crop-cycle history, multiple fields, trends, exportable records | Mobile |
| **Extension worker** | Fast case review, location and crop context, verification capture, approved advice | Mobile + expert portal |
| **Plant pathologist / agronomist** | Original evidence, metadata, alternatives, provenance, label correction, advisory approval | Expert portal |
| **District administrator** | Aggregated map, filters, coverage, verified trends, alert audit | Dashboard |
| **Programme administrator** | Roles, configuration, thresholds, exports, service oversight | Admin console |

### 4.2 v1 roles

Only four roles exist in v1:

| Role | Purpose |
|---|---|
| `farmer` | Submits reports, reads advisories |
| `extension_worker` | Verifies reports, captures on behalf of farmers, shares advisories |
| `pathologist` | Escalation reviewer, taxonomy owner, label correction, advisory approval |
| `admin` | Configuration, users, thresholds, exports, audit |

A user may hold multiple roles, but the active role is explicit in the session. There is no
public self-registration for `extension_worker`, `pathologist` or `admin`. MFA is required
for `pathologist` and `admin`.

### 4.3 Stakeholders

Farmers, extension services, plant clinics, agricultural universities, the operating
institution, the technology team, funders and the data-protection/legal owner.

---

## 5. v1 scope

### 5.1 Defended configuration

```
Crop:         one crop (candidate: potato or tomato — D1 pending)
Zone:         one agro-climatic zone / district cluster
Targets:      3–5 conditions + healthy + abiotic look-alike + unknown
Image AI:     lightweight CNN fine-tuned on field data, quality gate,
              abstention, top-3 candidates
Forecast:     validated agronomic weather-risk model (rules first),
              ML overlay only when data supports it
Product:      Flutter mobile app + Next.js web app, both with conversational
              capture; SMS/WhatsApp alerts; expert portal and dashboard
Verification: extension-worker-first; pathologist for escalations only
Geography:    block/mandal level, never farm level
Timeline:     18 months to limited operational alerts (planning assumption)
Team:         7–9 people
```

### 5.2 In scope

- Account, language preference and consent.
- A backend API consumed by both the web and mobile frontends.
- Conversational capture (chat) on web and mobile: attach/take an image, add optional
  context, send, and receive a structured assessment reply.
- Crop-cycle and approximate-area setup; unknown values allowed.
- Camera/gallery capture, framing guidance, quality feedback and retake.
- Offline save, queued upload, idempotent sync and stale-cache handling.
- Photo assessment with candidates, quality flags, confidence band and abstention.
- Area outlook from a versioned, expert-approved weather-risk model.
- Expert review queue with triage, verification states, evidence notes and audit.
- Separate map layers for verified reports, unverified reports, modelled risk and coverage.
- Approved non-chemical advisory retrieval with version and expiry.
- Alerts over SMS/WhatsApp with deduplication, cooldown and feedback.
- Admin configuration of crops, targets, geographies, thresholds and alert policy.
- Audit, basic monitoring, model registry and export controls.

### 5.3 Out of scope

| Deferred | Cut entirely |
|---|---|
| Spatiotemporal deep learning | Generative AI advisory |
| Drone / satellite analytics | Autonomous chemical guidance |
| On-device inference beyond the quality pre-check | Free-form generative diagnosis chat |
| Multi-language beyond one | Farm-level risk precision |
| Multi-crop | Universal all-crop diagnosis |
| IoT sensors | Confirmed-outbreak claims |
| RBAC beyond the four roles | Public exact farm coordinates |
| Automated retraining | Automated model promotion |
| Group chat / voice notes | Yield-impact claims without a study design |

### 5.4 Expansion rule

Add a crop, target or district only when **all** of the following exist:

1. Permissioned, representative data.
2. Expert labels and an approved taxonomy.
3. Approved local advisory content.
4. Evaluation evidence against the frozen test set.
5. Operational verification capacity.
6. A recorded expansion decision.

Scope grows by evidence, not by request.

---

## 6. Product surfaces and journeys

v1 delivers a **backend API** consumed by two frontends: a **web app** (conversational
capture, expert portal, district dashboard, admin) and a **mobile app** (conversational
capture plus offline field capture). The conversational surface is specified in
`feature-specs/08-conversational-capture.md`.

### 6.1 Farmer / field-staff mobile app

**Screens**

1. **Home** — registered crops, local outlook, report button, recent cases, sync queue,
   alert preferences.
2. **Crop context** — crop, optional variety, growth stage, approximate area, notes.
   Unknown is allowed and does not block submission.
3. **Capture** — framing/lighting/distance guidance, camera or gallery, on-device
   pre-check, retake, best-attempt selection.
4. **Result** — separate `AssessmentCard` and `OutlookCard`, with distinct titles,
   timestamps, model versions, confidence descriptions and next steps.
5. **History** — status, submission time, sync state, verification state, reviewer
   response, corrected label in plain language.
6. **Advisory** — approved guidance with version and expiry; escalation option.

**Journey: submit a symptom report**

```
select crop + approximate area
  → capture image
  → on-device pre-check
  → optional symptom context
  → save observation locally
       ├─ online: upload → server quality gate → photo assessment
       └─ offline: queue → sync later → same flow
  → result cards (assessment and outlook separately)
  → optional expert-review request
  → history shows sync and verification status
```

**Failure paths that must be designed**

- Unsupported crop: explain, show supported list, offer escalation; never force a class.
- Blurry/poor image: specific reason, retake, keep report.
- No connectivity: save locally, queue, sync later; no data loss.
- Stale outlook: visibly stale, last-updated time shown.
- Duplicate submit: idempotency prevents duplicate observations.
- Expired advisory: hide or mark expired; never serve unapproved content.

### 6.2 Expert review portal

**Queue** — filter and sort by area, crop, target, age, status, assignee and urgency.
Default sort: urgency → uncertainty → age, with stable tie-breaking.

**Case detail** — original image(s) at full resolution, metadata, quality flags, candidates,
model version, forecast context at report time, prior reviews and privacy-scoped history.

**Verification states** — confirmed, probable, rejected, duplicate, needs-visit, unresolved.
`confirmed` requires the pathologist role. Every decision writes an immutable review event
and an audit event.

**Evidence** — required by decision type; label correction records previous label, new label,
reviewer and reason; lab confirmation is a separate optional tier.

**Reviewer actions** — claim/unclaim, request a better image or field detail, escalate to
pathologist, record severity using crop-specific criteria, link duplicates.

### 6.3 District dashboard and map

**Layers (never merged)**

1. Verified reports.
2. Unverified reports.
3. Modelled risk (area outlook).
4. Data coverage.
5. Administrative boundaries.

**Filters** — crop, target, date/horizon, risk band, verification status, admin level.

**Always visible** — legend, issue time, expiry/horizon, drivers, coverage and a
plain-language explanation of what the layer represents.

**Privacy** — aggregate to the supported admin unit, suppress small counts, never show exact
farm coordinates to unauthorised roles.

**Summary panels** — new reports, verified cases, forecast distribution, data freshness and
review backlog.

### 6.4 Advisory and alerts

- Advisory content is expert-approved, versioned, non-chemical and time-bounded.
- Action types: scouting, monitoring, sanitation, crop management and escalation.
- Alerts trigger only when a validated threshold, data freshness and minimum coverage all
  pass.
- Alerts are deduplicated per area/target with severity-specific cooldowns.
- Every alert includes area, crop, target, valid period, reason and next action.
- A forecast is never labelled a confirmed outbreak.
- Users can acknowledge, give feedback and change preferences.

### 6.5 Admin console

- Configure crops, targets, geographies and boundary versions.
- Manage users and roles; provision non-farmer accounts.
- Configure thresholds and alert policy with approval records, not inline numbers.
- Review audit events; run controlled exports with purpose, row limits and audit.
- Monitor service health, backlog, coverage and delivery.

### 6.6 Conversational capture — chat (web and mobile)

**Purpose** — the fastest path from "something is wrong with this plant" to a safe,
traceable next step. The chat is available to every signed-in user on both frontends and
wraps the same observation and photo-assessment pipeline used by the structured flow.

**Thread and composer**

- Conversation list: crop/area context, last message, unread state, sync state.
- Composer: image (camera/gallery on mobile; picker/drag-drop on web), optional crop,
  growth stage, approximate area and a short symptom note.
- Sending creates one observation and one message, linked by `client_message_id`.
- Mobile works offline: the message and image are queued locally and sent on reconnect.

**Assistant reply (always structured, never free-form diagnosis)**

| Reply kind | What the user sees | Primary action |
|---|---|---|
| `assessment` | Top candidates, confidence band, model version, generation time, "assistive, not a diagnosis" | Add context, request review, open advisory |
| `abstained` | Specific reason (blur, exposure, no plant, unsupported crop, out of domain) | Retake |
| `unsupported_crop` | Explanation and supported-crop list | Change crop, escalate |
| `queued` | "Will assess when connected" | View queue |
| `failed` | Stable error code and whether retry helps | Retry |
| `review_requested` | Review status and expected response | View case |

**Hard rules**

- The reply never contains a chemical name, dose, mixture, interval or legal-use
  instruction; a server-side validator blocks unsafe content.
- The reply never presents a candidate as a diagnosis or confirmed outbreak.
- Photo assessment and area outlook are never merged; the chat may deep-link to the
  separate outlook card.
- No fabricated reply when the backend is unreachable.
- Every reply carries `model_version`, `generated_at`, calibration status and `is_demo`
  where applicable.
- Requesting expert review from chat creates the same review request and audit event as
  the structured capture flow.

**Failure paths that must be designed** — offline send, interrupted upload, duplicate
retry, blurry image, unsupported crop, model unavailable, expired cached conversation and
conversation deletion.

---

## 7. Functional requirements

The stable requirement IDs live in the feature specs. This section states the product-level
capability and the spec that owns it.

| ID | Capability | Requirement summary | Owner spec |
|---|---|---|---|
| PRD-F-01 | Identity and access | Phone-OTP farmers; provisioned staff accounts; four roles; MFA for privileged roles; deny by default; object-level access | `03-auth-and-roles.md` |
| PRD-F-02 | Consent and privacy | Plain-language consent; versioned and auditable; privacy requests; retention and deletion | `03-auth-and-roles.md` |
| PRD-F-03 | Crop and area context | Supported-crop list; approximate area; optional variety/stage; unknown allowed | `02-reporting-and-capture.md` |
| PRD-F-04 | Capture and quality | Camera/gallery; guidance; on-device pre-check; retake; metadata; compression | `02-reporting-and-capture.md` |
| PRD-F-05 | Offline and sync | Client IDs; idempotency; retry/backoff; resumable upload; visible queue states; no silent drop | `02-reporting-and-capture.md` |
| PRD-F-06 | Photo assessment | Top-3 candidates; quality flags; confidence band; abstention; unsupported-crop path | `02-reporting-and-capture.md`, `05-data-layer.md` |
| PRD-F-07 | Expert review | Queue, triage, claim, evidence, verification states, correction, escalation, audit | `04-expert-review.md` |
| PRD-F-08 | Area outlook | Crop × target × geography × horizon; band; drivers; coverage; issue/expiry; no-score | `06-forecast-and-risk-map.md` |
| PRD-F-09 | Risk map | Separate layers; filters; legend; privacy aggregation; freshness | `06-forecast-and-risk-map.md` |
| PRD-F-10 | Advisory | Approved non-chemical content; version; expiry; language; retrieval | `07-advisory-and-alerts.md` |
| PRD-F-11 | Alerts | Trigger policy; dedupe; cooldown; channels; delivery status; feedback | `07-advisory-and-alerts.md` |
| PRD-F-12 | Admin config | Crops, targets, geographies, thresholds, users, exports, audit | `03`, `05`, `06`, `07` |
| PRD-F-13 | Audit and traceability | Immutable events for reviews, roles, exports, consent, config, predictions | `04`, `05` |
| PRD-F-14 | Data platform | Permissioned ingestion; lineage; snapshots; append-only predictions; registry | `05-data-layer.md` |
| PRD-F-15 | Design system | Shared tokens/components; accessibility; colour-independent severity; wording | `01-design-system.md` |
| PRD-F-16 | Conversational capture | Chat on web and mobile; attach/take image; structured assessment reply; abstention; queue; review request; no free-form diagnosis or chemical advice | `08-conversational-capture.md` |

### 7.1 Mandatory product rules (derived from R1–R10)

- **PRD-R1** — Photo assessment and area outlook are never merged into one number, card,
  endpoint or map layer.
- **PRD-R2** — The system abstains with a reason when quality, crop support or domain
  validity fails.
- **PRD-R3** — Coverage and surveillance intensity are visible wherever risk is displayed;
  zero reports is never shown as disease-free.
- **PRD-R4** — No model output is auto-promoted to verified; only an authorised reviewer can
  set verification status.
- **PRD-R5** — No chemical names, doses, mixtures, intervals or legal-use instructions are
  generated, paraphrased or "improved".
- **PRD-R6** — No fabricated datasets, metrics, partner names or predictions; demo/synthetic
  data is labelled `is_demo` everywhere.
- **PRD-R7** — Every displayed prediction carries model version, source/generation
  timestamps, calibration status, snapshot and issue/expiry where applicable.
- **PRD-R8** — Field capture works offline; cached forecasts are visibly stale after expiry.
- **PRD-R9** — Approximate location by default; no exact farm coordinates or PII to
  unauthorised roles; small counts suppressed.
- **PRD-R10** — Spec before code; scope, schema, API or model changes update the spec and
  tracker in the same change.

**Additional chat rules (spec 08)** — the chat is a wrapper, not a new model:

- The assistant reply is a structured assessment card; no free-form generative diagnosis,
  treatment plan or prescription.
- The server-side content validator rejects chemical vocabulary before an assistant message
  is stored.
- A chat reply may link to the area outlook but must never merge the two outputs.
- Offline, failed and unsupported states show a next action; no fabricated reply.

---

## 8. Non-functional requirements

| ID | Area | Requirement |
|---|---|---|
| PRD-NF-01 | Performance | Capture and form entry stay responsive; inference and forecast latency targets are defined from device/network tests, not guessed |
| PRD-NF-02 | Availability | Provider outages degrade gracefully; stale data is labelled; retries are safe |
| PRD-NF-03 | Offline | Saving and queuing never require a live server; sync is idempotent and resumable |
| PRD-NF-04 | Accessibility | Readable text, large touch targets, colour-independent severity, plain language, one local language |
| PRD-NF-05 | Localisation | All user-facing strings externalised; translation treated as an engineering task |
| PRD-NF-06 | Security | Secure auth/session, RBAC, encryption in transit and at rest, private image storage, upload validation, rate limits, secret protection, dependency patching |
| PRD-NF-07 | Privacy | Data minimisation, consent, approximate location, retention/deletion, no PII in dashboards or exports |
| PRD-NF-08 | Auditability | Append-only audit for sensitive access, reviews, exports, config and model approval |
| PRD-NF-09 | Maintainability | Modular monolith first; versioned APIs; migrations; model registry; documented operations |
| PRD-NF-10 | Scalability | Image inference and forecast generation scale independently when load requires it |
| PRD-NF-11 | Observability | Metrics, logs and alerts cover data freshness, model behaviour, sync, latency and delivery without PII |
| PRD-NF-12 | Reliability | Backups and restore tested; RTO/RPO documented before pilot; rollback tested |
| PRD-NF-13 | Device support | Tested on a low-cost Android device and a constrained network |
| PRD-NF-14 | Testability | Every requirement ID links to at least one test, including negative/failure cases |
| PRD-NF-15 | Chat responsiveness | The chat composer stays responsive while an image uploads; replies show a queued state rather than blocking the UI |
| PRD-NF-16 | Chat safety | Assistant replies are template-rendered and validator-checked; no free-form generative diagnosis or chemical content |

---

## 9. Data requirements

### 9.1 Data families

- Field images and image-quality labels.
- Crop and crop-cycle context.
- Weather observations and forecasts.
- Historical occurrence records.
- Farmer and extension observations.
- Geographic boundaries and environmental context.
- Expert advisories and follow-up outcomes.

### 9.2 Data rules

- Every dataset has an owner, permitted use, update schedule, retention rule and quality
  check.
- Every field used in training or forecasting appears in the data dictionary.
- Images are grouped by farm/field/event for splits; forecast splits are chronological.
- A field-only test set is frozen before model selection.
- Unverified reports are excluded from forecast features as confirmed cases.
- Missing or stale weather produces `insufficient_data`, never imputed values.
- Raw, cleaned and model-ready versions are reproducible and versioned.
- Suspicious records are quarantined, never silently discarded.
- Hard negatives and ambiguous images are retained for abstention training.
- Event date and report date are stored separately.
- Demo/synthetic data is labelled `is_demo` in data, API and UI.

### 9.3 Geospatial and privacy

- Store approximate geometry or admin codes with explicit precision and access control.
- Use PostGIS only where spatial queries require it.
- Aggregate map outputs to the supported admin unit.
- Suppress small counts and restrict exact coordinates.
- Record the boundary version with every derived record.

---

## 10. AI and model requirements

### 10.1 Photo assessment

- **Formulation:** cautious visual triage of visible symptoms, not pathogen identification.
- **Input:** field image plus optional crop and plant-part context.
- **Output:** candidate scores, quality flags, confidence band, abstention state and model
  version.
- **Classes:** supported conditions + healthy + abiotic look-alike + unknown/other.
- **Quality gate:** separate check for blur, resolution, exposure, plant presence and
  distance; failure returns `abstained` with a reason and never blocks submission.
- **Architecture:** start with transfer learning (MobileNet/EfficientNet class); compare
  larger models only when data and compute justify it.
- **Preprocessing:** identical in training and inference; match the pretrained backbone.
- **Evaluation:** macro F1, per-class precision/recall, confusion, top-k, calibration,
  abstention rate, subgroup breakdowns and error analysis on the frozen field test set.
- **Explainability:** Grad-CAM-style outputs are debugging aids, not proof of causal
  reasoning; user-facing wording explains likely visual match, uncertainty, quality and next
  step.
- **Confidence:** show a percentage only when calibration is validated and approved;
  otherwise use qualitative bands.
- **Prohibited:** presenting a ranked class as a diagnosis; unsupported percentage
  confidence; forced classification of unknown inputs.

### 10.2 Area outlook

- **Prediction unit:** target × crop × geography × issue time × horizon.
- **Event definition:** written before feature engineering; different event types are
  separate tasks.
- **Negatives:** verified absence within coverage, never "no report".
- **Model ladder:** documented expert rules → logistic regression → gradient boosting →
  spatiotemporal models only with dense longitudinal data.
- **Features:** weather windows, crop/crop stage, seasonality, lagged verified reports,
  nearby verified reports, prior-season occurrence and coverage.
- **Leakage rule:** every feature must be computable at issue time; persist an immutable
  feature snapshot.
- **No-score gate:** weather freshness, minimum coverage, calendar/stage availability,
  boundary version match and approved model version must all pass.
- **Output:** risk band, optional calibrated probability, drivers, coverage, issue time,
  validity/expiry, model version and lineage.
- **Risk bands:** low, moderate, high, urgent and insufficient_data, each with an operational
  meaning and approved action.
- **Prohibited:** farm-level precision from coarse inputs; treating low risk as disease-free;
  labelling a forecast as a confirmed outbreak.

### 10.3 Model lifecycle

- Every run records commit, data version, architecture, hyperparameters, environment and
  seed.
- The registry is the serving authority; unapproved versions are refused.
- Retraining uses governed, verified data and the frozen evaluation suite.
- Previous versions are retained for rollback.
- No automatic promotion on training metrics.
- Calibration, abstention and thresholds are reviewed when the crop calendar, reporting
  patterns or data distribution change.

### 10.4 Conversational layer

- The chat does **not** introduce a new predictive model. It presents the existing photo
  assessment through a message thread.
- Reply text is rendered from versioned, expert-approved templates; the structured fields
  (candidates, confidence, model version, timestamps) are the source of truth.
- No free-form generative model answers a crop-health question in v1. If an approved LLM is
  added later for phrasing, it may only rephrase approved template content, must pass the
  same chemical-content validator and must not add facts.
- The chat never invokes the forecast engine to answer a photo question, and never merges
  an outlook into an assessment reply.
- Every assistant message stores the assessment reference, template version, model version
  and generation time so the reply can be reproduced and audited.

---

## 11. Safety, responsible AI and compliance

- **Human oversight is mandatory** for ambiguous, severe or high-impact cases.
- **Correction path** exists for users and reviewers; corrections are visible and audited.
- **Fairness** is evaluated across geography, device, season and farmer groups where data
  permits; limitations are reported.
- **No chemical advice** is a liability boundary, not a content gap.
- **No confirmed-outbreak claims** and no laboratory-confirmation language.
- **Privacy:** DPIA before production, consent in plain language, approximate location,
  retention/deletion, no PII in public dashboards.
- **Biosecurity:** aggregate outputs, suppress small counts, restrict precise locations.
- **Adversarial input:** provenance metadata, duplicate detection and spot checks.
- **Transparency:** show coverage, staleness, abstention reasons and model limitations in the
  interface.
- **Chat safety:** the assistant reply is an assistive photo assessment, not a diagnosis;
  it abstains with a reason, offers no chemical advice, and escalates uncertain or severe
  cases to expert review. The server-side validator blocks unsafe content before storage.
- **No impersonation:** the chat never claims to be an agronomist, pathologist or
  laboratory, and never states or implies that a case is confirmed.

---

## 12. Metrics and evaluation

Targets are set with domain experts **after** a baseline is measured. No target numbers are
committed in this PRD.

| Level | Metrics |
|---|---|
| Technical | Image macro F1, per-class recall, calibration, abstention rate; forecast PR-AUC, Brier score, calibration; latency |
| Operational | Report-to-review time, backlog, verified case rate, notification delivery, sync success |
| User | Task completion, comprehension of uncertainty wording, repeat use, alert usefulness, opt-out rate |
| Agricultural | Lead time, field-inspection prioritisation, credible outcome indicators |
| Equity | Performance and adoption by geography, device and user segment |
| Chat | Messages sent, images attached, replies by state (assessed, abstained, unsupported, failed), median reply time, retake rate, review requests from chat, validator rejections |

**Primary metric (D5):** median lead time from first farmer report to verified expert
confirmation, versus the existing advisory baseline. It must be pre-registered before the
pilot.

**Reporting rules**

- Report per-class and per-region breakdowns with sample counts.
- Report performance at the shipped abstention threshold, not the best threshold.
- Never report a single aggregate without its limitations.
- Use "not measured" when data cannot support a number.
- Negative results are legitimate findings and must be reported.

---

## 13. Release plan and gates

Detailed work per phase is in `docs-context/phase-plan.md`; live status is in
`docs-context/progress-tracker.md` §2.

| Phase | Main output | Exit gate |
|---|---|---|
| 0 — Discovery | Decisions D1–D6, partners, crop calendar, pilot protocol | Decisions resolved and recorded |
| 1 — Data foundation | Permissioned datasets, label handbook, schema, ingestion, frozen test set | Permissions + reproducible ingestion + approved handbook |
| 2 — Platform MVP | Backend API, web and mobile clients, chat capture, offline capture, case management, expert review, audit | Offline report synced once, reviewed, audited; chat image → assessment reply works on web and mobile |
| 3 — Image AI | Quality gate, calibrated triage, abstention, ONNX serving, result card | Field-test performance at shipped threshold |
| 4 — Forecasting | Rules baseline, snapshots, no-score path, map, advisories, alerts | Reproducible forecast + verified no-score + approved thresholds |
| 5 — Pilot | Silent phase, limited alerts, usability findings, issue log | Silent evidence reviewed, response staffed |
| 6 — Rollout | Runbooks, monitoring, training, launch checklist, named owner | All launch gates met and signed |

**Sequencing rules**

- A phase does not start until its predecessor's gate is met.
- Long-running data collection and pilot operations continue across gates.
- Any other overlap is a recorded decision.
- If a launch gate is unmet, the affected feature stays silent or non-operational.

---

## 14. Dependencies, assumptions and constraints

### 14.1 Dependencies

- Partner access to field sites, plant-clinic archives and expert reviewers.
- A weather data source with adequate history, resolution and licence.
- A versioned boundary dataset for the pilot geography.
- SMS/WhatsApp provider with per-message cost agreed.
- An owning/paying institution for post-pilot operations.
- Legal review of advisory content.

### 14.2 Assumptions

- One crop and one agro-climatic zone are enough to validate the model.
- Extension-worker verification is viable at the expected volume.
- The pilot can be timed to the epidemic season.
- A rules-based risk model is credible for the selected target.
- Low-cost Android devices and intermittent connectivity are the field baseline.

### 14.3 Constraints

- No chemical advice.
- No confirmed-outbreak or laboratory claims.
- No training on unpermissioned data.
- No real personal or farm-identifying data in demo content.
- No weakening of auth, authorisation or audit for convenience.
- No scope expansion without evidence and a recorded decision.

---

## 15. Risks and mitigations

| Risk | Mitigation |
|---|---|
| No verified historical data in year one | Rules baseline, nowcast, honest limitation statements |
| Public-data model fails in the field | Field test set, domain adaptation, quality gate |
| Verification backlog empties the verified layer | Extension-first triage, SLA, workload caps |
| "No reports" read as "no disease" | Coverage as feature and UI, suppression rules |
| Advisory liability | Non-chemical only, approval workflow, legal review |
| Privacy breach | Approximate location, RBAC, audit, DPIA |
| Pilot misses the epidemic season | Calendar-driven planning |
| Partner withdrawal | Dual partnerships, data ownership agreed upfront |
| False-alert fatigue | Calibration, cooldown, feedback loop |
| Scope creep | Expansion rule, Gate 0 decisions |
| Look-alike symptoms mislabelled | Abiotic class, label handbook, expert review |
| Low-coverage area read as low risk | Coverage gate blocks scored bands; coverage panel |
| Biosecurity inference from public map | Aggregation, suppression, access control |
| Adversarial/borrowed images | Provenance, duplicate detection, spot checks |
| Expert burnout | Workload caps, compensation, triage |

The live register with owners and status is in `docs-context/progress-tracker.md` §6.

---

## 16. Open decisions (blocking)

| ID | Decision | Recommended default | Owner |
|---|---|---|---|
| D1 | Crop + 3–5 targets + zone | Potato late blight, one zone, plus healthy + abiotic + unknown | Product lead + agronomist |
| D2 | Nowcast or 7-day outlook | Nowcast for v1; add outlook after a season of outcomes | Agronomist + ML lead |
| D3 | Verifier, capacity, SLA | Extension-first, pathologist escalation, published SLA and workload cap | Programme lead + partner |
| D4 | Owning/paying institution | Grant/NGO pilot → cooperative or insurer operations | Product lead |
| D5 | Primary outcome metric | Median lead time to verified confirmation, pre-registered | Product lead + evaluator |
| D6 | Legal position on advisory | Non-chemical + escalation, legal review before pilot | Programme lead + legal |

No code that depends on an unresolved decision may start.

---

## 17. Acceptance and launch readiness

The product is not launched as an operational early-warning service until all of the
following are true and signed off.

**Agronomy and data**

- [ ] Crop and target scope approved by local experts.
- [ ] Label handbook and verification workflow active.
- [ ] Data permissions and provenance documented.
- [ ] Weather and boundary data freshness monitored.

**AI and product**

- [ ] Image and forecast models evaluated separately.
- [ ] Calibration and abstention behaviour tested.
- [ ] Risk map distinguishes reports, predictions and coverage.
- [ ] Advisories approved and versioned.
- [ ] Offline queue and stale-data handling tested.
- [ ] Chat image → structured assessment reply works on web and mobile.
- [ ] Chat abstains with a reason on blur, unsupported crop and out-of-domain input.
- [ ] Chat contains no chemical advice; the validator test passes.
- [ ] Chat never merges photo assessment with area outlook.

**Operations and governance**

- [ ] Consent, privacy and retention procedures active.
- [ ] Security review completed.
- [ ] Alert thresholds and escalation owners approved.
- [ ] Monitoring, rollback and incident response ready.
- [ ] Pilot findings reviewed and documented.
- [ ] Named operating owner and support model in place.

If a gate is not met, keep the affected feature in silent or non-operational mode.

---

## 18. Out of scope for this PRD

- Detailed API schemas, database DDL, model architectures and UI token values.
- Implementation sequencing beyond the phase gates.
- Budget figures and staffing names.
- Legal advice or jurisdiction-specific compliance text.

Those belong in the feature specs, `phase-plan.md`, `roadmap-and-resources.md` and legal
review respectively.

---

## 19. Glossary

| Term | Meaning |
|---|---|
| **Photo assessment** | Image-based triage of visible symptoms. Never "diagnosis". |
| **Area outlook** | Forecast risk for crop × target × geography × horizon. Never "outbreak alert". |
| **Abstention / no assessment** | Model declined to answer because evidence is insufficient. |
| **Coverage** | Completeness, freshness and representativeness of inputs for an area. |
| **Verification** | Human decision on a report: confirmed, probable, rejected, duplicate, needs visit, unresolved. |
| **Target** | A supported pest/disease condition on the supported crop list. |
| **Supported** | Explicitly in the approved crop/target/geography list for the current release. |
| **Stale** | Past its validity window; must be visually distinct from fresh data. |
| **No-score** | Explicit `insufficient_data` outlook when coverage, freshness or approval fails. |
| **Demo data** | Synthetic or illustrative data labelled `is_demo`; never presented as real output. |
| **Conversational capture (chat)** | A message thread on web or mobile where a user sends an image and receives a structured photo-assessment reply. A wrapper, not a new model. |

---

## 20. References

| Document | Use |
|---|---|
| `TRD.md` | Technical design: architecture, stack, schema, API, ML, security, testing |
| `docs-context/AGENTS.md` | Working agreement, rules R1–R10, hard stops |
| `docs-context/project-overview.md` | Product context, users, v1 scope, objectives |
| `docs-context/architecture-context.md` | Components, modules, flows, deployment |
| `docs-context/ui-context.md` | Wording, visual rules, screens, states |
| `docs-context/code-standards.md` | Engineering, API, ML and testing conventions |
| `docs-context/data-foundation.md` | Data collection, labelling, cleaning, splits |
| `docs-context/ml-models.md` | Image and forecast model design and evaluation |
| `docs-context/operations-and-pilot.md` | Testing, pilot, deployment, monitoring, team |
| `docs-context/roadmap-and-resources.md` | Roadmap rationale, budget logic, risks |
| `docs-context/phase-plan.md` | Detailed work per phase |
| `docs-context/progress-tracker.md` | Live status, decisions, ADRs, risk register |
| `feature-specs/01`–`08` | Implementation contracts and acceptance criteria |
| `README.md` | Blueprint chapter-to-file map |

---

## 21. Document control

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-11-06 | Initial PRD distilled from the repository operating docs, feature specs and phase plan. No scope, gate or decision changed. |
| 1.1 | 2026-11-06 | Made full-stack delivery explicit (backend + web + mobile) and added conversational capture (chat) on both frontends, with spec `08` and safety rules. No existing gate changed. |

**Review cadence:** update this PRD whenever a decision (D1–D6), scope boundary, success
metric or launch gate changes. Record the change in `docs-context/progress-tracker.md` in
the same change.
