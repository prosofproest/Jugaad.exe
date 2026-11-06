# CropSentinel AI — Architecture Compliance Checklist

**Companion to:** `ARCHITECTURE-COMPLIANCE-REPORT.md`
**Baseline verified:** 2026-11-06 — verdict **NOT COMPLIANT**
**Checklist reconciled against the repository:** 2026-11-06 — verdict **unchanged: NOT COMPLIANT**
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

> **Work-log rule.** Completed work is recorded in [Work completed since baseline](#work-completed-since-baseline-reconciled-2026-11-06) with its evidence. Ticking a box never changes the audit verdict; only the compliance definition of done and a re-run audit can do that.

**Evidence log**

| Gate | Date | Verified by | Command / artefact | Result |
|---|---|---|---|---|
| 0 | 2026-11-06 | Repository review (checklist reconciliation) | `git log --oneline`; `progress-tracker.md` §4–§5; search for `final/backend` | **Open** — ADRs recorded in the tracker but no `docs/adr/` file; D1–D6 and D9–D12 open; docs largely reconciled |
| 1 | 2026-11-06 | Repository review (checklist reconciliation) | `cd backend && .venv/Scripts/python -m pytest -q`; `cd frontend && npm run typecheck`, `npm run lint`, `npm run build` | **Open** — 216 backend tests pass; web typecheck, lint and build pass; no auth, readiness, domain tables or media |
| 3 (slice) | 2026-11-06 | ML/backend implementation | `python -m pytest -q`; `python -m compileall -q app` | 103 passed; COMPILE_OK. No model, field data or field result. |
| 5 (machinery slice) | 2026-11-06 | Backend implementation | `python -m pytest`; `python -m compileall -q app` | 187 passed; COMPILE_OK. Service-level advisory/alert tests only; no provider, auth routes, pilot or field result. |
| — | 2026-11-06 | Repository review (checklist reconciliation) | `progress-tracker.md` §2 §5.1/§5.7; `TEST-MATRIX.md` FND-01…FND-19 | **Foundation under recorded exception** — scaffold exists; Gate 0 and Gate 1 remain unmet |

---

## Baseline snapshot (historical, pre-scaffold)

Do not re-litigate these; they are the starting point recorded by the audit. Several
lines are now out of date because Phase 2 §5.1 work landed afterwards — use the
work log below for the current state.

- [x] Repository enumerated — documentation + health-only backend scaffold
- [x] `pytest -q` -> **3 passed** (`backend/tests/test_health.py`)
- [x] `python -m compileall -q app` -> **COMPILE_OK**
- [x] OpenAPI paths -> only `/health`, `/v1/health`; `components: None`, `security: None`
- [x] `/v1/admin/users`, `/v1/observations`, `/v1/forecasts`, `/v1/advisories`, `/v1/alerts/preferences` -> **404**
- [x] `Firebase` / `Firestore` / `Cloudinary` / `Kannada` / Kannada Unicode -> **0 matches**
- [x] No `web/`, `mobile/`, `ml/`, `database/`, `deploy/`, `Dockerfile`, CI workflow, or model artefact

---

## Work completed since baseline (reconciled 2026-11-06)

This section records the user's work process against the checklist. A row is added only
where the repository contains the artefact; nothing here closes a gate on its own.

| # | Work completed | Evidence in repository | Checklist items affected |
|---|---|---|---|
| W-01 | Repository structure created for the approved stack: `backend/`, `frontend/`, `mobile/`, `database/`, `deploy/`, `ml/`, `chatbot/`, CI | directory tree; `.github/workflows/ci.yml` | 0.4, Gate 10, Gate 11 |
| W-02 | Architecture decisions recorded (modular monolith, SQLAlchemy/Alembic as schema authority, API-only web, rules-first forecast, ONNX CPU inference, Flutter + SMS/WhatsApp, full-stack scope, chat as a wrapper, `frontend/` naming) | `progress-tracker.md` §5 ADR-001…ADR-009 (ADR-005/006 still *Proposed*; the rest *Accepted*) | 0.1 |
| W-03 | Scientific-integrity decisions D7, D8 and D13 accepted; D1–D6 and D9–D12 remain open with owners and needs-by dates | `progress-tracker.md` §4 | 0.2 (partial) |
| W-04 | Product/technical docs reconciled with the implemented stack; false "no scaffold" claims and stale `final/backend` paths removed | `final/PRD.md` line 6; `final/TRD.md` line 6; search across `final/` for `final/backend` → 0 matches; `progress-tracker.md` changelog | 0.3 |
| W-05 | Backend foundation: app factory, RFC 7807 problem details, request-ID middleware, JSON logging, environment settings, CORS, health route | `backend/app/main.py`, `core/errors.py`, `core/logging.py`, `core/middleware.py`; `tests/test_errors.py`, `test_logging.py`, `test_request_context.py` | 1.5 (liveness only), Gate 9 |
| W-06 | Persistence baseline: SQLAlchemy base/session and Alembic revision `0001_baseline` (no domain tables yet) | `backend/app/db/base.py`, `db/session.py`, `db/migrations/versions/0001_baseline.py`, `alembic.ini` | 1.3 (baseline only) |
| W-07 | Demo conversations API: threads, messages, idempotent send (`Idempotency-Key` must equal `client_message_id`), retry, delete; structured `Assessment` reply with state, reason, candidates, confidence band, `model_version`, `generated_at`, `is_demo` | `backend/app/api/v1/conversations.py`, `modules/conversations/*`; OpenAPI `/v1/conversations` | Phase 2 §5.7 (backend subset) |
| W-08 | Web chat surface: `/chat` list, `/chat/[conversationId]` thread, structured assessment card, metadata-only image composer with drag/drop and 10 MB guard, offline notice, idempotent retry, delete with confirm | `frontend/app/chat/*`, `components/assessment-card.tsx`, `chat-composer.tsx`, `chat-index.tsx`, `chat-thread.tsx`, `message-bubble.tsx`, `sidebar-nav.tsx`, `lib/api.ts` | Phase 2 §5.7 (web subset) |
| W-09 | Honest empty-state surfaces for the other outputs: `/outlook` (no score without inputs) and `/review` (locked until auth/review exist) | `frontend/app/outlook/page.tsx`, `frontend/app/review/page.tsx`; production build emits both routes | R1/R3/R4 evidence; no feature claim |
| W-10 | Design tokens source committed and mirrored into CSS | `design/tokens.json`, `frontend/app/globals.css`; `frontend/README.md` §Design system | Phase 2 §5.1 design foundation |
| W-11 | Flutter shell committed with API client and widget test; **not run locally** | `mobile/pubspec.yaml`, `mobile/lib/*`, `mobile/test/widget_test.dart`; CI mobile job | Gate 10 (Defined, not verified) |
| W-12 | Deploy and CI scaffolding: API/web Dockerfiles, base + dev compose override, dev/staging env templates, CI jobs for backend/web/mobile/compose/image builds | `backend/Dockerfile`, `frontend/Dockerfile`, `deploy/*`, `.github/workflows/ci.yml` | Gate 11 (defined, not run) |
| W-13 | Test evidence refreshed: 216 backend tests pass, ruff clean; web typecheck, lint and production build pass (6 routes) | `cd backend && .venv/Scripts/python -m pytest -q` → 216 passed; `npm run typecheck`, `npm run lint`, `npm run build` → pass; `TEST-MATRIX.md` | Gate 10 (partial) |
| W-14 | Phase-1 data-governance and collection artifacts drafted (dataset register, MoU/licence tracker, consent wording, DPIA, retention/deletion, quarantine, capture protocol, sampling matrix, training, progress tracking, data dictionary) | `database/governance/*`, `database/collection/*`, `database/data-dictionary/*` | Phase 1 (documentation only) |

---

## Gate 0 — Resolve the architecture conflict (BLOCKING)

Nothing else may start until this gate is closed. Two incompatible designs currently coexist.

> **Exception on record (2026-11-06):** the Phase 2 §5.1 foundation and the demo-backed
> web chat surface (§5.7) were built under the explicit instruction recorded in
> `progress-tracker.md` §2. The exception permits foundation-only work; it does **not**
> close Gate 0 or authorise domain features.

### 0.1 Architecture Decision Record

- [ ] Create `docs/adr/0001-target-architecture.md`
  - **Done when:** it states the chosen database, storage, auth provider, frontend stack, role model, language list, model-output semantics, guidance policy, and forecast approach — with rejected alternatives and consequences.
  - **Evidence (2026-11-06):** the decisions exist as ADR-001…ADR-009 in `progress-tracker.md` §5, but no `docs/adr/` directory or ADR file exists. **Not done.**
- [x] Choose the database: **PostgreSQL 16 + PostGIS** (Firestore rejected) — ADR-002; `architecture-context.md` §2; `05-data-layer.md` §2
- [x] Choose image storage: **S3-compatible private bucket** (Cloudinary rejected) — `architecture-context.md` §2; `05-data-layer.md` §8
- [x] Choose the frontend: **Next.js web app + Flutter mobile app** — ADR-007; `architecture-context.md` §2
- [x] Choose the auth mechanism: **phone OTP for farmers; provisioned staff accounts; MFA for pathologist/agronomist/admin** — `03-auth-and-roles.md` §2 (provisioning) and §4.1–§4.2 (flows)
- [x] Confirm the role list: **five roles — farmer, extension worker, pathologist, agronomist, admin** — D13; `03-auth-and-roles.md` §2
- [x] Confirm the language list: **one local language + English** — `ui-context.md` §9; `02-reporting-and-capture.md` §8. The specific local language is still unnamed.
- [x] Define confidence semantics: **qualitative band + abstention; numeric probability only when calibration is approved** — D8; `ml-models.md` §6
- [x] Define severity: **expert-review field recorded with crop-specific criteria** — `PRD.md` §6.2 reviewer actions; `02-reporting-and-capture.md` §4
- [x] Define guidance policy: **curated, expert-approved, versioned, non-chemical content; no LLM** — `07-advisory-and-alerts.md` §1
- [x] Define outbreak approach: **rules-based nowcast first; ML only after verified seasons** — ADR-004; `06-forecast-and-risk-map.md` §2
- [x] Confirm notification channels: **adapter interface for SMS / WhatsApp / push** — `architecture-context.md` §2

### 0.2 Resolve blocking product decisions D1–D6

- [ ] D1 — Target crop(s)
- [ ] D2 — Forecast horizon
- [ ] D3 — Who verifies reports
- [ ] D4 — Data/account owner
- [ ] D5 — Primary success metric
- [ ] D6 — Advisory legality / chemical-advice position
  - **Done when:** every decision is recorded in `final/docs-context/progress-tracker.md` §4 with a date and owner.
  - **Evidence (2026-11-06):** D7, D8 and D13 are accepted in §4. D1–D6 and D9–D12 remain open, each with an owner and a needs-by date, so **0.2 is not closed**.

### 0.3 Reconcile documentation

- [x] Update `final/PRD.md` — false "initial scaffold exists" claim corrected (line 6 now records the Phase 2 scaffold and unverified mobile app)
- [x] Update `final/TRD.md` — false "backend/web/mobile scaffold exists" claim corrected (line 6 now records the real scaffold state)
- [x] Update `final/docs-context/architecture-context.md` — one stack only (PostgreSQL/PostGIS, S3-compatible, Flutter + Next.js)
- [x] Update `final/feature-specs/03-auth-and-roles.md` — five roles and phone-OTP/MFA mechanism recorded
- [x] Update `final/feature-specs/05-data-layer.md` — PostgreSQL/PostGIS and S3-compatible storage recorded
- [x] Update `final/feature-specs/06-forecast-and-risk-map.md` — rules-based nowcast baseline recorded
- [x] Update `final/feature-specs/07-advisory-and-alerts.md` — curated non-chemical guidance policy recorded
- [x] Update `final/docs-context/progress-tracker.md` — reflects the real state, including the Gate-1 exception and the demo chat surface
- [x] Remove or correct every reference to `final/backend` (actual path is `backend/`) — a search across `final/` returns 0 matches; the only remaining hits are this checklist and the audit report describing the correction
- [x] **Done when:** a full-text search finds no contradictory stack, role, or language claims. Open values (D1, D2, D9, D12) are marked open, not contradictory.

### 0.4 Repository hygiene

- [ ] Add `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `dist/`, `build/` to `.gitignore`
  - **Evidence (2026-11-06):** all are present except `dist/`. `.gitignore` covers `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/` and `build/`, but not `dist/`. **Partially done.**
- [x] Delete or rebuild the broken `backend/.venv` — `.venv` now resolves to this repository and runs the suite; `pyvenv.cfg` points at `backend\.venv`
- [ ] Add a lockfile (`uv.lock`, `poetry.lock`, or `requirements.lock`)
  - **Evidence (2026-11-06):** only `frontend/package-lock.json` exists; the backend has no lockfile. **Not done.**
- [ ] Confirm the documented quickstart works from a clean clone on the supported Python version
  - **Done when:** `pip install -r requirements.txt && pytest` succeeds with zero manual steps.
  - **Evidence (2026-11-06):** the local venv runs 216 tests, but a clean-clone install has not been repeated and the backend has no lockfile. **Not verified.**

**Gate 0 exit criteria:** one recorded architecture, D1–D6 closed, docs consistent, clean clone installs and tests pass.

---

## Gate 1 — Security and data foundation (P0)

> **Status (2026-11-06):** open. The repository has a liveness probe, problem-details
> errors, structured logs and an Alembic baseline, but no authentication, authorization,
> domain schema or media pipeline. No data-bearing endpoint is safe to expose.

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
  - **Evidence (2026-11-06):** only `/health` and `/v1/health` exist and both are documented as liveness; no `/ready` route exists.
- [ ] Readiness checks database, object storage, AI service, and required external providers
- [ ] Readiness returns `503` when a dependency is down
- [x] Health payload exposes no secrets — payload is `status`, `service`, `version`, `environment`, `timestamp`; no credentials or connection strings (`backend/app/api/v1/health.py`, `backend/tests/test_health.py`)
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

- [ ] Map endpoint serving real geometry (vector tiles or GeoJSON). GeoJSON layer
      endpoint exists and is tested, but no production geometry store or boundary dataset
      is wired, so it serves synthetic fixtures only.
- [x] Separate layers: verified reports, unverified reports, modelled risk, coverage,
      boundaries
  - **Evidence:** `tests/test_map_layers.py::test_layers_are_separate_and_carry_their_own_properties`,
    `tests/test_map_api.py::test_configured_verified_layer_serves_persisted_features`.
    Layer name is a closed enum; `GET /v1/map/layers/{layer}` serves one layer at a time.
- [x] Report and prediction layers never merged
  - **Evidence:** `tests/test_map_layers.py::test_layers_are_separate_and_carry_their_own_properties`
    (no `band` on report layers, no `verification_status` on model layers),
    `tests/test_map_api.py::test_merged_risk_layer_is_rejected_before_the_service`
    (`risk` is a `422`, never a merged collection).
- [x] Small-count suppression
  - **Evidence:** `tests/test_map_layers.py::test_small_counts_are_suppressed_without_faking_a_zero`,
    `::test_coverage_detail_suppresses_small_counts_field_by_field`. The threshold is
    caller-supplied `MapPolicy.small_count_threshold`; no default is encoded because D9
    is unresolved.
- [x] Boundary version recorded per map response
  - **Evidence:** `tests/test_map_layers.py::test_boundary_version_is_recorded_on_every_layer`,
    `::test_boundary_version_mismatch_refuses_the_layer`;
    `tests/test_map_api.py::test_boundary_version_mismatch_fails_closed`.
- [ ] Frontend renders the map from the API, not from hardcoded GeoJSON. No map client
      exists.
- [ ] Empty/loading/error states for the map. Backend empty and error states are tested
      (`tests/test_map_layers.py::test_empty_verified_layer_never_implies_disease_absence`,
      `tests/test_map_api.py::test_unconfigured_deployment_returns_an_explicit_problem`);
      no client loading/error UI exists.
- [ ] Map test proves data comes from the API. No browser/client test framework exists.

**Gate 6 exit criteria:** the map displays real persisted data and changes when the data changes.

**Met at service/API level** for layer separation, suppression, boundary-version
recording and empty-state wording. Not met as a Gate 6 exit: there is no production
geometry repository, boundary dataset, approved D9 suppression/aggregation values, map
client or end-to-end test. The route returns `map_not_configured` until a deployment
injects persisted geometry and an approved `MapPolicy`.

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

- [x] Structured JSON logs with request IDs — `backend/app/core/logging.py`, `core/middleware.py`; `tests/test_logging.py`, `test_request_context.py`
- [x] No PII or secrets in logs — exception logging keeps only `error_type` (payload text is dropped); `tests/test_logging.py::test_exception_logging_keeps_only_the_error_type`. Conversation text is not logged.
- [ ] Metrics: request rate/latency/errors, inference latency, abstention rate, forecast no-score rate, alert delivery failure rate
- [ ] Error tracking with stack traces
- [ ] Tracing across upload → inference → persistence
- [ ] Alerts for model failure, weather staleness, no-score spikes, delivery failures
- [x] Global exception handler with a consistent error envelope — RFC 7807 `application/problem+json`; `backend/app/core/errors.py`; `tests/test_errors.py`
- [ ] Timeouts and circuit breakers on all external calls
- [ ] Graceful shutdown

**Gate 9 exit criteria:** a forced dependency failure produces a logged, traceable, alertable event that does not crash the app.

> The three ticked rows landed with the §5.1 foundation while Gate 0/1 remain open. They are true on their own but **do not close Gate 9**: metrics, tracing, error tracking and dependency-failure proofs are still missing.

---

## Gate 10 — Testing and CI/CD (P2)

- [ ] Unit tests for services and rules
  - **Evidence (2026-11-06):** 216 tests cover health, the error envelope, request IDs, logging, OpenAPI, conversations, the image-triage decision/quality-gate/OOD/calibration/evaluation/explanation/registry path, advisory/alert dispatch, and the Gate 6 map layers. No real-database integration or module-boundary service test exists. **Not done.**
- [ ] Integration tests per module (real DB/emulator, not mocks)
- [ ] Contract tests against the OpenAPI schema
- [ ] Security tests: cross-user, cross-role, unauthenticated, object-level
- [ ] E2E: farmer flow, outbreak flow, admin flow
- [ ] Negative tests: abstention, quality failure, stale weather, no-score, upload failure
- [ ] Model tests: preprocessing parity, golden fixtures, calibration sanity
- [x] Frontend: build, lint, typecheck — `npm run typecheck`, `npm run lint`, `npm run build` all pass on 2026-11-06; build emits `/`, `/_not-found`, `/chat`, `/chat/[conversationId]`, `/outlook`, `/review`
- [ ] Load test: report submission and alert dispatch
- [ ] CI runs all of the above on every PR
  - **Evidence (2026-11-06):** `.github/workflows/ci.yml` defines backend, web, mobile, compose and image-build jobs, but no CI run is recorded in the repository. **Not verified.**
- [ ] Coverage threshold enforced
- [ ] A red CI blocks merge

**Gate 10 exit criteria:** a fresh clone can run the full suite locally and in CI; breaking a P0 flow turns CI red.

---

## Gate 11 — Deployment and operations (P2/P3)

- [ ] Container image (or chosen deploy target)
  - **Evidence (2026-11-06):** `backend/Dockerfile` and `frontend/Dockerfile` exist and the CI job builds them; local image builds have not been run (no Docker daemon). **Not verified.**
- [ ] Environment-specific configuration (dev/staging/prod)
  - **Evidence (2026-11-06):** dev and staging templates exist (`deploy/.env.example`, `deploy/.env.staging.example`); no production profile is defined.
- [ ] Secrets in a secret manager, not in `.env` in production
- [ ] TLS enforced
- [ ] Rate limiting, OTP throttling, account lockout
- [ ] CSRF strategy if cookies are used
- [ ] Upload malware/type checks
- [ ] Backup schedule + documented RTO/RPO
- [ ] Restore drill executed and recorded
- [ ] Rollback procedure
- [x] Docs site / API docs restricted or authenticated in production — `backend/app/main.py` sets `docs_url`, `redoc_url` and `openapi_url` to `None` when the environment is production (`core/config.py::is_production`); re-verified 2026-11-06 with `APP_ENVIRONMENT=production python -c "from app.main import create_app; ..."` → all three `None`. No automated test asserts this yet.
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
| 1 | Clean install | fresh clone -> install -> tests pass | PARTIAL — scaffold builds, but no backend lockfile and no clean-clone run recorded |
| 2 | Tests | full suite green, count recorded | PARTIAL - 216 backend tests pass (health, conversations, triage/decision, advisories/alerts, map layers); no domain-service integration, real-DB or E2E tests |
| 3 | OpenAPI security | `securitySchemes` present | MISSING — chat and health routes are unauthenticated |
| 4 | Unauthenticated admin route | `401` | MISSING — no admin route exists |
| 5 | Farmer cross-tenant read | `403`/`404` with no data leak | MISSING — no auth or ownership model |
| 6 | Upload -> inference | prediction returned with model version | MISSING — demo chat uses an in-memory labelled demo reply; no upload or model |
| 7 | Diagnosis persisted | record retrievable in history | MISSING — demo messages are in-memory only |
| 8 | Image retrievable via signed URL | `200`, URL expires | MISSING — metadata-only composer; no media storage |
| 9 | Weather affects risk | two fixtures -> different scores | MISSING — no weather ingestion or forecast |
| 10 | Risk -> alert | one deduped alert, correct recipients | MISSING — no alerts module |
| 11 | Map uses API data | layer changes when records change | MISSING - backend layer API exists (Gate 6 slice) but no map client; `/outlook` is an honest empty state |
| 12 | Admin sees real data | count matches database | MISSING — no admin surface or API |
| 13 | Audit event written | login / role change / record view present | MISSING — no audit module |
| 14 | Kannada complete | no English leaks on Kannada UI | MISSING — one local language + English is specified but no locale catalogs exist |
| 15 | Readiness degrades | `503` when a dependency is down | MISSING — only liveness `/health` exists |
| 16 | CI enforces | red test blocks merge | PARTIAL — `.github/workflows/ci.yml` is defined; no CI run or branch-protection evidence recorded |

> Rows 1, 2 and 16 are **PARTIAL** because scaffolding evidence exists, not because the
> audited capability is satisfied. No row may be marked **PASS** until the work-log
> evidence proves the expected result.

---

## Compliance definition of done

The project may be re-labelled from **NOT COMPLIANT** only when:

- [ ] Gate 0 is fully closed (one architecture, decisions resolved, docs consistent)
- [ ] Gates 1 and 2 pass with automated E2E evidence
- [ ] Gate 3 has either a real trained model **or** an explicitly stated claim of "inference-only, untrained"
- [ ] Gates 4–8 pass
- [ ] Every row in the final verification matrix is **PASS** (no `NOT VERIFIED`, no `PARTIAL`)
- [ ] The audit report is re-run and a new verdict is recorded with a date

Until then, the correct description remains: **documentation plus Phase 2 engineering
scaffolding (a demo-backed web chat surface and no real model) — not a compliant
application**. Gate 0 and Gate 1 remain open.
