# Technical Requirements Document (TRD)

**Product:** PS-03 — AI-Based Early Pest and Disease Outbreak Prediction Network
**Document type:** Technical Requirements Document
**Version:** 1.1
**Status:** Draft for review — architecture baseline; initial backend/web/mobile scaffold exists
**Owner:** Engineering lead
**Last updated:** 2026-11-06

**Companion documents**

| Concern | Document |
|---|---|
| Product requirements | `PRD.md` |
| Working rules and hard stops | `docs-context/AGENTS.md` |
| Architecture baseline and invariants | `docs-context/architecture-context.md` |
| Language, API, security and ML conventions | `docs-context/code-standards.md` |
| Implementation contracts | `feature-specs/01`–`08` |
| Conversational capture contract | `feature-specs/08-conversational-capture.md` |
| Data rules | `docs-context/data-foundation.md` |
| Model design | `docs-context/ml-models.md` |
| Operations, pilot and monitoring | `docs-context/operations-and-pilot.md` |
| Phase work and gates | `docs-context/phase-plan.md` |

This TRD defines **how** the system is built. It does not change product scope. If this
document and a feature spec conflict, the feature spec wins; if either conflicts with
`docs-context/AGENTS.md`, `AGENTS.md` wins. Any deviation from this baseline requires an
ADR in `docs-context/progress-tracker.md` §5.

---

## 1. Scope and technical objectives

### 1.1 In scope

- A modular-monolith API for identity, observations, media, inference, forecasts, reviews,
  advisories, alerts, admin and audit.
- A Flutter Android capture app with offline queue and sync, plus conversational capture.
- A Next.js web frontend: conversational capture, expert portal, district dashboard and
  admin, API-only.
- A conversation service ("chat") shared by web and mobile that wraps the photo-assessment
  pipeline: image message in, structured assessment reply out.
- A PostgreSQL 16 + PostGIS schema with migrations.
- Private S3-compatible object storage for images and model artefacts.
- A PyTorch training workflow exporting ONNX; CPU inference at pilot scale.
- A rules-based forecast engine with immutable feature snapshots.
- Scheduled jobs for weather ingest, forecast generation and alert dispatch.
- Structured logging, Prometheus metrics and audit events.
- Deployment via containers to `dev`, `staging` and `prod`.

### 1.2 Technical objectives

| ID | Objective |
|---|---|
| TRD-O-01 | Enforce the two-output separation structurally (separate tables, modules, endpoints, UI cards). |
| TRD-O-02 | Make abstention, coverage and staleness first-class states in data and API. |
| TRD-O-03 | Guarantee offline capture and exactly-once observation creation under retry. |
| TRD-O-04 | Make every prediction and forecast reproducible from stored inputs and versions. |
| TRD-O-05 | Enforce human verification and append-only audit at the lowest practical layer. |
| TRD-O-06 | Keep precise farm location out of unauthorised responses and public map layers. |
| TRD-O-07 | Operate on low-cost infrastructure: one VM, managed Postgres, object storage, CPU inference. |
| TRD-O-08 | Support testability, rollback and recovery before the pilot. |
| TRD-O-09 | Serve a chat surface on web and mobile whose replies are structured, traceable, validator-checked and never a free-form diagnosis. |

### 1.3 Out of scope

- Microservices, Kafka/streaming, Kubernetes, a separate feature store, a data lakehouse.
- Multi-region replication, multi-tenant SaaS abstractions, a public third-party API.
- On-device model inference in v1 (the quality pre-check is client-side; classification is
  server-side).
- Farm-level risk inference, universal crop diagnosis, generative advisory, free-form
  generative diagnosis chat.
- Real-time nowcasting from streaming data.
- Multi-crop joint models and automated model promotion.

---

## 2. Architecture overview

### 2.1 Architectural stance

1. **Modular monolith first.** One FastAPI application with explicit internal modules.
   Split a service only when load, failure isolation or team ownership demands it.
2. **Two AI tracks, one application.** Image inference and forecast generation are separate
   pipelines with separate versioning; they share case management and data.
3. **Offline is a client concern with server guarantees.** The client owns the queue; the
   server owns idempotency, ordering and conflict rules.
4. **Everything displayed is traceable.** Model version, input timestamps, issue/expiry,
   calibration status and snapshot references are stored, not reconstructed.
5. **Boring infrastructure.** One VM, managed Postgres, object storage, containers.

### 2.2 Component view

```
┌──────────────────────┐   ┌──────────────────────────────┐
│ Flutter app          │   │ Next.js web app               │
│ • chat + camera      │   │ • chat + image upload         │
│ • crop context       │   │ • expert portal / cases       │
│ • offline queue      │   │ • map layers / filters        │
│ • result cards       │   │ • advisory + admin            │
└──────────┬───────────┘   └───────────────┬──────────────┘
           │ HTTPS/JSON (OpenAPI v1)       │
           └───────────────┬───────────────┘
                           v
        ┌──────────────────────────────────────────────┐
        │ FastAPI modular monolith                     │
        │                                              │
        │  identity ─ consent ─ observations ─ media   │
        │  conversations ─ reviews ─ advisories        │
        │  forecasts ─ alerts ─ admin ─ audit ─ jobs   │
        │                                              │
        │  inference client ──► ONNX image service     │
        │  forecast engine  ──► rules / model artefacts│
        └───────┬───────────────┬──────────────┬───────┘
                │               │              │
                v               v              v
        PostgreSQL+PostGIS   Object store   External providers
        (records, audit,     (images,       (weather, boundaries,
         snapshots, registry) artefacts)    SMS/WhatsApp, maps)
```

Both clients use the same `/v1` API. The chat is a presentation layer over `observations`
and `inference`, implemented by the `conversations` module; it never calls the forecast
engine to answer a photo question.

The image service may start as an in-process module behind an interface. It becomes a
separate container when inference load or deployment cadence requires it; the API contract
does not change.

### 2.3 Runtime responsibilities

| Runtime | Responsibilities |
|---|---|
| `api` | HTTP API, auth, validation, orchestration, synchronous inference call, audit |
| `worker` | Weather ingest, forecast generation, alert dispatch, retries, cleanup jobs |
| `inference` | ONNX quality gate and classifier; may be in-process initially |
| `web` | Next.js server rendering and API proxy; no database access |
| `postgres` | Records, audit, snapshots, registry, PostGIS aggregation |
| `object-store` | Original images, derivatives, advisory files, model artefacts, exports |

---

## 3. Technology stack

The stack is fixed for v1. A change requires an ADR.

| Layer | Choice | Notes |
|---|---|---|
| Mobile | **Flutter** (Android-first) | Camera, local DB, background sync, single codebase |
| Web | **Next.js + TypeScript** (App Router) | Expert portal and district dashboard; API-only |
| API | **Python 3.12 + FastAPI** | Pydantic v2; OpenAPI as the contract |
| ORM / migrations | **SQLAlchemy 2.0 + Alembic** | Single schema authority; no second ORM |
| Database | **PostgreSQL 16 + PostGIS 3.x** | Spatial only where queries need it |
| Object storage | **S3-compatible private buckets** | Presigned upload/download, short TTL |
| Image ML | **PyTorch** training → **ONNX Runtime** serving | CPU inference at pilot scale |
| Forecast | Rules engine; scikit-learn / LightGBM later | Rules first; ML overlay after 2 seasons |
| Maps | **MapLibre GL JS** + PostGIS `ST_AsMVT` | No custom GIS platform |
| Jobs | **Celery beat** or **APScheduler** (choose at scaffold) | Weather ingest, forecast, alerts |
| Notifications | Adapter interface: SMS / WhatsApp / push | Provider chosen per pilot partner |
| Dev runtime | **Docker Compose** | API, DB, object storage, web |
| Observability | Structured JSON logs + Prometheus metrics | No PII in logs |

**Explicitly rejected:** Prisma or any second schema authority; microservices; Kafka; a
separate feature store; on-device classification in v1; multi-tenant abstractions.

**Version policy:** pin runtime and library versions in lockfiles; record the training
environment with every model artefact; patch security-critical dependencies on a defined
cadence.

---

## 4. Module boundaries

Each module owns its tables and exposes a service interface. Cross-module access goes
through that interface, never through another module's tables.

| Module | Owns | Must not |
|---|---|---|
| `identity` | users, roles, sessions, devices, consent | know about images or forecasts |
| `observations` | observations, crop cycles, growing areas, image assets | compute predictions |
| `media` | upload validation, storage keys, presigned URLs, derivatives | expose public buckets |
| `conversations` | chat threads, messages, attachments, reply templates, delivery state | compute predictions, write verification, generate free-form advice |
| `inference` | quality gate, photo assessment, model registry reads | write verification status |
| `forecasts` | forecast runs, feature snapshots, coverage, risk bands | read unverified reports as confirmed |
| `reviews` | review queue, verification states, evidence, corrections | auto-promote model output |
| `advisories` | advisory content, versions, approvals, expiry | generate chemical guidance |
| `alerts` | trigger policy, dedupe, cooldowns, delivery status | label a forecast as an outbreak |
| `admin` | crops, targets, geographies, thresholds, exports | bypass audit |
| `audit` | append-only audit events | be writable by clients |

**Dependency direction:** `api → module services → repositories → db`.

**Rules**

- Routers parse, authorise, delegate and serialise. No business logic and no SQL.
- Repositories contain queries; services contain decisions.
- A module never imports another module's repository or ORM model.
- Modules may call `audit` and `notifications`.
- `forecasts` may read **verified** observation projections through the `observations`
  interface only.
- `conversations` may call `observations`, `media`, `inference`, `reviews` and `advisories`
  through their interfaces; it never reads their tables directly.
- Cross-module transactions are explicit and rare; prefer an outbox/job for side effects.

### 4.1 Target source layout

```
backend/app/
├── api/v1/            # routers: parse, authorise, delegate, serialise
├── core/              # config, security, logging, errors
├── modules/
│   ├── identity/
│   ├── observations/
│   ├── media/
│   ├── conversations/   # chat threads + structured replies
│   ├── inference/
│   ├── forecasts/
│   ├── reviews/
│   ├── advisories/
│   ├── alerts/
│   └── audit/
├── db/                # session, base, models, repositories
└── workers/           # scheduled jobs
```

---

## 5. Deployment topology and environments

### 5.1 Pilot topology

```
Internet
  │
  ├── TLS terminator (Caddy/nginx)
  │     ├── /            → Next.js (web)
  │     ├── /api/*       → FastAPI (api)
  │     └── /tiles/*     → FastAPI map endpoints
  │
  ├── api container ──► Postgres (managed) + PostGIS
  │                └──► object storage (managed)
  │                └──► ONNX inference container (CPU)
  │
  ├── worker container (scheduled jobs: weather, forecast, alerts)
  └── backups: DB daily + object versioning; restore tested before pilot
```

### 5.2 Environments

| Environment | Purpose | Data rules |
|---|---|---|
| `dev` | Rapid iteration, local compose | Synthetic data only |
| `staging` | Mirrors production configuration; release rehearsal | No real farmer data |
| `prod` | Pilot operations | Strict access, backups, monitoring, audit |

### 5.3 Release rules

- Migrations run as a release step, forward-only in production, with a documented rollback
  (compensating migration or restore).
- Destructive changes use expand → migrate → contract.
- Rollout is controlled; rollback is documented and tested.
- Secrets come from environment/secret manager; never in images, mobile builds or fixtures.
- Infrastructure-as-code where practical; any manual step is documented.

---

## 6. Data model and storage

Authoritative detail is in `feature-specs/05-data-layer.md`. This section states the
technical contract.

### 6.1 Conventions

- PostgreSQL 16 + PostGIS 3.x; UUID primary keys (`gen_random_uuid()`).
- `created_at`, `updated_at` `timestamptz not null default now()`.
- `text` + `CHECK` for closed sets, not native enums.
- All timestamps UTC; ISO-8601 with `Z` at the API edge.
- Every external feature row stores `source_timestamp` and `fetched_at`.
- Soft delete only for user-facing entities (`deleted_at`). Predictions, reviews, audit and
  forecasts are never soft-deleted.
- Every foreign key has an index; every queue/filter path has a covering index.
- JSONB only for heterogeneous payloads with a documented shape (candidates, drivers,
  evidence blobs); not for relationally queried data.
- Demo/synthetic rows carry `is_demo = true` or a `demo_` ID prefix.

### 6.2 Entity map

```
users ─┬─ user_roles ── roles
       ├─ consents
       ├─ devices
       └─ user_area_assignments ── geographies

growing_areas ── crop_cycles ── observations ─┬─ image_assets ─┬─ image_quality_results
                                              │                └─ image_predictions
                                              ├─ review_requests
                                              └─ reviews ─┬─ review_evidence
                                                          └─ review_events
observations ── observation_verification (projection)

conversations ── messages ─┬─ message_attachments ── image_assets
                           └─ message_events

geographies (versioned boundaries)
weather_snapshots
forecasts ── feature_snapshots
advisories ── advisory_versions ── advisory_approvals
alerts ── alert_deliveries
model_registry
audit_events
export_jobs
```

### 6.3 Core tables

| Group | Tables |
|---|---|
| Identity | `users`, `roles`, `user_roles`, `devices`, `consents`, `user_area_assignments`, `sessions` |
| Geography / crop | `geographies`, `crop_calendars`, `crops`, `targets`, `growing_areas`, `crop_cycles` |
| Observations / media | `observations`, `image_assets`, `image_quality_results`, `image_predictions`, `review_requests` |
| Conversations | `conversations`, `messages`, `message_attachments`, `message_events` |
| Review | `reviews`, `review_evidence`, `review_events`, `observation_verification`, `review_assignments` |
| Forecast / weather | `weather_snapshots`, `feature_snapshots`, `forecasts`, `forecast_runs` |
| Advisory / alerts | `advisories`, `advisory_versions`, `advisory_approvals`, `alert_policies`, `alerts`, `alert_deliveries`, `alert_feedback` |
| Registry / audit | `model_registry`, `audit_events`, `export_jobs` |

### 6.4 State values

| Field | Allowed values |
|---|---|
| `observation.status` | `draft`, `pending_upload`, `uploaded`, `assessing`, `assessed`, `abstained`, `failed`, `pending_review`, `reviewed` |
| `image_predictions.abstain_reason` | `blur`, `exposure`, `resolution`, `no_plant`, `unsupported_crop`, `out_of_domain`, `gate_version_missing` |
| `messages.role` | `user`, `assistant` |
| `messages.kind` | `image`, `text`, `assessment`, `abstained`, `unsupported_crop`, `queued`, `failed`, `review_requested` |
| Verification `evidence_tier` | `confirmed`, `probable`, `unverified`, `rejected`, `duplicate`, `needs_visit`, `unresolved` |
| `risk_band` | `low`, `moderate`, `high`, `urgent`, `insufficient_data` |
| `coverage` | `good`, `partial`, `low`, `unknown` |
| `model_registry.status` | `draft`, `validated`, `approved`, `retired` |
| `alert_deliveries.status` | `queued`, `sent`, `delivered`, `failed`, `suppressed`, `opted_out` |

### 6.5 Enforced invariants

| Invariant | Enforcement |
|---|---|
| Photo assessment ≠ forecast | Separate tables, modules, endpoints and UI components |
| No assessment without quality pass | Service gate + status check on `image_predictions` |
| Predictions append-only | Insert-only repository + DB trigger/permissions |
| Reviews append-only | Insert-only `reviews` and `review_events` |
| Only reviewers verify | Role dependency + FK/check; `confirmed` requires pathologist |
| Unverified ≠ confirmed feature | Forecast query filters `verified_at IS NOT NULL` |
| Forecast lineage | `feature_snapshot_id` and `model_version` NOT NULL |
| No probability without calibration | `probability` null unless calibration approved |
| No chemical advisory | Content validator + approval required before serving |
| Approximate location default | `precision` column + serializer field-level auth |
| Small counts suppressed | Aggregate view/function, not UI |
| Stale data visible | Validity columns + `is_stale` in API and UI |
| Chat ≠ free-form diagnosis | Reply is a structured message kind + server-side validator; no generative text path in v1 |
| Chat messages append-only | Insert-only `messages`; corrections are new messages |
| Chat idempotency | Unique `(conversation_id, client_message_id)`; `Idempotency-Key` required |
| Chat reply traceable | Assistant message stores `assessment_id`, `model_version`, `template_version`, `generated_at` |

**Required constraints (non-exhaustive)**

```sql
-- Predictions and reviews are immutable
CREATE TRIGGER image_predictions_no_update
BEFORE UPDATE OR DELETE ON image_predictions
FOR EACH ROW EXECUTE FUNCTION reject_mutation();

-- Idempotent observation creation
ALTER TABLE observations
  ADD CONSTRAINT uq_observation_client UNIQUE (user_id, client_report_id);

-- Verified evidence requires a human review
ALTER TABLE observation_verification
  ADD CONSTRAINT ck_verified_requires_review
  CHECK (status = 'unverified' OR review_id IS NOT NULL);

-- A forecast must carry lineage
ALTER TABLE forecasts
  ADD CONSTRAINT ck_forecast_lineage
  CHECK (feature_snapshot_id IS NOT NULL AND model_version IS NOT NULL);

-- Probability is bounded when present
ALTER TABLE forecasts
  ADD CONSTRAINT ck_probability_bounds
  CHECK (probability IS NULL OR probability BETWEEN 0 AND 1);

-- One user message per client id inside a conversation
ALTER TABLE messages
  ADD CONSTRAINT uq_message_client UNIQUE (conversation_id, client_message_id);
```

**Service-level rules**

- A forecast with `coverage = 'low'` must be `insufficient_data`, never a scored band.
- `confirmed` requires a review with a `lab_result` or `field_observation` evidence row and
  a `pathologist` actor.
- Advisory serving requires at least one approval row and `valid_to` in the future.
- A model cannot be served unless its registry status is `approved`.
- An assistant message is stored only after the chemical-content validator passes; a
  rejected reply is a failed message, never a partial one.
- `conversations` calls `observations`/`inference` through their interfaces; it never
  computes a prediction or writes verification.

### 6.6 Indexing baseline

| Query | Index |
|---|---|
| Observation history by user, newest first | `(user_id, created_at desc)` |
| Queue by area/status/urgency | `(geo_code, status, urgency_score desc, created_at)` |
| Forecast lookup | `(crop_code, target_code, geo_code, issue_time desc)` |
| Alerts dedupe | `unique(dedupe_key)` |
| Audit by entity | `(entity_type, entity_id, created_at desc)` |
| Weather freshness | `(geo_code, source_timestamp desc)` |
| Image hash dedupe | `(content_hash)` |
| Conversation list by owner | `(owner_id, last_message_at desc)` |
| Messages by conversation | `(conversation_id, created_at)` |

### 6.7 Object storage layout

```
s3://<private-bucket>/
  observations/<yyyy>/<mm>/<observation_id>/<image_id>/original.<ext>
  observations/<yyyy>/<mm>/<observation_id>/<image_id>/preview.jpg
  advisories/<advisory_id>/<version>/<file>
  models/<kind>/<version>/<artefact>
  exports/<export_job_id>/<file>
```

**Rules**

- Private bucket; access only via short-lived presigned URLs (≤ 10 minutes).
- Store a content checksum; detect duplicates by hash.
- Keep originals; derivatives are separate and regenerable.
- Strip EXIF GPS unless explicitly consented and needed.
- Deletion propagates to derivatives and previews.
- No public read ACLs, no directory listing.

### 6.8 Migrations

- Alembic; one logical change per revision; descriptive message.
- Forward-only in production; rollback is a restore or compensating migration, documented in
  the PR.
- Every migration states data impact, lock risk, expected duration and backfill plan.
- Destructive changes use a two-step deploy (expand → migrate → contract).
- Migrations run in CI against an empty database and a seeded database.
- No migration imports application code that can change later.

### 6.9 Retention, deletion and backups

- Retention periods are a programme/legal decision; the mechanism is implemented now.
- Deletion flow: verify identity → mark `deleted_at` → revoke sessions → schedule hard delete
  → retain audit and non-identifying aggregates → record completion.
- Daily Postgres backup + WAL archiving where available; object storage versioning enabled.
- Restore tested before pilot; RTO/RPO documented; quarterly restore drill.
- Model artefacts and registry are included in each backup set.

---

## 7. API specification

### 7.1 Conventions

- Base path `/v1`; OpenAPI generated from FastAPI; JSON only.
- ISO-8601 UTC timestamps with `Z`; snake_case fields.
- Cursor pagination: `?cursor=&limit=` → `{items, next_cursor}`.
- `Idempotency-Key` required on observation creation and upload completion.
- Presigned URLs for binary transfer; no multipart through the API process at pilot scale.
- Role checks are dependencies, not controller `if` statements.
- Filters are explicit and whitelisted; no arbitrary query passthrough.
- No endpoint exposes raw model scores, feature vectors or storage keys to farmer clients.
- Model version and advisory version are returned wherever the output depends on them.
- Breaking changes require `/v2`; additive fields are allowed within `/v1`.

### 7.2 Error envelope

RFC 7807-style, one shape everywhere:

```json
{
  "type": "https://api.example/errors/unsupported-crop",
  "title": "Crop is not supported in this release",
  "status": 422,
  "code": "unsupported_crop",
  "detail": "Supported crops: potato.",
  "request_id": "req_01H...",
  "retryable": false,
  "fields": []
}
```

- `code` is stable and machine-readable; clients branch on it, never on `detail`.
- Validation errors include `fields`.
- Never leak stack traces, SQL or model internals.

### 7.3 Resource sketch

```
# Auth / identity
POST   /v1/auth/otp/request
POST   /v1/auth/otp/verify
POST   /v1/auth/refresh
POST   /v1/auth/logout
GET    /v1/me
PATCH  /v1/me
GET    /v1/config/crops
GET    /v1/areas

# Observations and media
POST   /v1/observations
GET    /v1/observations/{id}
GET    /v1/observations?cursor=&status=
POST   /v1/observations/{id}/images/upload-url
POST   /v1/observations/{id}/images/{image_id}/complete
POST   /v1/observations/{id}/images/{image_id}/retake
GET    /v1/observations/{id}/assessment
POST   /v1/observations/{id}/review-request

# Conversations (chat)
GET    /v1/conversations?cursor=
POST   /v1/conversations
GET    /v1/conversations/{id}
DELETE /v1/conversations/{id}
GET    /v1/conversations/{id}/messages?cursor=
POST   /v1/conversations/{id}/messages
POST   /v1/conversations/{id}/messages/{message_id}/retry
GET    /v1/conversations/{id}/events            # optional SSE; polling otherwise

# Forecasts and map
GET    /v1/forecasts?crop=&target=&geo=&horizon=
GET    /v1/forecasts/{id}
GET    /v1/map/layers/{layer}?bbox=&date=&crop=&target=

# Review
GET    /v1/reviews/queue?sort=&cursor=
GET    /v1/reviews/{observation_id}
POST   /v1/reviews/{observation_id}/claim
POST   /v1/reviews/{observation_id}/release
POST   /v1/reviews/{observation_id}/decisions
POST   /v1/reviews/{observation_id}/escalate

# Advisory and alerts
GET    /v1/advisories?crop=&target=&geo=&language=
GET    /v1/alerts/preferences
PATCH  /v1/alerts/preferences
POST   /v1/alerts/{id}/feedback

# Admin
GET    /v1/admin/users
PATCH  /v1/admin/users/{id}/roles
GET    /v1/admin/audit
POST   /v1/admin/exports
GET    /v1/admin/exports/{id}
```

### 7.4 Key response contracts

**Photo assessment** (illustrative; demo values)

```json
{
  "assessment_id": "as_demo_001",
  "observation_id": "obs_demo_001",
  "state": "assessed",
  "candidates": [
    {"label": "late_blight", "band": "medium"},
    {"label": "abiotic_lookalike", "band": "low"},
    {"label": "unknown", "band": "low"}
  ],
  "confidence_band": "medium",
  "calibrated": false,
  "quality_flags": [],
  "model_version": "image-classifier-demo-0.1",
  "generated_at": "2026-11-06T06:00:00Z",
  "is_demo": true
}
```

No numeric score or percentage is returned to a client before calibration is validated and
approved for display (see `docs-context/architecture-context.md` §9 and
`feature-specs/01-design-system.md` §3.4). Raw scores stay server-side and appear only in
append-only prediction rows for audit.

**Abstained assessment**

```json
{
  "assessment_id": "as_demo_002",
  "observation_id": "obs_demo_002",
  "state": "abstained",
  "reason_code": "blur",
  "reason_text": "The image is too blurry to assess.",
  "next_step": "retake",
  "model_version": "image-quality-gate-demo-0.1",
  "generated_at": "2026-11-06T06:00:00Z",
  "is_demo": true
}
```

**Chat message** — see `feature-specs/08-conversational-capture.md` §6. A message is one
of `assessment`, `abstained`, `unsupported_crop`, `queued`, `failed` or
`review_requested`. Required assistant fields: `kind`, `assessment_id` or `reason_code`,
`model_version`, `generated_at`, `next_steps`, `is_demo` where applicable. The assistant
text is rendered from a versioned template; the structured fields are authoritative.

**Area outlook** — see `feature-specs/06-forecast-and-risk-map.md` §7. Required fields:
`issue_time`, `valid_from`, `valid_to`, `risk_band`, `probability` (null unless calibrated),
`confidence`, `coverage`, `coverage_detail`, `drivers`, `model_version`,
`feature_snapshot_id`, `is_stale`, `is_demo`.

### 7.5 Map endpoints

Layers: `verified_reports`, `unverified_reports`, `modelled_risk`, `coverage`,
`boundaries`.

- Each layer returns its own geometry and properties.
- **No endpoint returns a merged "risk" layer.**
- Aggregation happens in SQL (`ST_AsMVT` / `ST_Intersection`), not in the browser.
- Small counts are suppressed server-side.
- Precise farm points are never returned to unauthorised roles.

### 7.6 Authorisation

- Deny by default; a route without a role dependency is a defect.
- Object-level ownership checks are mandatory for every farmer resource.
- `farmer` can read only their own observations.
- Staff access is area-scoped, joined in the query, never filtered after fetch.
- Admin access to an individual record requires a reason and writes an audit event before
  returning data.
- Exports require role check, purpose, row limit and audit; no PII columns.
- `confirmed` verification is pathologist-only.
- A conversation is readable and writable only by its owner; staff access requires a role,
  area scope and reason, and writes an audit event before returning content.
- An assistant message cannot be created by a client; only the server writes `role =
  assistant`.

---

## 8. Key data flows

### 8.1 Report submission (online)

```
client → POST /v1/observations (client_report_id, crop, area, context)
       → presigned image upload
       → POST /v1/observations/{id}/images/complete
       → quality gate (sync or queued)
       → photo assessment (only if quality passes)
       → response: case reference + assessment state
```

The observation exists before the image is uploaded. A failed upload never loses the case;
it stays in `pending_upload`.

### 8.2 Report submission (offline)

```
client saves observation locally (status=queued, client_report_id)
       → on reconnect: create observation (idempotent) → upload → complete
       → server returns canonical case + assessment
       → client reconciles local row (append-only history preserved)
```

Retries reuse `client_report_id`; the server returns the existing observation instead of
creating a duplicate. Conflict rule: server state wins for status; the client keeps its local
audit trail.

### 8.3 Expert review

```
queue (sorted by urgency, uncertainty, age, geography)
  → case detail (original image, metadata, candidates, quality flags, forecast context)
  → decision: confirmed | probable | rejected | duplicate | needs_visit | unresolved
  → optional label correction + severity + evidence notes
  → audit event
  → verified projection updated atomically (feeds forecast features)
```

### 8.4 Forecast generation (scheduled)

```
job at issue time
  → check model approval + config validity
  → load weather snapshots (freshness check)
  → load crop stage + calendar
  → load lagged verified reports (verified only)
  → compute coverage
  → if gate fails → persist insufficient_data row (reason, coverage)
  → else compute features → persist feature_snapshot (immutable)
  → run versioned rules model → band (+ probability if calibrated)
  → persist forecast (issue, valid_from, valid_to, drivers, lineage)
  → emit metrics + alert evaluation
```

Forecasts are generated per crop × target × geography × horizon, never per farm. A run for
the same `(crop, target, geo, horizon, issue_date)` must not create duplicates; forced
re-runs retain both rows.

### 8.5 Alert dispatch

```
eligible forecast → dedupe key (area, target, band, window) → cooldown check
  → render approved template (crop, target, area, period, reason, next action,
     coverage, issue time)
  → send via user channel preference
  → record delivery status + provider receipt
```

### 8.6 Conversational capture (chat)

```
client (web or mobile) → POST /v1/conversations/{id}/messages (client_message_id, image ref)
  → create observation if needed (idempotent)
  → attach image via presigned upload; validate + quality gate
  → inference (only if quality passes)
  → compose reply from a versioned template + structured assessment fields
  → chemical-content validator (reject → failed message, never partial)
  → persist assistant message (assessment_id, model_version, template_version, generated_at)
  → response: user message + assistant message
  → optional: request review (creates review_requests + audit event)
```

Offline mobile: the message and image are stored locally with `client_message_id` and sent
on reconnect. A retry returns the existing message; it never creates a second observation.
The reply never merges area outlook: an outlook is a separate card fetched from
`/v1/forecasts`.

---

## 9. Client requirements

### 9.1 Flutter mobile app

**Technical contract**

- Null safety; no `dynamic` in domain models.
- `freezed` + `json_serializable` for immutable models and unions
  (loading/loaded/stale/offline/error).
- `drift` local DB with versioned migrations; never drop unsent observations on upgrade.
- `go_router` navigation; `riverpod` state.
- Repository layer abstracts API + local DB; widgets never call HTTP directly.
- All user-facing strings in ARB files; no hard-coded copy.
- Images compressed before queueing while retaining diagnostic detail; original dimensions
  recorded.
- Queue operations idempotent and resumable; persist retry count and last error.
- Golden tests for result cards, quality feedback and stale banner.
- Test on a low-end Android profile and in airplane mode.

**Chat contract**

- Chat is a first-class route, not a web-view wrapper: `ChatList` and `ChatThread` screens.
- The composer attaches camera/gallery images through the same queue and compression path
  as the structured capture flow.
- Reply bubbles render structured `AssessmentCard` components; no raw JSON in the UI.
- Offline messages show `queued`; a retry reuses `client_message_id`.
- Conversation deletion calls the privacy endpoint and clears local rows.
- Chat strings live in ARB files like all other copy.

**Offline queue state machine**

```
draft → queued → syncing → synced
                  ├─ retryable_failure → queued (backoff)
                  └─ terminal_failure → failed (user action)
```

**Local data**

- Cached supported crops, areas, advisories and recent outlooks.
- Cached outlook carries `last_updated`; after `valid_to` it renders as stale.
- Unsent observations and images remain until explicitly deleted by the user or a completed
  sync.
- Queue-size warning before a configured limit; never silently drop.

### 9.2 Next.js web portals

- TypeScript `strict`; no `any` without an inline justification.
- Types generated from the FastAPI OpenAPI schema (`openapi-typescript`); no hand-written
  response types.
- Server Components by default; client components only for interaction.
- One typed API client with explicit error handling; no database client in the web app.
- Forms validated with zod mirrored from the API contract; field-level errors.
- TanStack Query for server state; no global store unless proven necessary.
- Accessibility is part of done: labels, focus order, keyboard operation, contrast.
- No inline hex colours or magic spacing; use design tokens.
- One component per file; named export; presentational components receive data, containers
  fetch.

**Chat contract**

- `/chat` and `/chat/[conversationId]` routes; Server Components fetch the thread, a client
  component owns the composer and optimistic messages.
- Image attach uses the presigned-URL flow; drag-and-drop is an addition, not a fork of the
  capture contract.
- The assistant reply renders from typed `kind` fields, never from parsed prose.
- `is_demo` renders a visible badge; abstained/queued/failed states each show one primary
  action.
- The chat never embeds or merges the district map or area-outlook card; it links to them.

---

## 10. Media pipeline

1. Client captures an image, records dimensions/source/compression, runs the on-device
   pre-check.
2. `POST /v1/observations/{id}/images/upload-url` returns a short-TTL presigned URL.
3. Client uploads directly to object storage.
4. `POST /v1/observations/{id}/images/{image_id}/complete` validates magic bytes, content
   type, size and dimensions; stores hash; strips EXIF GPS unless consented.
5. Server quality gate runs; result is insert-only with `gate_version`, flags and thresholds.
6. If the gate passes, inference runs; otherwise the observation is `abstained` with a reason.
7. Derivatives (preview) are generated separately and are regenerable.
8. A retake attaches a new image to the same observation; history is preserved.

**Chat attachments** use the same pipeline. A chat message references an upload; the
server creates the observation first, then attaches the image. The chat never accepts a
base64 image through the JSON API at pilot scale.

**Constraints**

- No public buckets; presigned TTL ≤ 10 minutes.
- Validate magic bytes, not client MIME.
- Reject oversized or corrupt files with a stable error code.
- Deduplicate by content hash; do not merge observations automatically.
- Store original and derivative separately.

---

## 11. Machine learning subsystem

### 11.1 Image quality gate and classifier

**Pipeline**

```
frozen field dataset
  → preprocessing config (shared by training and serving)
  → quality-gate model (blur, exposure, resolution, no-plant, distance)
  → classifier baseline (transfer learning)
  → validation-only tuning
  → calibration + abstention threshold selection
  → one evaluation on the frozen field test set
  → ONNX export → registry entry → serving
```

**Requirements**

- Preprocessing is generated from one config shared by training and serving; record the
  config and library versions with the model.
- Augmentation is realistic (rotation, crop, mild brightness/contrast, scale, modest blur);
  no aggressive hue shifts or synthetic artefacts.
- Class imbalance handled with class weights/sampling; report per-class results.
- Calibration is required before displaying a percentage; otherwise use qualitative bands.
- Abstention thresholds are chosen on validation using hard negatives, never on the test set.
- The shipped threshold is recorded and returned with every prediction.
- Serving requires a registry status of `approved`; unapproved or unregistered models are
  refused.
- Predictions are insert-only and carry `model_version`, `generated_at`, input snapshot
  reference and calibration status.
- A model never writes verification status.
- On CPU, batch where possible; measure latency on the target deployment path.

**Reproducibility record per artefact**

Code commit, dataset version, split version, preprocessing config, architecture,
hyperparameters, library versions, random seed, checksum and registry row.

### 11.2 Forecast engine

**Model ladder**

| Step | Model | When |
|---|---|---|
| 1 | Documented agronomic risk index (weather thresholds + crop stage), versioned and approved | Day one |
| 2 | Logistic regression on weather windows + stage + lagged verified reports | After one season |
| 3 | Gradient boosting (LightGBM/XGBoost) | After 2+ seasons |
| 4 | Spatiotemporal models | Only with dense longitudinal data (year 3+) |

The rules model is always retained as a fallback and comparison baseline. A more complex
model ships only if it beats the baseline on the operational metric, not on training loss.

**Feature groups**

- Weather: rolling rainfall, temperature ranges, humidity, consecutive wet days,
  leaf-wetness proxy.
- Crop: crop, stage, planting window, variety, irrigation context.
- Seasonal: week of year, monsoon period, days since planting, local crop calendar.
- Historical pressure: lagged verified cases, nearby verified reports, prior-season
  occurrence.
- Coverage: active reporters, visits, completeness, freshness.

**Leakage rule:** every feature must be computable at `issue_time`. Persist an immutable
feature snapshot per run; never recompute a historical forecast from today's data.

**No-score gate** — all must pass:

1. Weather snapshot freshness within threshold.
2. Minimum coverage (active reporters / completeness) met.
3. Crop calendar and stage available.
4. Boundary version matches the configured version.
5. Model version is `approved` in the registry.

If any fails, persist a forecast row with `risk_band = insufficient_data`, a machine
`reason_code` and `coverage`. Do not impute.

**Reproducibility:** re-running a forecast from its stored snapshot must reproduce the same
band. Late-arriving reports never rewrite a past forecast; they are used in the next issue.

### 11.3 Model registry and lifecycle

- Registry is the serving authority: `draft`, `validated`, `approved`, `retired`.
- Manual approval required; no automatic promotion on training metrics.
- Retain previous versions for rollback.
- Retraining uses governed, verified data and the frozen evaluation suite.
- Calibration, abstention and thresholds are reviewed when the crop calendar, reporting
  patterns or data distribution change.

---

## 12. Geospatial requirements

- `geographies.geom` is authoritative for aggregation; `boundary_version` is stored with
  every forecast and export.
- Observation location defaults to `precision = 'block'` and `geo_code`; precise geometry is
  nullable and never required.
- Precise geometry columns are excluded from API serialisers for roles without
  `view_precise_location`.
- Map endpoints aggregate in SQL (`ST_AsMVT` / `ST_Intersection`); never ship raw points to
  the browser for public layers.
- Distance-weighted features use geography type and a documented decay, computed in the
  forecast pipeline, not on the client.
- Small-count suppression is implemented in a view/function, not in the UI.
- Zoom is capped at the aggregation level; no farm precision.
- Area split/merge creates new codes; historical forecasts retain the old code and version.

---

## 13. Security architecture

### 13.1 Controls

| Control | Requirement |
|---|---|
| Authentication | Short-lived access token + rotating refresh token; phone OTP for farmers; Argon2id for staff passwords; MFA for pathologist/agronomist/admin |
| Authorisation | Role dependency on every route; deny by default; object-level ownership; area scoping in the query |
| Transport | TLS everywhere; HSTS |
| Storage | Encrypted volumes at rest; private object storage; presigned URLs ≤ 10 min |
| Uploads | Magic-byte validation, size/dimension limits, EXIF GPS stripping unless consented |
| Secrets | Environment/secret manager only; never in mobile builds, fixtures or logs |
| CORS | Explicit allowlist per environment |
| Headers | HSTS, CSP, `X-Content-Type-Options`, frame denial on portals |
| Dependencies | Pinned, scanned, patched; no unmaintained packages in the request path |
| Audit | Append-only `audit_events` for reviews, role changes, exports, config changes and sensitive access |
| Resilience | Backups, tested restore, incident-response ownership |
| Threat model | Completed before Phase 2 exit; refreshed when a new integration lands |
| Chat | Conversation ownership checks; server-only assistant role; chemical-content validator before storage; no client-supplied `model_version` or confidence |

### 13.2 Audit events (minimum)

- Auth: login, logout, token reuse detection, failed attempts, MFA changes.
- Consent: granted, withdrawn, version.
- Reviews: claim, release, decision, correction, escalation.
- Admin: role change, user disable, config/ threshold change, record view with reason.
- Exports: requested, completed, downloaded, expired.
- Predictions/forecasts: generated, model served, model approved/retired.
- Alerts: generated, suppressed, sent, failed, feedback.
- Chat: conversation created/deleted, message sent, reply generated, validator rejection,
  review requested from chat, staff access with reason.

Audit rows are insert-only and contain no PII payloads.

### 13.3 Hard stops

Refuse to implement anything that:

- generates pesticide/herbicide/fungicide/dosage advice;
- presents a model score as a diagnosis or confirmed outbreak;
- removes or hides abstention/coverage/staleness indicators;
- auto-verifies cases or bypasses expert review;
- trains/evaluates on data without documented permission;
- puts real personal or farm-identifying data into demo content, tests or fixtures;
- weakens authentication, authorisation or audit logging for convenience;
- serves a free-form generative diagnosis, treatment plan or chemical advice in chat;
- lets a client write an `assistant` message or supply model/confidence fields.

---

## 14. Offline, sync and conflict rules

- The client owns the queue; the server owns idempotency and ordering.
- `client_report_id` is generated on the device and is stable across retries.
- `Idempotency-Key` is required on observation creation and upload completion.
- Server returns the existing observation when a duplicate key is presented.
- Uploads resume or restart safely after interruption; the client records retry count and
  last error.
- Status precedence: server state wins for canonical status; the client keeps its local
  audit trail.
- Observations are append-only; expert verification changes are preserved as history.
- Cached outlooks are marked stale after `valid_to`.
- No flow requires a live server round-trip to save a report.
- Chat queue: `client_message_id` is stable across retries; the same key returns the same
  message and never creates a second observation.

**Required tests**

- Airplane mode capture → reconnect → single observation.
- Duplicate retry → no duplicate observation.
- Interrupted upload → safe resume/restart.
- Stale cached outlook → stale badge, not fresh risk.
- Queue-size limit → warning, no silent drop.
- Offline chat message → reconnect → one message, one assessment, no duplicate.

---

## 15. Observability and telemetry

### 15.1 Structured logs

One JSON event per line. Include `request_id` and propagate to jobs.

```json
{"ts":"2026-11-06T06:00:00Z","level":"info","event":"forecast.issued",
 "request_id":"req_...","forecast_id":"fcst_...","crop":"potato",
 "target":"late_blight","geo_code":"DEMO_BLOCK","risk_band":"moderate",
 "coverage":"good","model_version":"forecast-0.1.0"}
```

**Rules**

- Log state transitions, not payloads.
- Never log image bytes, phone numbers, exact coordinates, free-text notes or secrets.
- Include a stable error `code` on failures.

### 15.2 Required metrics

| Area | Metrics |
|---|---|
| API | Request latency, error rate, rate-limit hits |
| Upload / sync | Upload success, queue depth, sync success, retry count |
| Inference | Inference latency, abstention rate, quality-gate failure rate by reason |
| Forecast | Run success/failure, no-score rate, coverage distribution, generation latency |
| Alerts | Eligible, suppressed, sent, delivered, failed, opt-out |
| Data | Weather freshness lag, missing snapshots, boundary version mismatches |
| Review | Queue depth, median age, overdue count, decisions by type |
| Chat | Messages sent, images attached, replies by state, median reply time, retake rate, validator rejections, review requests |

Every metric and alert has an owner and a runbook entry before pilot launch.

### 15.3 Dashboards

Separate data problems (stale, missing), model problems (drift, calibration) and product
problems (latency, failures). Do not collapse them into one health number.

---

## 16. Performance, reliability and scalability

### 16.1 Targets

No numeric target is committed in this document. Targets are set from device and network
tests during scaffolding and recorded in `docs-context/progress-tracker.md`.

| Area | Target definition |
|---|---|
| API latency | p50/p95 per endpoint under pilot load |
| Inference latency | p50/p95 on the deployment CPU path |
| Forecast job | Completes within the issue window; no partial silent failure |
| Upload | Success rate on constrained networks |
| Sync | Success rate after retry; duplicate rate |
| Availability | Measured API availability during pilot hours |
| Recovery | RTO/RPO agreed before pilot |

### 16.2 Reliability rules

- Provider outages degrade gracefully; no silent imputation.
- Stale or incomplete data produces an explicit state.
- Retries are safe and idempotent; no duplicate observations or alerts.
- Forecast generation is idempotent per issue key.
- Failed jobs alert an owner; no silent backlog.
- Backups and restore are tested before pilot.

### 16.3 Scaling path (only when triggered)

| Trigger | Action |
|---|---|
| Inference latency exceeds target | Split inference into its own service; add a queue |
| Forecast volume grows | Batch per geography; precompute tiles |
| Map queries slow | Materialised aggregate tables + `ST_AsMVT` |
| Multiple districts with different rules | Config per geography, not code branches |
| Second crop | New target taxonomy + separate model head; never a universal model |
| Multi-language | Externalised strings; advisory content per language, not machine translation |

Do not pre-build any of this.

---

## 17. Testing requirements

| Layer | Minimum evidence |
|---|---|
| Domain rule | Unit test, positive + negative |
| API endpoint | Contract test + auth test (403 for wrong role) |
| Migration | Apply on empty DB + apply on seeded DB; rollback note |
| Sync/queue | Duplicate retry, interrupted upload, offline start |
| Image pipeline | Quality-gate tests; abstention path; version recorded |
| Forecast | Snapshot immutability; no-score on stale input; unverified excluded |
| Map layer | Verified/unverified/risk separation; suppression threshold |
| Advisory | Validator rejects chemical content; approval required before retrieval |
| Chat | Image message → one observation; abstention path; validator rejection; reply traceability; conversation ownership (403) |
| UI screen | Component/golden test for every state |
| Model training | Reproducible run from recorded config; frozen split hash |
| Security | Authorisation boundaries, upload abuse, PII leakage, secret handling |
| End-to-end | Report → upload → inference → review → alert → offline sync |

**Test data**

- Synthetic images and fake identifiers only. No real farmer data in fixtures, screenshots or
  demos.
- Integration tests run against a real PostgreSQL (testcontainers or compose), never SQLite.
- No network access in unit tests; stub providers behind interfaces.
- Every bug fix gets a regression test.
- Test names describe behaviour: `test_blurry_image_returns_abstained_state`.

**Reporting**

- Report commands exactly as run and pass/fail counts.
- If a suite was not run, say so and why. "Should work" is not a verification result.

---

## 18. CI/CD and engineering workflow

- Conventional commits: `feat(forecast): add coverage gate`, `fix(sync): dedupe retry`.
- Branch per change; small PRs where practical.
- PR description states requirement IDs, what changed, how tested, risk and rollback.
- CI runs lint, type checks, unit tests, integration tests and migration checks.
- Migration PRs include the rollback note and data-impact assessment.
- No secrets, no real farmer data, no large binaries in git.
- A reviewer checks the `AGENTS.md` definition of done, not just compilation.
- Environment promotion: `dev` → `staging` → `prod`; staging holds no real farmer data.

### 18.1 Definition of done (technical)

- [ ] Implements an accepted requirement ID.
- [ ] Failure paths implemented (unsupported crop, blur, stale weather, offline, duplicate,
      unauthorised role).
- [ ] Tests cover new behaviour and at least one negative case.
- [ ] No R1–R10 rule weakened.
- [ ] API change reflected in OpenAPI and the feature spec.
- [ ] Schema change ships with a forward migration and rollback note.
- [ ] User-facing strings externalised for translation.
- [ ] Telemetry/audit events emitted where required.
- [ ] No PII or secrets in logs, fixtures or commits.
- [ ] `progress-tracker.md` updated.

---

## 19. Technical acceptance criteria

The implementation is technically acceptable for pilot only when:

- [ ] The schema creates from zero via migrations and applies cleanly to a seeded database.
- [ ] Duplicate observation retry returns the existing observation; no duplicate row.
- [ ] Predictions, reviews, forecasts and audit rows reject update/delete.
- [ ] A forecast cannot be inserted without a feature snapshot and model version.
- [ ] An unverified observation is excluded from forecast feature queries (test).
- [ ] Precise geometry is absent from responses for unauthorised roles (test).
- [ ] Small-count suppression is enforced in the query layer (test).
- [ ] Advisory retrieval fails when no approval exists or content is expired (test).
- [ ] Serving an unapproved model version is refused (test).
- [ ] Demo rows are distinguishable and excluded from production queries by default.
- [ ] No-score gate returns `insufficient_data` for each failure condition.
- [ ] Re-running a forecast from its snapshot reproduces the same band.
- [ ] The map never merges reports and predictions server-side.
- [ ] Offline capture, interrupted upload and duplicate retry are verified on a low-end
      device.
- [ ] Chat image message produces one observation and one structured assessment reply on
      web and mobile.
- [ ] Chat retry is idempotent; no duplicate message or observation.
- [ ] Chat abstains with a reason on blur, unsupported crop and out-of-domain input.
- [ ] The chat validator rejects chemical content before storage (test).
- [ ] A conversation is inaccessible to another user (403).
- [ ] Assistant messages are server-only and carry assessment, model and template versions.
- [ ] Chat never merges the area outlook into an assessment reply.
- [ ] Audit events exist for auth, review, role, export, config, prediction and chat events.
- [ ] Backup restore drill completed and documented.
- [ ] Threat model completed before Phase 2 exit.
- [ ] No secrets or PII in logs, fixtures, screenshots or builds.

---

## 20. Technical risks and mitigations

| Risk | Mitigation |
|---|---|
| Dual schema authority drift | SQLAlchemy/Alembic only; no Prisma or manual prod DDL |
| Offline conflict corruption | Client IDs, idempotency keys, append-only history, server-state precedence |
| Forecast leakage | Feature availability at issue time; immutable snapshots; leakage tests |
| Unapproved model served | Registry status check in the serving path |
| PII leakage via logs/exports | Log allowlist, PII-free events, export role checks and audit |
| Precise location exposure | Precision columns, serializer field auth, SQL aggregation, suppression |
| Map layer conflation | Separate endpoints and components; no merged layer |
| Alert storms | Dedupe key, cooldowns, coverage/freshness gates, pause control |
| Provider outage | Explicit stale/incomplete states; no imputation; owner alert |
| Migration lock or data loss | Expand → migrate → contract; tested on seeded DB; rollback note |
| Cost growth | CPU inference, one VM, managed services, free weather sources until justified |
| Model drift | Monitoring, calibration review, governed retraining, version rollback |
| Chat reads as diagnosis | Structured reply templates, abstention, "assistive not diagnosis" copy, human review |
| Chat emits chemical advice | Server-side validator before storage; template tests; no free-form generative path |
| Chat bypasses verification | Chat review request uses the same review module, states and audit |
| Chat scope creep into a general LLM assistant | Explicit out-of-scope; no generative diagnosis in v1 |

---

## 21. Traceability

| TRD area | Primary spec / document |
|---|---|
| Modules and flows | `docs-context/architecture-context.md` |
| Schema, storage, migrations | `feature-specs/05-data-layer.md` |
| Capture, quality, sync, result | `feature-specs/02-reporting-and-capture.md` |
| Identity, roles, consent | `feature-specs/03-auth-and-roles.md` |
| Review and verification | `feature-specs/04-expert-review.md` |
| Forecast, no-score, map | `feature-specs/06-forecast-and-risk-map.md` |
| Advisory and alerts | `feature-specs/07-advisory-and-alerts.md` |
| Conversational capture (chat) | `feature-specs/08-conversational-capture.md` |
| UI tokens and states | `feature-specs/01-design-system.md`, `docs-context/ui-context.md` |
| Data rules and splits | `docs-context/data-foundation.md` |
| Model design and evaluation | `docs-context/ml-models.md` |
| Testing, deployment, monitoring | `docs-context/operations-and-pilot.md` |
| Phase gates | `docs-context/phase-plan.md` |

---

## 22. Glossary

| Term | Meaning |
|---|---|
| **Modular monolith** | One deployable API with explicit internal module boundaries. |
| **Idempotency key** | Client-supplied key that makes a retried create return the original result. |
| **Feature snapshot** | Immutable record of every input used to compute a forecast. |
| **Verified projection** | Derived current verification state built from append-only review events. |
| **Abstention** | Model declines to answer because evidence is insufficient. |
| **No-score** | Explicit `insufficient_data` outlook when coverage, freshness or approval fails. |
| **Coverage** | Completeness, freshness and representativeness of inputs for an area. |
| **Stale** | Past its validity window; must be visually and semantically distinct from fresh data. |
| **Presigned URL** | Short-lived signed URL for direct object-storage access. |
| **ONNX** | Portable model format used for CPU inference at pilot scale. |
| **Conversation** | A private chat thread owned by one user; messages are append-only. |
| **Assistant reply** | A server-authored, template-rendered message carrying structured assessment fields. |

---

## 23. Document control

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-11-06 | Initial TRD distilled from the architecture baseline, code standards, feature specs and phase plan. No scope, gate or decision changed. |
| 1.1 | 2026-11-06 | Made full-stack delivery explicit (backend + web + mobile) and added the `conversations` module, chat API, data tables, flows, client contracts, security controls, tests and acceptance criteria. No existing gate changed. |

**Change control:** update this TRD whenever a stack choice, module boundary, schema
invariant, API contract, security control or deployment topology changes. Record the change
and the ADR in `docs-context/progress-tracker.md` in the same change.
