# CropSentinel AI — Architecture Compliance Checklist

**Companion to:** `ARCHITECTURE-COMPLIANCE-REPORT.md`
**Baseline verified:** 2026-11-06 — verdict **NOT COMPLIANT**
**Purpose:** Convert the audit findings into an ordered, verifiable work plan.

---

## How to use this checklist

1. Work top to bottom. Do not start a later gate while an earlier gate has unchecked P0 items.
2. **Never tick a box without evidence.** Evidence means a file path, command output, test name, or API response captured in the repository or CI.
3. A box is only tickable when *all* of its "Done when" criteria are met.
4. Status vocabulary stays consistent with the audit:
   `PASS` / `PARTIAL` / `FAIL` / `MISSING` / `NOT VERIFIED`.
5. If an item cannot be verified, leave it unchecked and mark it `NOT VERIFIED` — do not mark it done.
6. Re-run the [final verification matrix](#final-verification-matrix) after each gate.

**Evidence log**

| Gate | Date | Verified by | Command / artefact | Result |
|---|---|---|---|---|
| 0 | | | | |
| 1 | | | | |
| 3 (slice) | 2026-11-06 | ML/backend implementation | `python -m pytest -q`; `python -m compileall -q app` | 103 passed; COMPILE_OK. No model, field data or field result. |
| 5 (machinery slice) | 2026-11-06 | Backend implementation | `python -m pytest`; `python -m compileall -q app` | 187 passed; COMPILE_OK. Service-level advisory/alert tests only; no provider, auth routes, pilot or field result. |

---

## Baseline snapshot (already verified)

Do not re-litigate these; they are the starting point.

- [x] Repository enumerated — documentation + health-only backend scaffold
- [x] `pytest -q` -> **3 passed** (`backend/tests/test_health.py`)
- [x] `python -m compileall -q app` -> **COMPILE_OK**
- [x] OpenAPI paths -> only `/health`, `/v1/health`; `components: None`, `security: None`
- [x] `/v1/admin/users`, `/v1/observations`, `/v1/forecasts`, `/v1/advisories`, `/v1/alerts/preferences` -> **404**
- [x] `Firebase` / `Firestore` / `Cloudinary` / `Kannada` / Kannada Unicode -> **0 matches**
- [x] No `web/`, `mobile/`, `ml/`, `database/`, `deploy/`, `Dockerfile`, CI workflow, or model artefact

---

## Gate 0 — Resolve the architecture conflict (BLOCKING)

Nothing else may start until this gate is closed. Two incompatible designs currently coexist.

### 0.1 Architecture Decision Record

- [ ] Create `docs/adr/0001-target-architecture.md`
  - **Done when:** it states the chosen database, storage, auth provider, frontend stack, role model, language list, model-output semantics, guidance policy, and forecast approach — with rejected alternatives and consequences.
- [ ] Choose the database: **Firestore** (target) *or* **PostgreSQL + PostGIS** (documented) — record the decision
- [ ] Choose image storage: **Cloudinary** (target) *or* **S3-compatible** (documented)
- [ ] Choose the frontend: **single web app**, **web + mobile**, or **Flutter + Next.js**
- [ ] Choose the auth mechanism: phone OTP / email+password / MFA scope
- [ ] Confirm the role list: target (farmer, admin) vs documented (farmer, extension worker, pathologist, admin)
- [ ] Confirm the language list: **English + Kannada**, or documented "one unnamed local language + English"
- [ ] Define confidence semantics: validated numeric probability vs qualitative band + abstention
- [ ] Define severity: model output vs expert-review field
- [ ] Define guidance policy: curated approved content vs LLM-generated — if generated, define validator + approval + audit
- [ ] Define outbreak approach: rules-based nowcast first vs ML model
- [ ] Confirm notification channels: in-app + email + optional SMS, or documented SMS/WhatsApp/push

### 0.2 Resolve blocking product decisions D1–D6

- [ ] D1 — Target crop(s)
- [ ] D2 — Forecast horizon
- [ ] D3 — Who verifies reports
- [ ] D4 — Data/account owner
- [ ] D5 — Primary success metric
- [ ] D6 — Advisory legality / chemical-advice position
  - **Done when:** every decision is recorded in `final/docs-context/progress-tracker.md` §4 with a date and owner.

### 0.3 Reconcile documentation

- [ ] Update `final/PRD.md` — remove false "initial scaffold exists" claim (line 6)
- [ ] Update `final/TRD.md` — remove false "backend/web/mobile scaffold exists" claim (line 6)
- [ ] Update `final/docs-context/architecture-context.md` — one stack only
- [ ] Update `final/feature-specs/03-auth-and-roles.md` — roles, auth mechanism
- [ ] Update `final/feature-specs/05-data-layer.md` — chosen database/storage
- [ ] Update `final/feature-specs/06-forecast-and-risk-map.md` — chosen forecast approach
- [ ] Update `final/feature-specs/07-advisory-and-alerts.md` — guidance policy + channels
- [ ] Update `final/docs-context/progress-tracker.md` — reflect real state, not aspirational state
- [ ] Remove or correct every reference to `final/backend` (actual path is `backend/`)
- [ ] **Done when:** a full-text search finds no contradictory stack, role, or language claims.

### 0.4 Repository hygiene

- [ ] Add `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `dist/`, `build/` to `.gitignore`
- [ ] Delete or rebuild the broken `backend/.venv` (contains only pip; `pyvenv.cfg` points at `final\backend\.venv`)
- [ ] Add a lockfile (`uv.lock`, `poetry.lock`, or `requirements.lock`)
- [ ] Confirm the documented quickstart works from a clean clone on the supported Python version
  - **Done when:** `pip install -r requirements.txt && pytest` succeeds with zero manual steps.

**Gate 0 exit criteria:** one recorded architecture, D1–D6 closed, docs consistent, clean clone installs and tests pass.

---

## Gate 1 — Security and data foundation (P0)

### 1.1 Authentication

- [ ] Farmer registration and login
  - **Done when:** a real credential exchange issues a token; a bad credential returns `401`; a test covers both.
- [ ] Admin/staff login with MFA
  - **Done when:** MFA is enforced for admin roles and cannot be bypassed by a direct API call.
- [ ] Access + refresh token lifecycle (or documented equivalent)
- [ ] Session revocation / logout
- [ ] Device binding or session list (if required by chosen design)
- [ ] Consent capture and versioning
- [ ] Persist auth state and verify it survives a restart

### 1.2 Authorization

- [ ] Role and permission model defined in one place (not scattered conditionals)
- [ ] Deny-by-default route dependencies
  - **Done when:** calling an admin route unauthenticated returns `401`, and with a farmer token returns `403` — not `404`.
- [ ] Object-level ownership checks on every farmer record
- [ ] Role-change events are audited
- [ ] Permission-matrix test covering every role x every protected route
- [ ] OpenAPI now reports real security schemes (`components.securitySchemes` is no longer `None`)

### 1.3 Persistence

- [ ] Schema/collections created for: users, roles, consents, reports/observations, images, diagnoses, advisories, forecasts, alerts, deliveries, audit
- [ ] Migrations (SQL) or index + rules files (Firestore) committed
- [ ] Constraints: uniqueness, required fields, enum validity, referential integrity
- [ ] Append-only rules for diagnoses, forecasts, and audit
- [ ] Seed data is clearly labelled demo data and excluded from operational alerts
- [ ] Backup/restore procedure documented and exercised once
- [ ] Security rules tested against direct client access (Firestore) **or** database authorization tests (SQL)

### 1.4 Image storage

- [ ] Signed upload flow from the client
- [ ] Server-side validation: magic bytes, MIME, max size, dimensions, EXIF stripping
- [ ] Private storage; retrieval only through short-lived signed URLs
- [ ] Image record linked to report and diagnosis
- [ ] Delete endpoint or lifecycle job
- [ ] Orphan cleanup for failed uploads
- [ ] Upload failure returns a typed error and a retry path

### 1.5 Real health checks

- [ ] Separate **liveness** (`/health`) from **readiness** (`/ready`)
- [ ] Readiness checks database, object storage, AI service, and required external providers
- [ ] Readiness returns `503` when a dependency is down
- [ ] Health payload exposes no secrets
- [ ] A test proves readiness fails when a dependency is stubbed to fail

**Gate 1 exit criteria:** an unauthenticated user can reach nothing but health/docs; a farmer cannot read another farmer's data; an admin route rejects non-admins; data and images persist and are retrievable; readiness fails when dependencies fail.

---

## Gate 2 — Farmer vertical slice (P0)

Build one complete path before adding anything else.

- [ ] Farmer dashboard (frontend route + data source)
- [ ] Supported-crop list served by the backend (not hardcoded in the client)
- [ ] Location capture: GPS or manual area selection, with validation
- [ ] Image capture (camera/gallery on mobile, picker/drag-drop on web)
- [ ] Image quality gate: blur, exposure, resolution, plant-present
- [ ] Quality-failure path returns a retake instruction, not a crash
- [ ] Report/observation created with idempotency key
- [ ] AI inference invoked with the uploaded image
- [ ] Result contains: candidate condition(s), confidence presentation, severity, model version, timestamp
- [ ] Abstention path returns a safe "insufficient evidence" outcome
- [ ] Unsupported-crop path returns a safe outcome
- [ ] Verified disease information retrieval
- [ ] Guidance + preventive measures retrieval
- [ ] Result persisted and linked to the image
- [ ] Diagnosis history endpoint (paginated) + UI
- [ ] Case detail view
- [ ] Loading, error, empty, offline, stale, and abstained states implemented
- [ ] End-to-end automated test covers the happy path **and** at least one failure path

**Gate 2 exit criteria:** login → dashboard → crop/location → upload → quality gate → inference → result → guidance → persistence → history works against real components, with a passing E2E test.

---

## Gate 3 — AI model pipeline (P1)

Distinguish these three deliverables; do not let one masquerade as another.

### 3.1 Inference integration

- [ ] Versioned model artefact committed to a registry (not an untracked blob)
- [ ] Class taxonomy / label map
- [ ] Preprocessing parity with training
- [ ] Timeout, retry, and fallback behaviour
- [ ] Model registry records: version, checksum, approval state, retirement
- [ ] Inference latency and abstention rate recorded
- [ ] Model failure produces a safe user-facing outcome
- [ ] Prediction lineage stored (model version + input snapshot reference)

### 3.2 Training pipeline

- [ ] Dataset acquisition with documented permissions and licence
- [ ] Data dictionary and manifest
- [ ] Grouped splits (no image-level leakage) and chronological splits for forecast data
- [ ] Training script + experiment configuration + reproducibility metadata
- [ ] Evaluation report: macro F1, per-class precision/recall, confusion matrix, top-k, calibration
- [ ] Subgroup analysis (crop, region, device, lighting)
- [ ] Model card published
- [ ] Promotion workflow from trained → evaluated → approved → serving

### 3.3 Outbreak risk model

- [ ] Feature definition: weather, verified reports, crop, geography, time
- [ ] Immutable feature snapshots per forecast run
- [ ] Rules-based or ML model with a documented version
- [ ] No-score gate when data is insufficient or stale
- [ ] Risk bands with approved thresholds (not inline numbers)
- [ ] Calibration/backtest report with sample counts
- [ ] Re-run reproducibility: same inputs -> same output

**Gate 3 exit criteria:** predictions come from a versioned artefact; a training run can be reproduced; forecast output is explainable and gated.

### 3.4 Phase 3 image-triage slice — machinery and tests (2026-11-06)

**Entry condition is not met.** Gate 2 is not closed and no field dataset or frozen
test set exists. This slice therefore claims **machinery and automated tests only**.
It does not claim a trained model, an approved operating point, field performance or a
"field-tested" capability. D1 (crop/targets), D3 (verifier capacity) and the D8 floor
values are still required before a model can be fitted or served.

No production crop list, class taxonomy or numeric operating point is committed. The
only policy in the repository is explicitly labelled `synthetic_unit_test` and
`is_demo: true`; the deployment refuses to serve without a real policy and registry.

**Implemented and verified**

- [x] Versioned triage policy: supported crops, class taxonomy, per-class `tau_c`,
      margin, entropy, OOD threshold, quality thresholds and confidence bands. Missing
      or invalid values fail closed; there are no built-in defaults.
      **Evidence:** `backend/app/modules/assessments/policy.py`;
      `backend/tests/fixtures/synthetic_policy.json`.
- [x] Server quality gate with `pass | blurry | dark | overexposed | low_resolution |
      no_plant`, versioned thresholds, all failing flags retained and a stable primary
      reason. A missing metric fails closed.
      **Evidence:** `backend/app/modules/assessments/quality.py`;
      `backend/tests/test_quality_gate.py`.
- [x] D8 decision function: per-class `tau_c`, top-1/top-2 margin, normalised entropy,
      OOD threshold, deterministic reason precedence, and no candidate list on
      abstention.
      **Evidence:** `backend/app/modules/assessments/decision.py`;
      `backend/tests/test_decision.py`.
- [x] Temperature scaling fitted on a dedicated calibration split, with minimum-sample
      refusal, deterministic artefact checksum and ECE/Brier/NLL diagnostics.
      **Evidence:** `backend/app/modules/assessments/calibration.py`;
      `backend/tests/test_calibration.py`.
- [x] Bounded OOD score (`1 - max softmax`), threshold fitted on held-out classes at a
      declared false-accept rate, with unknown-vs-known AUROC and false-accept rate
      reported at the shipped threshold.
      **Evidence:** `backend/app/modules/assessments/ood.py`; `backend/tests/test_ood.py`.
- [x] Model registry: approval state, artefact checksum, retirement, and taxonomy /
      calibration version matching. Unapproved, retired or mismatched models refuse to
      serve.
      **Evidence:** `backend/app/modules/assessments/registry.py`;
      `backend/tests/test_registry.py`.
- [x] Bounded inference boundary: timeout, retry, typed failures, and a safe `failed`
      user outcome when no model is configured or the configuration is invalid.
      **Evidence:** `backend/app/modules/assessments/inference.py`;
      `backend/tests/test_triage_service.py`.
- [x] Append-only prediction record storing model, taxonomy, preprocessing and
      calibration versions, the full threshold set, OOD score, quality gate/version and
      input snapshot reference. Idempotent on `client_assessment_id`; mutation is
      rejected.
      **Evidence:** `backend/app/modules/assessments/store.py`,
      `backend/app/modules/assessments/service.py`;
      `backend/tests/test_triage_service.py`.
- [x] Versioned assessment API: `POST /v1/assessments`,
      `GET /v1/assessments/{id}` and paginated history, with abstention,
      unsupported-crop and safe-failure paths.
      **Evidence:** `backend/app/api/v1/assessments.py`;
      `backend/tests/test_assessments_api.py`.
- [x] Safe explanation layer: every message contains "not a diagnosis", reason-code
      copy and next steps; a validator blocks chemical prescription and diagnostic
      claims.
      **Evidence:** `backend/app/modules/assessments/explanation.py`;
      `backend/tests/test_explanation.py`.
- [x] Evaluation harness: per-class precision/recall, macro F1, confusion matrix,
      top-k accuracy, abstention rate, and calibration only when calibration is
      approved.
      **Evidence:** `backend/app/modules/assessments/evaluation.py`;
      `backend/tests/test_evaluation.py`.
- [x] Evidence run: `python -m pytest -q` -> **103 passed**;
      `python -m compileall -q app` -> **COMPILE_OK** (2026-11-06).

**Deliberately not ticked — no evidence, or blocked on a decision/data**

- [ ] Trained model artefact and approved registry entry. No dataset; D1 open.
- [ ] Preprocessing parity with training. No training pipeline exists.
- [ ] OOD threshold and AUROC/FAR measured on real held-out classes. The code exists;
      no held-out-class data exists.
- [ ] D8 image floor values pre-registered before the frozen test set is opened. Values
      are not measured.
- [ ] Frozen field test set, evaluation report, subgroup breakdowns and robustness
      tests. No field images or labels.
- [ ] `AssessmentCard` rendered in the web/mobile clients. Backend contract only.
- [ ] Inference latency and abstention-rate telemetry aggregated. Per-prediction latency
      is recorded; no metrics endpoint exists.

---

## Gate 4 — Outbreak prediction pipeline (P1)

- [ ] Weather provider client with source timestamp, units, and freshness check
- [ ] Weather ingestion scheduled and idempotent
- [ ] Validation: completeness, stale data, implausible values
- [ ] Verified-report aggregation by geography and time window
- [ ] Unverified reports kept separate from verified counts
- [ ] Spatial aggregation using real geometries and boundary versions
- [ ] Forecast job runs on a schedule and records status
- [ ] Weather data demonstrably changes the risk score (test with two weather fixtures)
- [ ] Verified reports demonstrably change the risk score (test with two report fixtures)
- [ ] No-score state surfaced in API and UI
- [ ] Forecast run history and failure visibility
- [ ] Backlog/coverage metrics exposed

**Gate 4 exit criteria:** a forecast can be reproduced from fixtures, and its inputs provably affect the output.

---

## Gate 5 — Alerts and notifications (P1)

Backend advisory/alert machinery from `final/feature-specs/07-advisory-and-alerts.md` is
implemented and unit-tested. This is **not** pilot evidence: no delivery provider, no
authenticated user routes, no field deployment and no approved production advisory exist.

- [x] Alerts generated from forecasts, **never** from raw reports
  - **Evidence:** `backend/app/modules/alerts/trigger.py` accepts only a
    `ForecastSnapshot`; `tests/test_alert_trigger.py`.
- [x] Gates: coverage, freshness, approved advisory, opt-in
  - **Evidence:** `tests/test_alert_trigger.py::test_every_gate_blocks_the_alert`
    covers demo, paused, inactive, stale, insufficient band, below-minimum band, low
    coverage, missing drivers, missing advisory, expired advisory and no recipients.
- [x] Dedupe key + cooldown + suppression
  - **Evidence:** `tests/test_alert_dispatch.py::test_replaying_the_same_forecast_creates_no_duplicate`,
    `::test_cooldown_suppresses_repeats_but_allows_after_expiry`.
- [x] Alert persisted before dispatch
  - **Evidence:** `tests/test_alert_dispatch.py::test_alert_is_persisted_before_the_provider_is_called`.
- [ ] In-app delivery + inbox. Backend inbox query exists and is tested; no HTTP endpoint
      or client, because Phase 2 authentication/roles do not exist.
- [ ] Email delivery with provider receipt. No email provider, credentials or partner
      channel decision exists.
- [ ] Optional SMS with explicit opt-in. Channel preference exists; no SMS provider or
      gateway is configured.
- [x] Delivery status and failure reason recorded
  - **Evidence:** `tests/test_alert_dispatch.py::test_missing_provider_is_recorded_as_a_failure_not_a_send`,
    `::test_failed_provider_is_retried_and_never_marked_sent`.
- [x] Retry with backoff; no duplicate sends
  - **Evidence:** `::test_retry_backoff_delays_between_attempts`,
    `::test_transient_provider_failure_recovers_on_retry`,
    `::test_replaying_the_same_forecast_creates_no_duplicate`.
- [ ] Alert history and feedback endpoint. Service-level history and owner-scoped
      feedback exist and are tested; no HTTP access because auth/roles are missing.
- [x] Correct-recipient test: only opted-in users in the affected area receive the alert
  - **Evidence:** `tests/test_alert_trigger.py::test_recipient_selection_filters_scope_language_channel_and_opt_out`,
    `tests/test_alert_dispatch.py::test_high_risk_generates_exactly_one_alert_with_recorded_delivery`.
- [x] Pause/kill-switch tested
  - **Evidence:** `tests/test_alert_dispatch.py::test_pause_stops_dispatch_until_resumed`.

**Gate 5 exit criteria:** a test proves high risk -> exactly one alert -> correct recipients -> recorded delivery status; re-running creates no duplicates.

**Met at service level** by `test_high_risk_generates_exactly_one_alert_with_recorded_delivery`
and `test_replaying_the_same_forecast_creates_no_duplicate`. Not met as a Gate 5 exit:
there is no production provider, no pilot site, no approved production advisory and no
field evidence.

---

## Gate 6 — GIS risk map (P1)

- [ ] Map endpoint serving real geometry (vector tiles or GeoJSON)
- [ ] Separate layers: verified reports, unverified reports, modelled risk, coverage, boundaries
- [ ] Report and prediction layers never merged
- [ ] Small-count suppression
- [ ] Boundary version recorded per map response
- [ ] Frontend renders the map from the API, not from hardcoded GeoJSON
- [ ] Empty/loading/error states for the map
- [ ] Map test proves data comes from the API

**Gate 6 exit criteria:** the map displays real persisted data and changes when the data changes.

---

## Gate 7 — Admin management (P1)

- [ ] Admin dashboard
- [ ] User list / create / disable / reset
- [ ] Role assignment + revocation with audit
- [ ] Report management: list, filter, detail, moderation
- [ ] Alert management: list, pause, acknowledge, policy editor
- [ ] Model health: version, latency, abstention rate, last success
- [ ] System health: dependency status from the readiness probe
- [ ] Error and failure visibility
- [ ] Audit log: generation, persistence, search, export
- [ ] Every admin record view is audited with a reason
- [ ] Admin-only access enforced server-side (not just hidden in UI)

**Gate 7 exit criteria:** an admin can see real data, an unaudited admin view is impossible, and a farmer token gets `403` on every admin route.

---

## Gate 8 — Localization (P1)

- [ ] All user-facing strings externalized (no literals in components)
- [ ] English catalogue complete
- [ ] Kannada catalogue complete
- [ ] Language switcher on every user surface
- [ ] Kannada renders correctly (font, shaping, line height)
- [ ] Language choice persists across sessions/devices
- [ ] Backend-generated messages (errors, alerts) localized
- [ ] Missing-translation fallback behaviour defined and tested
- [ ] Automated test detects untranslated keys

**Gate 8 exit criteria:** switching to Kannada leaves no English leaks on any screen; the choice survives logout/login.

---

## Gate 9 — Observability and reliability (P2)

- [ ] Structured JSON logs with request IDs
- [ ] No PII or secrets in logs
- [ ] Metrics: request rate/latency/errors, inference latency, abstention rate, forecast no-score rate, alert delivery failure rate
- [ ] Error tracking with stack traces
- [ ] Tracing across upload → inference → persistence
- [ ] Alerts for model failure, weather staleness, no-score spikes, delivery failures
- [ ] Global exception handler with a consistent error envelope
- [ ] Timeouts and circuit breakers on all external calls
- [ ] Graceful shutdown

**Gate 9 exit criteria:** a forced dependency failure produces a logged, traceable, alertable event that does not crash the app.

---

## Gate 10 — Testing and CI/CD (P2)

- [ ] Unit tests for services and rules
- [ ] Integration tests per module (real DB/emulator, not mocks)
- [ ] Contract tests against the OpenAPI schema
- [ ] Security tests: cross-user, cross-role, unauthenticated, object-level
- [ ] E2E: farmer flow, outbreak flow, admin flow
- [ ] Negative tests: abstention, quality failure, stale weather, no-score, upload failure
- [ ] Model tests: preprocessing parity, golden fixtures, calibration sanity
- [ ] Frontend: build, lint, typecheck
- [ ] Load test: report submission and alert dispatch
- [ ] CI runs all of the above on every PR
- [ ] Coverage threshold enforced
- [ ] A red CI blocks merge

**Gate 10 exit criteria:** a fresh clone can run the full suite locally and in CI; breaking a P0 flow turns CI red.

---

## Gate 11 — Deployment and operations (P2/P3)

- [ ] Container image (or chosen deploy target)
- [ ] Environment-specific configuration (dev/staging/prod)
- [ ] Secrets in a secret manager, not in `.env` in production
- [ ] TLS enforced
- [ ] Rate limiting, OTP throttling, account lockout
- [ ] CSRF strategy if cookies are used
- [ ] Upload malware/type checks
- [ ] Backup schedule + documented RTO/RPO
- [ ] Restore drill executed and recorded
- [ ] Rollback procedure
- [ ] Docs site / API docs restricted or authenticated in production
- [ ] Accessibility and performance budgets

**Gate 11 exit criteria:** a deploy can be rolled back, a backup restored, and a dependency failure survived — each demonstrated once.

---

## Gate 12 — Data governance and compliance (P2)

- [ ] Consent versioning and withdrawal
- [ ] Retention policy per data class
- [ ] User data export
- [ ] User data deletion (including images and derived records)
- [ ] Audit trail immutable and queryable
- [ ] Demo data labelled and excluded from real alerts
- [ ] Privacy notice and language coverage
- [ ] Access-review process for admin roles

**Gate 12 exit criteria:** export, deletion, and audit requests can each be fulfilled and demonstrated.

---

## Final verification matrix

Re-run this after every gate. A row is **PASS** only with fresh evidence.

| # | Check | Expected evidence | Status |
|---|---|---|---|
| 1 | Clean install | fresh clone -> install -> tests pass | MISSING |
| 2 | Tests | full suite green, count recorded | PARTIAL (103 tests; assessment module covered, product E2E missing) |
| 3 | OpenAPI security | `securitySchemes` present | MISSING |
| 4 | Unauthenticated admin route | `401` | MISSING |
| 5 | Farmer cross-tenant read | `403`/`404` with no data leak | MISSING |
| 6 | Upload -> inference | prediction returned with model version | MISSING |
| 7 | Diagnosis persisted | record retrievable in history | MISSING |
| 8 | Image retrievable via signed URL | `200`, URL expires | MISSING |
| 9 | Weather affects risk | two fixtures -> different scores | MISSING |
| 10 | Risk -> alert | one deduped alert, correct recipients | MISSING |
| 11 | Map uses API data | layer changes when records change | MISSING |
| 12 | Admin sees real data | count matches database | MISSING |
| 13 | Audit event written | login / role change / record view present | MISSING |
| 14 | Kannada complete | no English leaks on Kannada UI | MISSING |
| 15 | Readiness degrades | `503` when a dependency is down | MISSING |
| 16 | CI enforces | red test blocks merge | MISSING |

---

## Compliance definition of done

The project may be re-labelled from **NOT COMPLIANT** only when:

- [ ] Gate 0 is fully closed (one architecture, decisions resolved, docs consistent)
- [ ] Gates 1 and 2 pass with automated E2E evidence
- [ ] Gate 3 has either a real trained model **or** an explicitly stated claim of "inference-only, untrained"
- [ ] Gates 4–8 pass
- [ ] Every row in the final verification matrix is **PASS** (no `NOT VERIFIED`, no `PARTIAL`)
- [ ] The audit report is re-run and a new verdict is recorded with a date

Until then, the correct description remains: **documentation-only design with a
health-check scaffold and an unconfigured image-triage decision/serving slice**. No
trained model, field dataset, approved operating point or field result exists, so no
"calibrated, field-tested" claim may be made.
