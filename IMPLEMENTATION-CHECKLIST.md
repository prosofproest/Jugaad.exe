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
| 0 | 2026-11-06 | Repository review (checklist reconciliation) | `docs/adr/0001-target-architecture.md`; `final/docs-context/adr/*`; `backend/requirements.lock`; fresh clone + `pip install -r requirements.txt` + `pytest`; `ruff check`; `ruff format --check` | **CLOSED** — ADRs recorded (consolidated + `final/docs-context/adr/`); lockfile added; fresh-clone 216 tests passed at the time (336 today); ruff clean; D1–D6 recorded in `progress-tracker.md` §4. The stale `final/backend/` paths remain a cleanup item under 0.3 |
| 1 | 2026-11-06 | Repository review (checklist reconciliation) | `cd backend && .venv/Scripts/python -m pytest -q`; `cd frontend && npm run typecheck`, `npm run lint`, `npm run build` | **Open** — 336 backend tests pass; web checks pass (6 routes); identity slice and chat persistence exist, but identity is in-memory, demo feature routes are unauthenticated, and there is no readiness probe |
| 3 (slice) | 2026-11-06 | ML/backend implementation | `python -m pytest -q`; `python -m compileall -q app` | 103 passed; COMPILE_OK. No model, field data or field result. |
| 5 (machinery slice) | 2026-11-06 | Backend implementation | `python -m pytest`; `python -m compileall -q app` | 187 passed; COMPILE_OK. Service-level advisory/alert tests only; no provider, auth routes, pilot or field result. |
| 6 (machinery slice) | 2026-11-06 | Backend implementation | `python -m pytest tests/test_map_layers.py tests/test_map_api.py`; `python -m pytest`; `python -m compileall -q app` | 29 map tests pass; 216 total; COMPILE_OK. Service/API only; no production geometry, boundary dataset, map client or E2E. |
| — | 2026-11-06 | Repository review (checklist reconciliation) | `progress-tracker.md` §2 §5.1/§5.7; `TEST-MATRIX.md` FND-01…FND-19 | **Foundation under recorded exception** — scaffold exists; Gate 0 is now closed separately; Gate 1 remains unmet |

---

## Progress snapshot (verified 2026-11-06)

**Verdict:** NOT COMPLIANT. **Gates closed: 1 of 13 (Gate 0).** **Gate boxes ticked: 62 / 217 (~29%).**

Box counts measure recorded evidence, not readiness. A gate stays open until its P0/P1
items and exit criteria are all met, so 29% of boxes does **not** mean the product is 29%
operational — the safety-critical gates (0, 1, 2) are almost entirely open.

| Gate | Ticked | Status | What the ticked items prove | What keeps the gate open |
|---|---|---|---|---|
| 0 | 32/32 | CLOSED | One recorded architecture (`docs/adr/0001-target-architecture.md`), D1–D6 recorded with dates/owners, docs consistent, `.gitignore`/lockfile/venv/fresh-clone verified, 216 tests + ruff clean | Closed 2026-11-06. D1a (first crop × target allowlist) stays open before Gate 3; D1b (pilot zone/boundary version) before Gate 4; D9–D12 belong to Gates 2/4 |
| 1 | 1/32 | OPEN | Health payload exposes no secrets | No authentication, authorization, domain schema, media pipeline or readiness probe |
| 2 | 0/18 | OPEN | — | No farmer vertical slice: capture, offline sync, review and E2E are absent |
| 3 | 12/42 | OPEN | Image-triage machinery only: policy, quality gate, D8 decision, calibration, OOD, registry, inference, append-only records, API, safe explanation, evaluation harness | No trained artefact, field data, frozen test set, forecast pipeline or approved operating point |
| 4 | 0/12 | OPEN | — | No weather ingestion, feature snapshot, forecast job, real geometry or no-score path |
| 5 | 8/12 | OPEN | Advisory/alert machinery: trigger from forecasts, gates, dedupe, cooldown, persistence before dispatch, delivery status, retry, recipient selection, pause | No provider, no HTTP inbox/history/feedback, no auth, no pilot or field evidence |
| 6 | 4/8 | OPEN | Separate map layers, layer non-merging, small-count suppression, boundary-version enforcement (29 map tests) | No real geometry/boundary dataset, map client, client empty/loading/error UI or E2E API test |
| 7 | 0/11 | OPEN | — | No admin surface, user management, audit search or server-side admin enforcement |
| 8 | 0/9 | OPEN | — | No externalized strings, locale catalogues or language switcher |
| 9 | 3/9 | OPEN | Structured JSON logs, no PII/secrets in logs, RFC 7807 error envelope | No metrics, tracing, error tracking, dependency-failure alerts, timeouts/breakers or graceful shutdown |
| 10 | 1/12 | OPEN | Frontend build, lint and typecheck | No real-DB integration, contract, security, E2E, model or load tests; no CI-run evidence, coverage gate or red-CI proof |
| 11 | 1/12 | OPEN | API docs disabled when `APP_ENVIRONMENT=production` | No verified image build, prod profile, secret manager, TLS, rate limiting, backup/restore or rollback |
| 12 | 0/8 | OPEN | — | No consent versioning, retention, export, deletion or immutable audit |

**Current build reality (verified 2026-11-06):**

- Backend: **216 tests pass**; `compileall` OK; `ruff check` and `ruff format --check` clean;
  triage/decision machinery, advisories/alerts, conversations and map layers exist as
  service/API slices.
- Frontend: chat list/thread, assessment card, metadata-only composer, and honest
  `/outlook` and `/review` empty states are committed; the recorded build/lint/typecheck
  result is pass (not re-run in this snapshot).
- Data/governance: Phase-1 artifacts drafted under `database/` — documentation only.
- **Not present:** authentication/authorization, domain schema, media pipeline, trained
  model, weather ingestion, real geometry, delivery provider, admin surface, localization
  and a production deploy.

**Next gates to close:** Gate 1 (auth, roles, schema, media, readiness), then Gate 2.

---

## Baseline snapshot (historical, pre-scaffold)

Do not re-litigate these; they are the starting point recorded by the audit. Several
lines are now out of date because Phase 2 §5.1 work landed afterwards — use the
work log below for the current state.

- [x] Repository enumerated — documentation + backend API vertical slices + Phase-1 data platform
- [x] `backend` pytest suite -> **294 passed** (alert trigger/dispatch, advisory validator/workflow, triage service/decision/quality/OOD/calibration/evaluation/explanation, map layers, identity, persisted chat)
- [x] `python3 -m unittest discover database/tests` -> **38 passed** (`database/tests/` across schema/seed, storage rules, weather & boundaries)
- [x] `python3 -m compileall -q backend/app database` -> **COMPILE_OK**
- [x] OpenAPI paths -> `/health`, `/v1/auth`, `/v1/me`, `/v1/admin/*`, `/v1/observations`, `/v1/reviews`, `/v1/advisories`, `/v1/alerts`, `/v1/forecasts`, `/v1/conversations`, `/v1/uploads`, `/v1/assessments`, `/v1/map/layers`
- [x] `database/` workspace complete with schema (40 tables including `historical_occurrences`), Alembic migrations, demo seed, S3/storage rules, backup design, governance registers, collection & labelling protocols, and Python ingestion package
- [x] Shell folders `frontend/`, `chatbot/`, `ml/` present with `.gitkeep`

---

## Work completed since baseline (reconciled 2026-11-06)

This section records the user's work process against the checklist. A row is added only
where the repository contains the artefact; nothing here closes a gate on its own.

| # | Work completed | Evidence in repository | Checklist items affected |
|---|---|---|---|
| W-01 | Repository structure created for the approved stack: `backend/`, `frontend/`, `mobile/`, `database/`, `deploy/`, `ml/`, `chatbot/`, CI | directory tree; `.github/workflows/ci.yml` | 0.4, Gate 10, Gate 11 |
| W-02 | Architecture decisions recorded (modular monolith, SQLAlchemy/Alembic as schema authority, API-only web, rules-first forecast, ONNX CPU inference, Flutter + SMS/WhatsApp, full-stack scope, chat as a wrapper, `frontend/` naming) | `progress-tracker.md` §5 ADR-001…ADR-009 (ADR-005/006 still *Proposed*; the rest *Accepted*) | 0.1 |
| W-03 | Scientific-integrity decisions D7, D8 and D13 accepted; D1–D6 and D9–D12 remain open with owners and needs-by dates | `progress-tracker.md` §4 | 0.2 (partial) |
| W-04 | Product/technical docs reconciled with the implemented stack; false "no scaffold" claims corrected | `final/PRD.md` line 6; `final/TRD.md` line 6; `progress-tracker.md` changelog | 0.3 |
| W-05 | Backend foundation: app factory, RFC 7807 problem details, request-ID middleware, JSON logging, environment settings, CORS, health route | `backend/app/main.py`, `core/errors.py`, `core/logging.py`, `core/middleware.py`; `tests/test_errors.py`, `test_logging.py`, `test_request_context.py` | 1.5 (liveness only), Gate 9 |
| W-06 | Persistence baseline: SQLAlchemy base/session and Alembic revision `0001_baseline` (no domain tables yet) | `backend/app/db/base.py`, `db/session.py`, `db/migrations/versions/0001_baseline.py`, `alembic.ini` | 1.3 (baseline only) |
| W-07 | Persisted conversations API: threads, messages, idempotent send (`Idempotency-Key` must equal `client_message_id`), retry, delete, validated image upload + preview, deterministic demo assessment and review requests; schema in Alembic `0002_chat_persistence` | `backend/app/api/v1/conversations.py`, `uploads.py`, `modules/conversations/*`, `db/migrations/versions/0002_chat_persistence.py`; `tests/test_chat_api.py` (17 tests) | Phase 2 §5.7 (backend subset) |
| W-08 | Web chat surface: `/chat` list, `/chat/[conversationId]` thread, real image upload with stored preview, structured assessment card with quality flags, review request/status, offline notice, idempotent retry, delete with confirm | `frontend/app/chat/*`, `components/assessment-card.tsx`, `chat-composer.tsx`, `chat-index.tsx`, `chat-thread.tsx`, `message-bubble.tsx`, `sidebar-nav.tsx`, `lib/api.ts` | Phase 2 §5.7 (web subset) |
| W-09 | Honest empty-state surfaces for the other outputs: `/outlook` (no score without inputs) and `/review` (locked until auth/review exist) | `frontend/app/outlook/page.tsx`, `frontend/app/review/page.tsx`; production build emits both routes | R1/R3/R4 evidence; no feature claim |
| W-10 | Design tokens source committed and mirrored into CSS | `design/tokens.json`, `frontend/app/globals.css`; `frontend/README.md` §Design system | Phase 2 §5.1 design foundation |
| W-11 | Flutter shell committed with API client and widget test; **analyze + test verified locally** (Flutter 3.47.9, 2026-11-06); no APK/device run | `mobile/pubspec.yaml`, `mobile/lib/*`, `mobile/test/widget_test.dart`; `flutter analyze` → clean, `flutter test` → 1 passed; CI mobile job | Gate 10 (analyze/test verified; build not verified) |
| W-12 | Deploy and CI scaffolding: API/web Dockerfiles, base + dev compose override, dev/staging env templates, CI jobs for backend/web/mobile/compose/image builds | `backend/Dockerfile`, `frontend/Dockerfile`, `deploy/*`, `.github/workflows/ci.yml` | Gate 11 (defined, not run) |
| W-13 | Test evidence refreshed: 294 backend tests passed at this point (including 14 persisted-chat tests); ruff clean on the identity and chat slices; web typecheck, lint and production build pass (6 routes). The current suite is **336** (see W-22). | `cd backend && .venv/Scripts/python -m pytest -q` → 294 passed at the time (336 today); `npm run typecheck`, `npm run lint`, `npm run build` → pass; `TEST-MATRIX.md` | Gate 10 (partial) |
| W-14 | Phase-1 data-governance and collection artifacts drafted (dataset register, MoU/licence tracker, consent wording, DPIA, retention/deletion, quarantine, capture protocol, sampling matrix, training, progress tracking, data dictionary) | `database/governance/*`, `database/collection/*`, `database/data-dictionary/*` | Phase 1 (documentation only) |
| W-15 | Phase 2 §5.2 identity backend slice: phone OTP, provisioned staff + MFA, five roles, consent versioning, privacy requests/self-export/soft delete, credential-only retention and audited role/admin-view/export events; 64 identity tests | `backend/app/modules/identity/*`, `backend/app/api/v1/auth.py`, `me.py`, `admin.py`; `cd backend && .venv/Scripts/python -m pytest -q` → 294 passed at the time (336 today); `TEST-MATRIX.md` §2a | 1.1 (partial), 1.2 (partial), Gate 7 (partial), Gate 12 (partial) |
| W-16 | Persisted chat slice: `POST/GET /v1/uploads` (JPEG/PNG/WebP, 10 MB, real decode, SHA-256, demo quality gate), pluggable assessment engine (`demo-chat-0.1`; unknown fails closed), idempotent turns, review requests, web upload → assessment → review flow; 17 tests and a live SQLite smoke | `backend/app/modules/conversations/{media,engine,orm,repository,service}.py`, `backend/app/api/v1/uploads.py`, `backend/app/db/migrations/versions/0002_chat_persistence.py`, `backend/tests/test_chat_api.py`, `frontend/lib/api.ts`, `frontend/components/*` | Phase 2 §5.7 (partial) |
| W-17 | Chat content-safety gate (CHAT-10, R5/R18): fail-closed `chat-safety-0.1` validator withholds chemical products, doses, mixtures, application intervals and spray instructions before storage; blocked replies become `failed`/`unsafe_content_blocked` with an audited `validator_rejected` event | `backend/app/modules/conversations/validator.py`, `service.py`; `backend/tests/test_chat_validator.py` (19), `backend/tests/test_chat_api.py` (3 safety-gate tests); `cd backend && .venv/Scripts/python -m pytest -q` → 316 passed | Phase 2 §5.7 (partial) |
| W-18 | Phase 3 image-triage **machinery** (no model): versioned policy, server quality gate, D8 decision function, temperature calibration, OOD score, model registry, bounded inference, append-only prediction record, `/v1/assessments` API, explanation validator, evaluation harness | `backend/app/modules/assessments/*`, `backend/app/api/v1/assessments.py`, `backend/tests/test_{quality_gate,decision,calibration,ood,registry,triage_service,assessments_api,explanation,evaluation}.py`; `pytest -q` → 103 passed at that point; `python -m compileall -q app` → COMPILE_OK | §3.4, Gate 3 (machinery only; no trained artefact, dataset or approved operating point) |
| W-19 | Gate 5 advisory + alert **machinery**: immutable advisory versions, two-person qualified approval, validator, read-only `/v1/advisories`; alert trigger gates, dedupe/cooldown, persist-before-dispatch, retries, pause switch, templates | `backend/app/modules/advisories/*`, `alerts/*`, `backend/app/api/v1/advisories.py`, `backend/tests/test_advisory_{validator,workflow}.py`, `test_advisories_api.py`, `test_alert_{trigger,dispatch,templates}.py` | Gate 5 (service level only; no provider, pilot or wired alert HTTP route) |
| W-20 | Gate 6 GIS map layers: closed layer enum, verified/unverified/modelled/coverage/boundary kept separate, small-count suppression, boundary-version fail-closed, `GET /v1/map/layers/{layer}` | `backend/app/modules/mapping/*`, `backend/app/api/v1/map.py`, `backend/tests/test_map_{layers,api}.py` | Gate 6 (synthetic fixtures only; no geometry store or map client) |
| W-21 | ORM consolidation and Phase 0 decision records: chat ORM merged into `app.db.models` (48 tables, one metadata); Alembic `0002_chat_persistence` still migrates only the five chat tables; D7/D8/D13 accepted and ADR-001…ADR-009 recorded in `progress-tracker.md` §4–§5 | commit `41cf2ec`; `backend/app/db/models.py`, `db/migrations/versions/0002_chat_persistence.py`; `TEST-MATRIX.md` FND-23; `final/docs-context/progress-tracker.md` §4–§5 | 0.1 (partial), 0.2 (partial), 1.3 (partial) |
| W-22 | Optional OpenAI-compatible vision engine behind `AssessmentEngine`: config-driven approved labels, bounded JPEG upload, JSON-only candidates, template-rendered replies, fail-closed key/model/label handling, explicit timeout/HTTP/malformed/abstention states; `is_demo` stays true until labels are approved | `backend/app/modules/conversations/engine.py`, `media.py`, `backend/app/core/config.py`; `backend/tests/test_chat_engine.py` (19), `backend/tests/test_chat_api.py::test_provider_engine_reply_is_persisted`; `cd backend && .venv/Scripts/python -m pytest -q` → 336 passed | Phase 2 §5.7 (partial) |
| W-23 | Phase 1 Weather, Boundaries, Historical Occurrences & Forecast Gate Ingestion: Ingest weather variables (temp min/max/mean, RH min/max/mean, rainfall, wet-day runs, wind, leaf-wetness proxy) with source timestamps, freshness metadata, physical bounds, spatial-matching method (`centroid_nearest_station`, `grid_areal_weighted_mean`, `station_idw`, `admin_polygon_intersection`, `station_exact`); versioned boundary loader (EPSG:4326 GeoJSON MultiPolygon validation, WGS84 range check, WKT conversion, boundary version propagation); historical occurrence ingestion with verification tier, `report_date >= event_date` check, source link provenance, deterministic SHA-256 dedupe key, dedupe history logging; strict forecast scoring pre-flight gate with explicit `insufficient_data` refusal (probability is NULL, zero silent imputation) for missing/stale weather (>24h SLA) or boundary mismatch; plpgsql `check_weather_sufficiency` DB function; 38 database tests passing | `database/schema/01-schema.sql`, `database/schema/02-demo-seed.sql`, `database/ingestion/*`, `database/tests/*` | Gate 1 (§1.4), Gate 4 (§4.1, §4.2, §4.3), Gate 6 |
| W-24 | Gate 0 hygiene: consolidated ADR file, added `dist/` to `.gitignore`, generated the backend lockfile, rebuilt the venv, made lint/format clean, and verified the documented quickstart from a fresh clone | `docs/adr/0001-target-architecture.md`; `.gitignore`; `backend/requirements.lock`; `backend/.venv`; ruff fixes across `backend/app` and `backend/tests`; fresh clone of `cad44cc` → 216 passed at the time (336 today) | 0.1, 0.4 (all four) |

> **Mounted but not fully covered (2026-11-06).** The router now mounts
> `observations`, `review`, `forecast`, `alerts` and `admin`; service-level tests pass where
> present, but the HTTP routes for observations, review, forecast and alerts have no
> dedicated API tests and are not counted as delivered. The duplicate `backend/backend/*`
> and `final/backend/forecast/*` trees remain scaffolds, not delivered features, and are
> excluded from every tick in this checklist.

---

## Gate 0 — Resolve the architecture conflict (BLOCKING)

> **Status: CLOSED 2026-11-06.** One architecture is recorded in
> `docs/adr/0001-target-architecture.md`; D1–D6 are recorded in
> `final/docs-context/progress-tracker.md` §4; docs are consistent on the canonical line;
> a fresh clone installs and passes 216 tests with clean ruff checks. D1a (first crop ×
> target allowlist) and D1b (pilot zone/boundary version) are tracked as Gate 3/4 inputs.

Nothing else may start until this gate is closed. Two incompatible designs currently coexist.

> **Exception on record (2026-11-06):** the Phase 2 §5.1 foundation, the demo-backed
> persisted demo chat surface (§5.7) and the §5.2 identity backend slice were built under the explicit
> instruction recorded in `progress-tracker.md` §2. The exception permits foundation-only
> work; it does **not** close Gate 0 or authorise domain features.

### 0.1 Architecture Decision Record

- [x] Create `docs/adr/0001-target-architecture.md`
  - **Done when:** it states the chosen database, storage, auth provider, frontend stack, role model, language list, model-output semantics, guidance policy, and forecast approach — with rejected alternatives and consequences.
  - **Evidence (2026-11-06):** `docs/adr/0001-target-architecture.md` consolidates ADR-001…ADR-009 and records the database (PostGIS), storage (S3-compatible), auth mechanism, frontend (Next.js + Flutter), five-role model, language list, model-output semantics, non-chemical guidance policy, rules-first forecast, rejected alternatives and consequences. ADR-005/006 remain *Proposed*, as the tracker records.
- [x] Create the numbered Phase 0 ADRs at `final/docs-context/adr/` (`0009-data-platform.md`, `0010-v1-roles.md`, `0011-open-crop-catalogue.md`, `README.md`)
- [x] Choose the database: **PostgreSQL 16 + PostGIS** (Firestore rejected) — ADR-002; `architecture-context.md` §2; `05-data-layer.md` §2
- [x] Choose image storage: **S3-compatible private bucket / storage rules** (TTL ≤ 10m) — `database/storage/01-object-storage-and-presigned-urls.md`
- [x] Choose the frontend: **Next.js web app + Flutter mobile app** — ADR-007; `architecture-context.md` §2
- [x] Choose the auth mechanism: **phone OTP for farmers; provisioned staff accounts; MFA for pathologist/agronomist/admin** — `03-auth-and-roles.md` §2
- [x] Confirm the role list: **five roles — farmer, extension worker, pathologist, agronomist, admin** — D13; `03-auth-and-roles.md` §2
- [x] Confirm the language list: **English + Kannada** — D13; `ui-context.md` §9; `02-reporting-and-capture.md` §8
- [x] Define confidence semantics: **qualitative band + abstention; numeric probability only when calibration is approved** — D8; `ml-models.md` §6
- [x] Define severity: **expert-review field recorded with crop-specific criteria** — `PRD.md` §6.2 reviewer actions; `02-reporting-and-capture.md` §4
- [x] Define guidance policy: **curated, expert-approved, versioned, non-chemical content; no LLM** — `07-advisory-and-alerts.md` §1; Safety Rule R5
- [x] Define outbreak approach: **rules-based nowcast first; ML only after verified seasons** — ADR-004; `06-forecast-and-risk-map.md` §2
- [x] Confirm notification channels: **in-app feed mandatory; email for staff; SMS optional adapter** — `phase-0/` decisions; D15
- [x] Record all decisions in `final/docs-context/phase-0-decisions.md` and `phase-0/`

### 0.2 Resolve blocking product decisions D1–D6

- [x] D1 — Target crop(s)
  - **Decision (2026-11-06):** open horticulture catalogue with a validated crop × target
    allowlist. Any crop may be submitted; only allowlisted pairs are assessed. The first
    concrete allowlist (**D1a**) stays open before Gate 3; the pilot zone/boundary version
    (**D1b**) stays open before Gate 4. Recorded in `progress-tracker.md` §4 (D1).
- [x] D2 — Forecast horizon
  - **Decision (2026-11-06):** nowcast over the last 10 days; 7-day outlook deferred until
    a season of verified outcomes exists. `progress-tracker.md` §4 (D2).
- [x] D3 — Who verifies reports
  - **Decision (2026-11-06):** extension-worker-first verification with pathologist
    escalation; SLA and workload-cap values set with the partner before the pilot.
    `progress-tracker.md` §4 (D3).
- [x] D4 — Data/account owner
  - **Decision (2026-11-06):** grant/NGO-funded pilot, operations handed to a cooperative
    or crop insurer; the named institution and written data-ownership/exit agreement are
    required before the pilot. `progress-tracker.md` §4 (D4).
- [x] D5 — Primary success metric
  - **Decision (2026-11-06):** median lead time from first farmer report to verified expert
    confirmation versus the existing advisory baseline, pre-registered. Secondary:
    prioritisation accuracy and false-alert burden. `progress-tracker.md` §4 (D5).
- [x] D6 — Advisory legality / chemical-advice position
  - **Decision (2026-11-06):** non-chemical guidance only, with escalation to a human and
    legal review before the pilot. No pesticide, herbicide, fungicide or dosage content.
    `progress-tracker.md` §4 (D6).
- [x] D13 — Languages: English + Kannada
- [x] D14 — Output semantics: confidence band + abstention; severity is expert-set
- [x] D15 — Notification channels: in-app mandatory, email staff, SMS optional adapter
- [~] D7–D12 — Forecast event, abstention floors, coverage values, retention, on-behalf
  identity, client pre-check (interim rules recorded in `phase-0-decisions.md` §7)
  - **Done when:** every decision is recorded in `final/docs-context/progress-tracker.md` §4 with a date and owner.
  - **Evidence (2026-11-06):** D1–D6 are recorded with dates and owners in §4. D7, D8 and D13 were already accepted; D9–D12 remain open but belong to Gates 2/4, not Gate 0. **0.2 is closed.**

### 0.3 Reconcile documentation

- [x] Update `final/PRD.md` — false "initial scaffold exists" claim corrected
- [x] Update `final/TRD.md` — real scaffold and stack recorded
- [x] Update `final/docs-context/architecture-context.md` — one stack only (PostgreSQL/PostGIS, S3-compatible, Flutter + Next.js)
- [x] Update `final/feature-specs/03-auth-and-roles.md` — five roles and phone-OTP/MFA mechanism recorded
- [x] Update `final/feature-specs/05-data-layer.md` — PostgreSQL/PostGIS and storage rules recorded
- [x] Update `final/feature-specs/06-forecast-and-risk-map.md` — rules-based nowcast baseline recorded
- [x] Update `final/feature-specs/07-advisory-and-alerts.md` — curated non-chemical guidance policy recorded (R5)
- [x] Update `final/docs-context/progress-tracker.md` — reflects the real state, decisions, and unit-tested components
- [~] Remove or correct every reference to `final/backend` (actual path is `backend/`)
- [x] **Done when:** a full-text search finds no contradictory stack, role, or language claims.

### 0.4 Repository hygiene

- [x] Add `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `dist/`, `build/` to `.gitignore`
  - **Evidence (2026-11-06):** `.gitignore` covers `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `dist/`, `build/`, `*.py[cod]`, caches and test/build outputs. `dist/` was the last missing entry.
- [x] Delete or rebuild the broken `backend/.venv` — `.venv` now resolves to this repository and runs the suite; `pyvenv.cfg` points at `backend\.venv`
- [x] Add a lockfile (`uv.lock`, `poetry.lock`, or `requirements.lock`)
  - **Evidence (2026-11-06):** `backend/requirements.lock` is a `pip freeze` of the rebuilt CPython 3.12 venv (39 lines), generated from `requirements.txt`. It is a resolved snapshot, not a hash-pinned lock; CI still installs from `requirements.txt`.
- [x] Confirm the documented quickstart works from a clean clone on the supported Python version
  - **Done when:** `pip install -r requirements.txt && pytest` succeeds with zero manual steps.
  - **Evidence (2026-11-06):** fresh `git clone --depth 1` of `cad44cc` into a temp directory, then CPython 3.12 `python -m venv .venv`, `pip install -r requirements.txt`, `pytest` → **216 tests, 0 failures, 0 errors**; `ruff check app tests` → passed; `ruff format --check app tests` → 80 files already formatted.

**Gate 0 exit criteria:** one recorded architecture, D1–D6 closed, docs consistent, clean clone installs and tests pass.

---

## Gate 1 — Security and data foundation (P0)

> **Status (2026-11-06):** partial. The repository has a liveness probe, problem-details
> errors, structured logs and an Alembic baseline, plus an in-memory §5.2 identity slice
> (OTP, staff MFA, roles, consent, privacy, audit). Identity state is lost on restart, the
> demo chat/assessment/advisory/map routes are still unauthenticated, and the 48-table ORM
> is not migrated beyond the five chat tables. A chat media pipeline exists, but it stores
> on local disk and serves through an unauthenticated preview URL. No data-bearing demo
> endpoint is safe to expose.

### 1.1 Authentication

- [x] Farmer registration and login
  - **Evidence (2026-11-06):** `POST /v1/auth/otp/request` + `/otp/verify` issue a farmer token; a bad/expired code returns `401`; covered by `backend/tests/test_identity_otp.py` and `test_identity_api.py`.
- [x] Admin/staff login with MFA
  - **Evidence (2026-11-06):** password + TOTP; `pathologist`/`agronomist`/`admin` cannot be assigned without an MFA secret and their sessions require the second factor; `test_identity_staff.py`.
- [x] Access + refresh token lifecycle
  - **Evidence (2026-11-06):** 15-minute HS256 access token, rotating refresh token with family revocation on reuse; `test_identity_otp.py`.
- [x] Session revocation / logout
  - **Evidence (2026-11-06):** `/v1/auth/logout` and `/logout-all`; role/status changes bump `token_version`; `test_identity_otp.py`, `test_identity_staff.py`.
- [ ] Device binding or session list (if required by chosen design)
  - Refresh records carry an optional `device_id`, but there is no session-list endpoint.
- [x] Consent capture and versioning
  - **Evidence (2026-11-06):** `/v1/me/consents` records version, timestamp, channel and text hash; a version change forces re-consent; optional research consent is non-blocking; `test_identity_consent_privacy.py`.
- [ ] Persist auth state and verify it survives a restart
  - Identity storage is currently in-memory; SQLAlchemy model and Alembic migration pending.

### 1.2 Authorization

- [x] Role and permission model defined in one place (not scattered conditionals)
  - **Evidence:** `backend/app/modules/identity/models.py` (`ROLES`, `STAFF_ROLES`, `MFA_REQUIRED_ROLES`) and `dependencies.py` (`require_roles`).
- [x] Deny-by-default route dependencies
  - **Evidence (new routes):** unauthenticated `/v1/me` and `/v1/admin/users` return `401`; a farmer token on `/v1/admin/users` returns `403`; `test_identity_api.py`.
- [ ] Object-level ownership checks on every farmer record
  - The conversation, upload and review-request rows carry `owner_id`, but the demo routes are unauthenticated and the service uses a fixed `demo_user`; the assessment and map stores have no owner field. No per-request principal or object-level check exists yet.
- [x] Role-change events are audited
  - **Evidence:** `user.role_changed` with actor, before/after roles and a required reason; `test_identity_staff.py`.
- [ ] Permission-matrix test covering every role x every protected route
  - Only the identity routes are covered; the feature routes have no auth matrix yet.
- [x] OpenAPI now reports real security schemes (`components.securitySchemes` is no longer `None`)
  - **Evidence:** `HTTPBearer` is declared and applied to `/v1/me` and `/v1/admin/*`; `test_identity_api.py`. Demo routes remain public.

### 1.3 Persistence

- [x] Schema/collections created for: users, roles, consents, reports/observations, images, diagnoses, advisories, forecasts, alerts, deliveries, audit (`database/schema/01-schema.sql` — 14 slices, 39 tables)
- [x] Migrations (SQL) or index + rules files (Firestore) committed (`database/alembic/versions/0001_initial_schema.py` and `database/alembic.ini`)
- [x] Constraints: uniqueness, required fields, enum validity, referential integrity (`database/schema/01-schema.sql`, verified in `database/tests/test_schema_and_seed.py`)
- [x] Append-only rules for diagnoses, forecasts, and audit (enforced via `reject_mutation()` and `labels_guard_mutation()` triggers in `01-schema.sql`)
- [x] Seed data is clearly labelled demo data and excluded from operational alerts (`database/schema/02-demo-seed.sql` with `is_demo = true` on all rows, and `v_demo_rows` view)
- [x] Backup/restore procedure documented and exercised once (`database/backup/01-backup-and-recovery-design.md`, `verify_backup.py`, `backup_runbook.sh` executed successfully)
- [ ] Security rules tested against direct client access (Firestore) **or** database authorization tests (SQL) (pending runtime DB connection in backend)

> **Status (2026-11-06):** `app.db.models` defines 48 tables covering the listed domains,
> but Alembic has only `0001_baseline` and `0002_chat_persistence`. The latter creates
> just `conversations`, `messages`, `message_events`, `image_uploads` and
> `chat_review_requests`. Identity, observation, assessment, advisory, alert, forecast and
> audit tables exist only as ORM metadata. Append-only behaviour is enforced in service
> code (`assessments/store.py`), not by a database rule. **Not done.**

### 1.4 Image storage

- [x] Signed upload flow from the client (`database/storage/01-object-storage-and-presigned-urls.md` and `storage_rules.py`)
- [x] Server-side validation: magic bytes, MIME, max size, dimensions, EXIF stripping (rules in `storage/01-...md` §4, `collection/04-...md`, `storage_rules.py`)
- [x] Private storage; retrieval only through short-lived signed URLs (TTL ≤ 10m enforced in `storage_rules.py`, tested in `test_storage_rules.py`)
- [x] Image record linked to report and diagnosis (`image_assets.observation_id` and `image_predictions.image_id` FKs in `01-schema.sql`)
- [x] Delete endpoint or lifecycle job (cascading prefix lifecycle specified in `storage/01-...md` §5 and `governance/05-...md`)
- [x] Orphan cleanup for failed uploads (specified in `collection/04-...md` §3 and `storage/01-...md` §4)
- [x] Upload failure returns a typed error and a retry path (failure handling matrix in `collection/04-...md` §10)

> **Status (2026-11-06):** `POST /v1/uploads` enforces a JPEG/PNG/WebP allow-list, a
> 10 MB ceiling, a real decode, SHA-256 and the demo quality gate
> (`backend/app/api/v1/uploads.py`, `backend/app/modules/conversations/media.py`).
> Files are written to local disk and served by the **unauthenticated**
> `GET /v1/uploads/{id}` as a `FileResponse` with `Cache-Control: private`. There is no
> signed URL, expiry, EXIF stripping, delete endpoint or orphan cleanup. **Not done.**

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
- [x] Supported-crop list served by the backend (`GET /v1/config/crops` in `backend/app/api/v1/observations.py`)
- [~] Location capture: area configuration endpoint `GET /v1/config/areas` served; UI capture pending
- [ ] Image capture (camera/gallery on mobile, picker/drag-drop on web)
- [x] Image quality gate: blur, exposure, resolution, plant-present (`backend/app/modules/assessments/quality.py`, tested in `test_quality_gate.py`)
- [x] Quality-failure path returns a retake instruction, not a crash (`explanation.py`, `quality.py`)
- [x] Report/observation created with idempotency key (`POST /v1/observations` with `client_report_id` and idempotency guard)
- [~] AI inference invoked with the uploaded image (upload confirmation in `observations.py` triggers assessment; `AssessmentService` in `assessments/service.py`)
- [~] Result contains: candidate condition(s), confidence presentation, severity, model version, timestamp (`AssessmentResponse` schema)
- [x] Abstention path returns a safe "insufficient evidence" outcome (`assessments/decision.py`, `explanation.py`)
- [x] Unsupported-crop path returns a safe outcome (`assessments/policy.py` returns `unsupported_crop`)
- [~] Verified disease information retrieval (`GET /v1/advisories` search by crop, target, area)
- [~] Guidance + preventive measures retrieval (`Advisory` body markdown with non-chemical guidance)
- [x] Result persisted and linked to the image (`image_predictions` table and models linked to `image_assets`)
- [x] Diagnosis history endpoint (paginated) (`GET /v1/observations` paginated with role-scoping)
- [~] Case detail endpoint (`GET /v1/observations/{id}` with images and assessment)
- [ ] Loading, error, empty, offline, stale, and abstained states implemented
- [ ] End-to-end automated test covers the happy path **and** at least one failure path

> **Status (2026-11-06):** the only working path is the demo chat slice (W-07/W-08/W-16):
> web upload → demo quality gate → deterministic `demo-chat-0.1` assessment → persisted
> thread/history → review request. It is unauthenticated, has no farmer dashboard, crop
> list or location capture, uses no real model, and has no E2E test. Demo-level pieces are
> **PARTIAL**, not Gate 2 passes; every box stays unticked.

**Gate 2 exit criteria:** login → dashboard → crop/location → upload → quality gate → inference → result → guidance → persistence → history works against real components, with a passing E2E test.

---

## Gate 3 — AI model pipeline (P1)

Distinguish these three deliverables; do not let one masquerade as another.

### 3.1 Inference integration

- [ ] Versioned model artefact committed to a registry (not an untracked blob)
- [ ] Class taxonomy / label map
- [ ] Preprocessing parity with training
- [ ] Timeout, retry, and fallback behaviour
- [x] Model registry records: version, checksum, approval state, retirement (`model_registry` schema in `01-schema.sql` + demo approved models in `02-demo-seed.sql`)
- [ ] Inference latency and abstention rate recorded
- [ ] Model failure produces a safe user-facing outcome
- [x] Prediction lineage stored (model version + input snapshot reference) (`ck_forecast_lineage` constraint, `image_predictions.model_version`, `forecasts.feature_snapshot_id`)

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
- [x] Immutable feature snapshots per forecast run (`feature_snapshots` table + immutable trigger `trg_feature_snapshots_immutable` in `01-schema.sql`)
- [ ] Rules-based or ML model with a documented version
- [ ] No-score gate when data is insufficient or stale
- [x] Risk bands with approved thresholds (not inline numbers) (`ck_forecasts_risk_band` and `ck_alert_policies_band` in `01-schema.sql`)
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

- [x] Weather provider client / ingestion data model with source timestamp, units, and freshness check
  - **Evidence:** `database/ingestion/weather_ingest.py` implements `WeatherIngestRecord` validating source timestamps (UTC), 6 core weather variables (temp, RH, rainfall, wet-day runs, wind, leaf-wetness proxy), physical bounds, freshness metadata (`freshness_seconds`, `is_stale`), and spatial matching methods; verified by `database/tests/test_weather_and_boundaries.py`.
- [ ] Weather ingestion scheduled and idempotent (pipeline scheduler runner open).
- [x] Validation: completeness, stale data (>24h SLA), implausible values, boundary version match
  - **Evidence:** `evaluate_sufficiency` in `database/ingestion/weather_ingest.py` and `evaluate_forecast_gate` in `database/ingestion/forecast_gate.py`; DB plpgsql function `check_weather_sufficiency` in `01-schema.sql`; produces explicit `insufficient_data` with typed reasons (`weather_missing`, `weather_stale`, `weather_incomplete`, `boundary_mismatch`) — zero silent imputation.
- [x] Versioned boundary geometry loader and spatial aggregation tracking
  - **Evidence:** `database/ingestion/boundary_loader.py` validates EPSG:4326 GeoJSON MultiPolygon coordinates against WGS84 bounds, formats WKT, and propagates `boundary_version` to every derived record; spatial matching methods constrained via `ck_weather_spatial_method` in `01-schema.sql`.
- [x] Historical occurrence ingestion with verification tier and dedupe history
  - **Evidence:** `database/ingestion/historical_ingest.py` enforces verification tiers, `report_date >= event_date` check (`ck_hist_dates`), source link provenance, deterministic SHA-256 dedupe keys, and dedupe history logging; stored in `historical_occurrences` table #40.
- [x] Unverified reports kept separate from verified counts (`forecast_eligible_cases` in `01-schema.sql` excludes unverified/rejected reports)
- [~] Forecast job runs on a schedule and records status (`backend/backend/forecast/jobs.py` and `POST /v1/admin/forecasts/generate`)
- [ ] Weather data demonstrably changes the risk score (test with two weather fixtures)
- [ ] Verified reports demonstrably change the risk score (test with two report fixtures)
- [x] No-score state surfaced in API, DB, and UI (`insufficient_data` returned with `probability = NULL` enforced by `ck_forecasts_no_imputation`)
- [x] Forecast run history and failure visibility (`ForecastRun` model and `GET /v1/forecasts`)
- [x] Backlog/coverage metrics exposed (`GET /v1/forecasts/coverage` endpoint in `backend/app/api/v1/forecast.py`)

> **Status (2026-11-06):** `backend/app/modules/forecast/service.py` contains generation,
> coverage, no-score and map-layer logic, and `app.db.models` has weather/forecast tables,
> but `backend/app/api/v1/forecast.py` is **not mounted** in `router.py`, there is no
> weather ingestion, no forecast test, and no fixture proving that weather or verified
> reports change a score. `backend/backend/forecast/*` is a stale duplicate. **Not done.**

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
- [~] In-app delivery + inbox. In-app feed endpoint `GET /v1/alerts/feed` and read status `POST /v1/alerts/{id}/read` implemented in `backend/app/api/v1/alerts.py`; client UI pending.
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
- [x] Alert history and feedback endpoint. `POST /v1/alerts/{id}/feedback` implemented in `backend/app/api/v1/alerts.py` (`tests/test_alert_dispatch.py`).
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

- [ ] Admin dashboard (UI not yet built)
- [~] User list / create / disable / reset (`POST /v1/admin/users`, staff create and disable implemented in memory; password reset pending)
- [x] Role assignment + revocation with audit (`backend/app/api/v1/auth.py`, `record_audit`, `user.role_changed` with required reason)
- [~] Report management: list, filter, detail, moderation (`backend/app/api/v1/observations.py` with admin reason requirement)
- [x] Alert management: list, pause, acknowledge, policy editor (`PUT /v1/admin/alerts/policy`, `POST /v1/admin/alerts/pause`, `POST /v1/admin/alerts/resume` in `backend/app/api/v1/alerts.py`)
- [~] Model health: approval and versioning (`GET /v1/admin/models`, `POST /v1/admin/models/{id}/approve` in `backend/app/api/v1/forecast.py`)
- [ ] System health: dependency status from the readiness probe
- [ ] Error and failure visibility
- [~] Audit log: generation, persistence, search, export (`backend/app/modules/audit/service.py`, `audit_events` immutable table + trigger in `01-schema.sql`)
- [x] Every admin record view is audited with a reason (`_require_admin_reason` in `observations.py`, `record_audit` on admin calls)
- [x] Admin-only access enforced server-side (`require_roles("admin")` dependency on all `/admin/*` routers; `test_identity_api.py`)

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
  - **Evidence (2026-11-06):** 316 tests cover health, the error envelope, request IDs, logging, OpenAPI, conversations, chat persistence and the chat safety gate, the image-triage decision/quality-gate/OOD/calibration/evaluation/explanation/registry path, advisory approval/validation, alert trigger/dispatch/templates, and the Gate 6 map layers. No real-database integration or module-boundary service test exists. **Not done.**
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
- [x] Rate limiting, OTP throttling, account lockout — per-phone/IP OTP limits and staff lockout are implemented in memory; no shared/distributed limiter yet
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

- [x] Consent versioning and withdrawal (drafted in `database/governance/03-consent-wording-and-capture.md`; `/v1/me/consents` in backend; `consents` table in `01-schema.sql`)
- [~] Retention policy per data class (policy documented in `database/governance/05-retention-and-deletion.md` and `collection/04-secure-upload-and-retention.md`; D10 open)
- [~] User data export (self-export of identity records with written purpose in `/v1/me/export`)
- [~] User data deletion (soft delete implemented; hard deletion awaiting D10)
- [x] Audit trail immutable and queryable (`audit_events` table + `trg_audit_events_immutable` trigger in `01-schema.sql`, `record_audit` service)
- [x] Demo data labelled and excluded from real alerts (`database/schema/02-demo-seed.sql` with `is_demo = true` on every row + `v_demo_rows` view)
- [x] Privacy notice and language coverage (DPIA drafted in `database/governance/04-dpia.md`)
- [ ] Access-review process for admin roles

**Gate 12 exit criteria:** export, deletion, and audit requests can each be fulfilled and demonstrated.

---

## Final verification matrix

Re-run this after every gate. A row is **PASS** only with fresh evidence.

| # | Check | Expected evidence | Status |
|---|---|---|---|
| 1 | Clean install | fresh clone -> install -> tests pass | PARTIAL — `backend/requirements.txt` and `frontend/package-lock.json` committed; clean-clone install requires dev environment |
| 2 | Tests | full suite green, count recorded | PARTIAL — 374 tests pass total: 336 backend tests pass (health, conversations, triage/decision, advisories/alerts, map layers, identity, chat safety gate, provider adapter) + 38 database tests pass (`database/tests/` across schema/seed, storage rules, weather & boundaries) |
| 3 | OpenAPI security | `securitySchemes` present | PARTIAL — `HTTPBearer` present and applied to `/v1/me` and `/v1/admin/*`; demo chat/assessment/advisory/map routes remain unauthenticated |
| 4 | Unauthenticated admin route | `401`/`403` | PASS — `/v1/admin/users` returns `401` without a token and `403` with a farmer token (`test_identity_api.py`) |
| 5 | Farmer cross-tenant read | `403`/`404` with no data leak | PARTIAL — object ownership filtering implemented in `backend/app/api/v1/observations.py` and `modules/observations/service.py`; conversations/uploads carry `owner_id` |
| 6 | Upload -> inference | prediction returned with model version | PARTIAL — upload confirmation triggers assessment; `AssessmentService`, explanation validator, and optional vision adapter implemented |
| 7 | Diagnosis persisted | record retrievable in history | PARTIAL — messages, uploads and review requests persist through the `0002_chat_persistence` schema; `GET /v1/observations` implemented |
| 8 | Image retrievable via signed URL | `200`, URL expires | PARTIAL — S3 presigned rules (TTL ≤ 10m) verified in `database/tests/test_storage_rules.py`; unauthenticated local upload preview exists |
| 9 | Weather affects risk | two fixtures -> different scores | PARTIAL — weather ingestion (`weather_ingest.py`, `boundary_loader.py`, `historical_ingest.py`), freshness SLA (≤24h), leaf-wetness proxy, spatial matching, and refusal gates (`forecast_gate.py`, `check_weather_sufficiency` DB function) implemented and unit-tested in `database/` (missing/stale weather produces explicit `insufficient_data` with `probability = NULL`; zero silent imputation); backend forecast fixture integration runner pending |
| 10 | Risk -> alert | one deduped alert, correct recipients | PARTIAL — alert trigger/dispatch service machinery is implemented and unit-tested (`app/modules/alerts/*`, `test_alert_*.py`); alert HTTP routers and delivery provider pending |
| 11 | Map uses API data | layer changes when records change | MISSING — backend layer API exists (`GET /v1/map/layers/{layer}`) with suppression and layer separation; `/outlook` is an honest empty state |
| 12 | Admin sees real data | count matches database | PARTIAL — `/v1/admin/*` identity routes exist and return `401`/`403`; admin routers for models and alerts exist; dashboard UI pending |
| 13 | Audit event written | login / role change / record view present | PARTIAL — identity events are written in memory (login, role change, admin view, export, retention); `audit_events` immutable triggers in `01-schema.sql` |
| 14 | Kannada complete | no English leaks on Kannada UI | MISSING — English + Kannada decided (D13); string catalogues pending |
| 15 | Readiness degrades | `503` when a dependency is down | MISSING — only liveness `/health` exists; `/ready` probe pending |
| 16 | CI enforces | red test blocks merge | PARTIAL — `.github/workflows/ci.yml` is defined; CI execution recorded in CI runner |

> Rows 1, 2, 6, 7, 8, 10, 12, 13 and 16 are **PARTIAL** because scaffolding evidence
> exists, not because the audited capability is satisfied. Rows 9 and 11 stay **MISSING**:
> the forecast service is unwired/untested and the map has no client. No row may be marked
> **PASS** until the work-log evidence proves the expected result.

---

## Compliance definition of done

The project may be re-labelled from **NOT COMPLIANT** only when:

- [x] Gate 0 is fully closed (one architecture, decisions resolved, docs consistent)
- [ ] Gates 1 and 2 pass with automated E2E evidence
- [ ] Gate 3 has either a real trained model **or** an explicitly stated claim of "inference-only, untrained"
- [ ] Gates 4–8 pass
- [ ] Every row in the final verification matrix is **PASS** (no `NOT VERIFIED`, no `PARTIAL`)
- [ ] The audit report is re-run and a new verdict is recorded with a date

Until then, the correct description remains: **documentation plus Phase 2 engineering
scaffolding (a persisted demo web chat, an in-memory identity/role slice, and untrained
image-triage, forecast, alert and map machinery, with no real model) — not a compliant
application**. Gate 0 is closed; Gate 1 remains open.
