# Gate Completion Summary (Authentication Gate Deferred)

This document tracks the current state of each gate in the **CropSentinel AI** compliance checklist. All items that have been implemented in the repository are marked as done. Items that require further work are listed as pending, with brief next‑step guidance. **Gate 1 – Authentication** is intentionally left incomplete as requested.

---

## Gate 0 – Resolve the architecture conflict (BLOCKING)
- **All items completed** (see original checklist). No further action required.

## Gate 1 – Security and data foundation (P0)
### 1.1 Authentication (DEFERRED)
- ❌ Farmer registration and login – *deferred*
- ❌ Admin/staff login with MFA – *deferred*
- ❌ Access + refresh token lifecycle – *deferred*
- ❌ Session revocation / logout – *deferred*
- ❌ Device binding or session list – *deferred*
- ❌ Consent capture and versioning – *deferred*
- ❌ Persist auth state and verify it survives a restart – *deferred*

### 1.2 Authorization (pending)
- [ ] Role and permission model defined in a single module (`backend/app/core/permissions.py`)
- [ ] Deny‑by‑default route dependencies
- [ ] Object‑level ownership checks on every farmer record
- [ ] Role‑change events audited
- [ ] Permission‑matrix test covering every role × every protected route
- [ ] OpenAPI security schemes populated

### 1.3 Persistence (pending)
- [ ] Create SQL migrations for users, roles, consents, observations, images, diagnoses, advisories, forecasts, alerts, deliveries, audit
- [ ] Add constraints (unique, not‑null, enum, foreign‑key) in models
- [ ] Implement append‑only tables for diagnoses, forecasts, audit
- [ ] Add seed data flag (`is_demo`) and exclude from operational alerts
- [ ] Document and run a backup/restore drill (e.g., `pg_dump`/`pg_restore` script)
- [ ] Add database‑level security tests (attempt direct DB access without credentials)

### 1.4 Image storage (pending)
- [ ] Implement signed upload endpoint (`/v1/media/upload`)
- [ ] Validate magic bytes, MIME type, size, dimensions, strip EXIF
- [ ] Store images privately in Cloudinary, generate short‑lived signed URLs
- [ ] Link image records to observations/diagnoses (FK `observation_id`)
- [ ] Add delete endpoint and orphan‑cleanup job (periodic task)
- [ ] Return typed error on upload failure with retry guidance

### 1.5 Real health checks (pending)
- [ ] Separate liveness (`/health`) and readiness (`/ready`) endpoints
- [ ] Readiness probes check DB, Cloudinary, AI inference service, external weather API
- [ ] Return `503` when any dependency is down
- [ ] Ensure health payload contains no secrets
- [ ] Add a test that forces a dependency failure and asserts readiness 503

## Gate 2 – Farmer vertical slice (P0)
- [ ] Farmer dashboard (frontend route + data source) – *pending UI implementation*
- [ ] Supported‑crop list served by backend (not hardcoded) – *pending endpoint `/v1/crops`*
- [ ] Location capture (GPS/manual) with validation – *pending frontend & backend validation*
- [ ] Image capture (camera/gallery/web picker) – *pending UI component*
- [ ] Image quality gate – *pending `backend/app/modules/media/quality.py` implementation*
- [ ] Quality‑failure retake flow – *pending UI handling*
- [ ] Idempotent report creation – *pending `/v1/observations` idempotency key*
- [ ] AI inference invocation – *pending integration with `inference` service*
- [ ] Result payload with candidate, confidence, severity, version, timestamp – *pending model response mapping*
- [ ] Abstention safe outcome – *pending logic in inference wrapper*
- [ ] Unsupported‑crop safe outcome – *pending guard clause*
- [ ] Verified disease information retrieval – *pending advisory service link*
- [ ] Guidance & preventive measures retrieval – *pending advisory endpoint*
- [ ] Persist result linked to image – *pending DB schema & service update*
- [ ] Diagnosis history endpoint (paginated) – *pending `/v1/diagnoses`*
- [ ] Case detail view – *pending UI page*
- [ ] Loading/error/empty/offline/stale/abstained UI states – *pending component design*
- [ ] End‑to‑end automated test covering happy & one failure path – *pending `tests/e2e/test_gate2.py`*

## Gate 3 – AI model pipeline (P1) — 🟡 **machinery only**
> **Evidence (2026-11-06):** serving machinery exists in
> `backend/app/modules/assessments/` (quality gate, D8 abstention, calibration,
> OOD, registry, inference, evaluation) and the training-side scaffold exists in
> `ml/`. The scaffold is verified by 23 tests on a **clearly-labelled synthetic
> fixture** only. No licensed dataset, image feature extractor, trained image
> model, approved calibration artefact or numeric operating point exists, and a
> synthetic fixture can never be promoted past `evaluated`. Gate 3 is **not met**.

### 3.1 Inference integration
- [ ] Versioned model artefact committed to registry – *registry entry shape and checksum are exercised by the `ml/` scaffold, but no trained image artefact is committed or served*
- [~] Class taxonomy / label map – *synthetic-only label map (`ml/contract/label_map.synthetic.json`) for pipeline tests; production D1a allowlist / D2 taxonomy still open*
- [ ] Preprocessing parity – *only a synthetic feature-vector contract exists (`ml/pest_ml/features.py`); no image extractor or training/serving parity test*
- [ ] Timeout, retry, fallback – *pending wrapper around inference service*
- [~] Registry records (version, checksum, approval, retirement) – *backend registry schema validates `ml/` entries; no DB table, committed model or admin UI*
- [ ] Inference latency & abstention metrics – *pending Prometheus metrics collection*
- [ ] Safe outcome on model failure – *pending error handling in inference client*
- [ ] Prediction lineage stored – *pending audit entry linking model version & input snapshot*

### 3.2 Training pipeline (scaffold only)
- [ ] Dataset acquisition docs & licence – *synthetic fixture licence documented; no field dataset or permissions record*
- [~] Data dictionary & manifest – *fail-closed manifest contract + JSON Schema (`ml/contract/dataset-manifest.schema.json`, `ml/pest_ml/manifest.py`); no field data dictionary*
- [~] Splits (no leakage) scripts – *grouped/stratified seeded splits with leakage checks (`ml/pest_ml/splits.py`); chronological forecast splits not implemented*
- [~] Training script with reproducible config – *deterministic nearest-centroid fixture baseline + checksummed artefact (`ml/pest_ml/train.py`); no image model*
- [~] Evaluation report generation – *reuses `app.modules.assessments.evaluation` for macro F1, per-class metrics, confusion and top-k (`ml/pest_ml/evaluate.py`); calibration stays `null`*
- [ ] Subgroup analysis scripts – *no field data to analyse*
- [~] Model card creation – *generated fixture card + real-model template (`ml/pest_ml/model_card.py`, `ml/model_card.template.md`); no real model card*
- [~] Promotion workflow automation – *fail-closed trained → evaluated → approved gate (`ml/pest_ml/promote.py`); synthetic fixtures stop at `evaluated`*

### 3.3 Outbreak risk model (pending)
- [ ] Feature definition & immutable snapshots
- [ ] Rules‑based / ML model versioning
- [ ] No‑score gate implementation
- [ ] Risk bands & thresholds config
- [ ] Calibration & back‑test report
- [ ] Re‑run reproducibility test

## Gate 4 - Outbreak prediction pipeline (P1) - **partial machinery, not met**

> **Evidence (2026-11-06):** `backend/app/modules/forecast/` now separates a pure
> deterministic rules module (`rules.py`) from the persistence/service layer
> (`service.py`). `backend/tests/test_forecast_rules.py` and
> `backend/tests/test_forecast_service.py` prove on **synthetic fixtures** that
> dry vs wet weather changes the score/band, a verified report changes the score
> with weather held constant, identical inputs reproduce the same result from the
> stored feature snapshot, and missing/stale weather, low coverage, a missing
> calendar or a boundary mismatch return `insufficient_data` with
> `probability = NULL`. The forecast API is mounted (`/v1/forecasts`,
> `/v1/coverage`, `/v1/admin/forecasts/*`, `/v1/map/layers/*`).
>
> Still **open:** a real weather provider and scheduled/idempotent ingestion
> runner; reconciliation of the `database/ingestion` variable names with the
> backend snapshot schema; D8 forecast floors (not pre-registered or met); D9
> coverage/freshness/suppression values (not approved); D1b pilot zone and
> boundary version; and any agronomist-approved operating point or field
> validation. The rule points and band thresholds are demo configuration, not a
> performance claim. Gate 4 is **not met**.

## Gate 5 – Alerts and notifications (P1) – *pending all items*
(Generation from forecasts, gating, dedupe, persistence, delivery channels, status tracking, retry/backoff, history endpoint, recipient testing, pause/kill switch)

## Gate 6 – GIS risk map (P1) – *pending all items*
(API endpoint, vector tiles/GeoJSON, layer separation, small‑count suppression, boundary versioning, frontend integration, UI states, map tests)

## Gate 7 – Admin management (P1) – *pending all items*
(Admin dashboard, user CRUD, role audit, report moderation, alert management, model health view, system health probe, error visibility, audit log search/export, enforced server‑side checks)

## Gate 8 – Localization (P1) – *pending all items*
(Externalised strings, English/Kannada catalogues, language switcher, Kannada rendering, persistence of choice, backend localisation, fallback behaviour, untranslated‑key test)

## Gate 9 – Observability and reliability (P2) – *pending all items*
(JSON logs, PII scrub, metrics, error tracking, tracing, alerts, circuit breakers, graceful shutdown)

## Gate 10 – Testing and CI/CD (P2) – *pending all items*
(Unit, integration, contract, security, E2E, negative, model, frontend build, load test, CI pipeline, coverage thresholds, red‑CI blocking)

## Gate 11 – Deployment and operations (P2/P3) – *pending all items*
(Container image, env‑specific config, secret manager, TLS, rate limiting, OTP throttling, CSRF, malware checks, backup schedule, restore drill, rollback procedure, protected docs, accessibility, performance budgets)

## Gate 12 – Data governance and compliance (P2) – *pending all items*
(Consent versioning/withdrawal, retention policies, user data export/deletion, immutable audit trail, demo data flagging, privacy notice, admin access‑review process)

---

### Next Steps (Authentication Gate Deferred)
1. **Finalize Authorization (Gate 1.2)** – Define a central `permissions.py`, add role‑based dependencies in FastAPI routes, and write the permission‑matrix test suite.
2. **Persist Core Schemas (Gate 1.3)** – Run `alembic revision --autogenerate` to create migrations for all tables listed above, then apply them.
3. **Implement Image Service (Gate 1.4)** – Add Cloudinary SDK calls, signed URL generation, and validation logic.
4. **Expose Liveness/Readiness (Gate 1.5)** – Add `/health` and `/ready` endpoints with dependency checks.
5. **Begin Farmer Vertical Slice (Gate 2)** – Implement the `/v1/crops` endpoint and a minimal dashboard page to verify end‑to‑end flow.
6. **Wire Model Registry (Gate 3)** – Register the newly added `backend/model_registry.py` and store a dummy model artefact for testing.
7. **Iterate through remaining gates** following the same pattern: create the required API, DB schema, and tests, then mark the checklist items as completed.

---

**Evidence log** (to be populated as work progresses):
| Gate | Date | Verified by | Command / artefact | Result |
|------|------|-------------|--------------------|--------|
| 0 | 2026‑11‑06 | **Auto** | `git log -1` | Architecture decisions recorded |
| 1.2 | TBD | | `pytest tests/test_permissions.py` | |
| 1.3 | TBD | | `alembic history` | |
| … | … | … | … | … |

_This file lives at `final/docs-context/gate-progress.md` and should be updated after each completed task._
