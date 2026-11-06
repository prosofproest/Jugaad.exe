# Architecture context

**Purpose:** describe how the system is composed, where logic belongs, and which
invariants the implementation must enforce.
**Status:** baseline architecture for v1. Any deviation requires an ADR entry in
`progress-tracker.md`.
**Last updated:** 2026-11-06

---

## 1. Architectural stance

- **Modular monolith first.** One FastAPI application with explicit internal modules.
  Split out a service only when load, failure isolation or team ownership demands it.
- **Two AI tracks, one application.** Image inference and forecast generation are
  separate pipelines with separate versioning, but share case management and data.
- **Offline is a client concern with server guarantees.** The client owns the queue; the
  server owns idempotency, ordering and conflict rules.
- **Everything displayed is traceable.** Model version, input timestamps, issue/expiry,
  calibration status and snapshot references are stored, not reconstructed.
- **Boring infrastructure.** One VM, managed Postgres, object storage, containers. No
  Kubernetes, no streaming platform, no feature store in v1.

---

## 2. Baseline stack

| Layer | Choice | Notes |
|---|---|---|
| Mobile | **Flutter** (Android-first) | Conversational capture + camera, local DB, background sync; single codebase |
| Web app | **Next.js + TypeScript** (App Router) | Conversational capture, expert portal, district dashboard and admin; API-only data access |
| API | **Python 3.12 + FastAPI** | Pydantic v2, OpenAPI as the contract |
| ORM / migrations | **SQLAlchemy 2.0 + Alembic** | Single migration owner; no second ORM |
| Database | **PostgreSQL 16 + PostGIS** | Spatial only where queries need it |
| Object storage | S3-compatible, private buckets | Presigned upload/download, short TTL |
| Image ML | **PyTorch** training → **ONNX Runtime** serving | CPU inference at pilot scale |
| Forecast | Rules engine + scikit-learn / LightGBM later | Rules first, ML overlay after 2 seasons |
| Maps | **MapLibre GL JS** + PostGIS `ST_AsMVT` | No custom GIS platform |
| Jobs | APScheduler or Celery beat (choose at scaffold) | Weather ingest, forecast run, alert dispatch |
| Notifications | Adapter interface: SMS / WhatsApp / push | Provider chosen per pilot partner |
| Dev runtime | Docker Compose | API, DB, object storage, web |
| Observability | Structured JSON logs + Prometheus metrics | No PII in logs |

**Explicitly rejected:** Prisma (Node-only; would create a second schema authority),
microservices, Kafka, a separate feature store, on-device inference in v1, multi-tenant
SaaS abstractions.

The web app and mobile app consume the FastAPI OpenAPI schema; they never read the database
directly. Generated TypeScript/Dart types come from that schema. The chat surface on both
clients is a presentation layer over the `conversations` module, not a second backend.

---

## 3. Component view

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
and `inference`, implemented by the `conversations` module; it does not call the forecast
engine to answer a photo question.

The image service may start as an in-process module behind an interface. It becomes a
separate container when inference load or deployment cadence requires it; the API
contract does not change.

---

## 4. Module boundaries

Each module owns its tables and exposes a service interface. Cross-module access goes
through that interface, not through another module's tables.

| Module | Owns | Must not |
|---|---|---|
| `identity` | users, roles, sessions, devices, consent | know about images or forecasts |
| `observations` | observations, crop cycles, growing areas, image assets | compute predictions |
| `media` | upload validation, storage keys, presigned URLs, derivatives | expose public buckets |
| `conversations` | chat threads, messages, attachments, reply templates, delivery state | compute predictions, write verification, return free-form advice |
| `inference` | quality gate, photo assessment, model registry reads | write verification status |
| `forecasts` | forecast runs, feature snapshots, coverage, risk bands | read unverified reports as confirmed |
| `reviews` | review queue, verification states, evidence, corrections | auto-promote model output |
| `advisories` | advisory content, versions, approvals, expiry | generate chemical guidance |
| `alerts` | trigger policy, dedupe, cooldowns, delivery status | label a forecast as an outbreak |
| `admin` | crops, targets, geographies, thresholds, exports | bypass audit |
| `audit` | append-only audit events | be writable by clients |

Dependency direction: `api → module services → repositories → db`. Modules may call
`audit` and `notifications`. `forecasts` may read **verified** observation projections
through the `observations` interface only.

---

## 5. Primary flows

### 5.1 Report submission (online)

```
client → POST /v1/observations (client_report_id, crop, area, context)
       → presigned image upload
       → POST /v1/observations/{id}/images/complete
       → quality gate (sync or queued)
       → photo assessment (if quality passes)
       → response: case reference + assessment state
```

The observation exists before the image is uploaded. A failed upload never loses the
case; it stays in `pending_upload`.

### 5.2 Report submission (offline)

```
client saves observation locally (status=queued, client_report_id)
       → on reconnect: create observation (idempotent) → upload → complete
       → server returns canonical case + assessment
       → client reconciles local row (append-only history preserved)
```

Retries reuse `client_report_id`; the server returns the existing observation instead of
creating a duplicate. Conflict rule: server state wins for status; client keeps its local
audit trail.

### 5.3 Expert review

```
queue (sorted by urgency, uncertainty, age, geography)
  → case detail (original image, metadata, candidates, quality flags, forecast context)
  → decision: confirmed | probable | rejected | duplicate | needs_visit | unresolved
  → optional label correction + severity + evidence notes
  → audit event
  → verified projection updated (feeds forecast features)
```

### 5.4 Forecast generation (scheduled)

```
job at issue time
  → load weather windows + crop stage + verified report lags + coverage
  → persist feature_snapshot (immutable)
  → run versioned rules/model
  → persist forecast (issue, valid_from, valid_to, band, probability|null,
     coverage, drivers, model_version)
  → if insufficient data: persist no-score record with reason
  → alert evaluation (threshold + freshness + coverage + dedupe/cooldown)
```

Forecasts are generated per crop × target × geography × horizon, never per farm.

### 5.5 Alert dispatch

```
eligible forecast → dedupe key (area,target,band,window) → cooldown check
  → render approved template (crop, target, area, period, reason, next action,
     coverage, issue time)
  → send via user channel preference
  → record delivery status + provider receipt
```

### 5.6 Conversational capture (chat)

```
client (web or mobile) → POST /v1/conversations/{id}/messages
  → create observation if needed (idempotent; client_message_id)
  → presigned image upload → quality gate → inference
  → compose reply from versioned template + structured assessment
  → chemical-content validator (reject → failed message, never partial)
  → persist assistant message (assessment_id, model_version, template_version)
  → response: user message + assistant message
  → optional review request (same review module + audit event)
```

The chat is a wrapper over observations and inference. It never merges the area outlook
into the assessment reply; an outlook is a separate card fetched from `/v1/forecasts`.

---

## 6. Data model (conceptual)

Authoritative detail lives in `../feature-specs/05-data-layer.md`.

```
users ─┬─ consents
       ├─ devices
       └─ user_roles

growing_areas ── crop_cycles ── observations ─┬─ image_assets ── image_predictions
                                              └─ reviews ── review_evidence

conversations ── messages ─┬─ message_attachments ── image_assets
                           └─ message_events

geographies (boundary_version, level, code)
forecasts ── feature_snapshots
advisories ── advisory_versions ── advisory_approvals
alerts ── alert_deliveries
audit_events
model_registry
```

Key relationships:

- one crop cycle → many observations;
- one observation → many images; one image → many predictions across model versions;
- one forecast → one feature snapshot; forecasts are immutable once issued;
- reviews append; the current verification status is a derived projection with history.

---

## 7. Invariants and where they are enforced

| Invariant | DB | Service | API | UI |
|---|---|---|---|---|
| Photo assessment ≠ forecast | separate tables | separate modules | separate resources | separate cards |
| No assessment without quality pass | `image_predictions.status` check | inference gate | 200 with `abstained` state | explicit no-result card |
| Predictions append-only | no UPDATE grant / trigger | insert-only repo | no PATCH endpoint | history view |
| Only reviewers verify | role FK + check | RBAC guard | 403 | hidden controls |
| Unverified ≠ confirmed feature | forecast query filters `verified_at IS NOT NULL` | forecast service | — | coverage note |
| No chemical advisory | content schema + approval | advisory validator | — | — |
| Approximate location default | precision column | geo service | field-level auth | coarse map |
| Small counts suppressed | aggregate view | dashboard service | — | legend note |
| Stale data visible | validity columns | freshness check | `is_stale` | stale banner |
| Chat ≠ free-form diagnosis | `messages.kind` check | `conversations` service + validator | structured reply only | `AssessmentCard` |
| Chat messages append-only | insert-only table grant | insert-only repo | no PATCH endpoint | history view |
| Chat idempotency | unique `(conversation_id, client_message_id)` | message service | `Idempotency-Key` | retry reuses id |
| Assistant reply traceable | `messages.assessment_id` NOT NULL for assistant | compose service | `model_version`, `template_version`, `generated_at` | metadata line |
| Conversation private to owner | `owner_id` FK | ownership guard | 403 for others | not listed |

If an invariant cannot be enforced at the lowest layer available, document why in the
feature spec.

---

## 8. External integrations

| Integration | Contract | Failure behaviour |
|---|---|---|
| Weather (NASA POWER / ERA5-Land) | Daily/hourly variables per grid point, with source timestamp | Mark snapshot incomplete; forecast returns `insufficient_data`; never impute silently |
| Admin boundaries | Versioned GeoJSON/PostGIS, stable codes | Block forecast issue for unmatched areas; surface error |
| Map tiles | MapLibre style + vector tiles from own API | Cached last tiles; show "map data unavailable" |
| SMS/WhatsApp gateway | Adapter with send + receipt callback | Retry with backoff; record failed delivery; no duplicate sends |
| Object storage | S3 API, presigned URLs | Upload retry; expired URL re-issued |
| Model artefacts | Registry row + object key + checksum | Refuse to serve unregistered/unapproved model |

Every external feature row stores `source_timestamp` and `fetched_at`. No provider secret
ever ships in a client build.

---

## 9. API shape

- Base path `/v1`; OpenAPI generated from FastAPI.
- JSON only; ISO-8601 UTC timestamps; snake_case fields.
- Errors use a single envelope (see `code-standards.md` §6).
- Cursor pagination for queues and histories.
- `Idempotency-Key` required on observation creation, upload completion and chat messages.
- Presigned URLs for binary transfer; no multipart through the API process at pilot scale.
- Role checks are dependencies, not controller `if` statements.
- No endpoint exposes raw model scores, feature vectors or storage keys to farmer clients.
- Chat replies are structured message kinds, not free-form text; the server alone writes
  `role = assistant`.

Resource sketch:

```
POST   /v1/observations
GET    /v1/observations/{id}
GET    /v1/observations?cursor=&status=
POST   /v1/observations/{id}/images/upload-url
POST   /v1/observations/{id}/images/{image_id}/complete
POST   /v1/observations/{id}/review-request
GET    /v1/observations/{id}/assessment

GET    /v1/conversations?cursor=
POST   /v1/conversations
GET    /v1/conversations/{id}
DELETE /v1/conversations/{id}
GET    /v1/conversations/{id}/messages?cursor=
POST   /v1/conversations/{id}/messages
POST   /v1/conversations/{id}/messages/{message_id}/retry

GET    /v1/forecasts?crop=&target=&geo=&horizon=
GET    /v1/forecasts/{id}
GET    /v1/map/layers/{layer}?bbox=&date=&crop=&target=

GET    /v1/reviews/queue?sort=&cursor=
GET    /v1/reviews/{observation_id}
POST   /v1/reviews/{observation_id}/decisions

GET    /v1/advisories?crop=&target=&geo=&language=
GET    /v1/alerts/preferences
PATCH  /v1/alerts/preferences
POST   /v1/alerts/{id}/feedback
```

---

## 10. Deployment topology (pilot)

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

Environments: `dev`, `staging`, `prod`. Staging mirrors prod configuration and holds no
real farmer data. Migrations run as a release step, forward-only, with a documented
rollback (down migration or restore).

---

## 11. Scaling path (only when triggered)

| Trigger | Action |
|---|---|
| Inference latency exceeds target | Split inference into its own service; add queue |
| Forecast volume grows | Batch per geography; precompute tiles |
| Map queries slow | Materialised aggregate tables + `ST_AsMVT` |
| Multiple districts with different rules | Config per geography, not code branches |
| Second crop | New target taxonomy + separate model head; never a universal model |
| Multi-language | Externalised strings; advisory content per language, not machine translation |

Do not pre-build any of this.

---

## 12. Architecture decisions (ADR log seed)

| ID | Decision | Rationale | Status |
|---|---|---|---|
| ADR-001 | Modular monolith, not microservices | Team size, operational cost, unclear boundaries | Accepted |
| ADR-002 | FastAPI + SQLAlchemy/Alembic as single schema authority | Avoid dual-ORM drift; Python ML integration | Accepted |
| ADR-003 | Web portals are API-only clients | One contract, no DB coupling, role enforcement server-side | Accepted |
| ADR-004 | Rules-based forecast before ML | No historical data in year one; defensible baseline | Accepted |
| ADR-005 | ONNX Runtime on CPU for pilot inference | Cost; latency sufficient for MobileNet-class models | Proposed |
| ADR-006 | Flutter for capture, SMS/WhatsApp for delivery | Camera + offline needs an app; reach needs messaging | Proposed |

New ADRs are appended in `progress-tracker.md` and referenced here.

---

## 13. What this architecture deliberately does not include

- A universal crop diagnostic model.
- Farm-level risk inference from block-level inputs.
- A general-purpose advisory chatbot.
- Real-time streaming ingestion.
- A public API for third parties.
- Cross-farmer social or sharing features.
- Any feature that requires precise farm coordinates to function.

---

## 14. Security architecture (chapter 43)

Security controls protect farmer information, images, expert accounts and operational
integrity. The normative rules are in `code-standards.md` §7 and
`../feature-specs/03-auth-and-roles.md`; this section states where they sit.

| Control | Architecture placement |
|---|---|
| Identity and sessions | `identity` module; short-lived access token + rotating refresh family; MFA for staff roles |
| Authorisation | Route dependencies + object-level checks; area scoping joined in the query, never filtered after fetch |
| Data protection | TLS in transit; encrypted volumes at rest; private object storage with ≤10 min presigned URLs |
| Upload safety | Magic-byte validation, size/dimension limits, EXIF GPS stripping unless consented |
| Secrets | Environment/secret manager only; never in mobile builds, fixtures or logs |
| Audit | Append-only `audit_events`; reviews, role changes, exports, admin record views and config changes |
| Resilience | Backups, tested restore, incident-response ownership |
| Threat model | Completed before Phase 2 exit; refreshed when a new external integration lands |

**Implementation points**

- Deny by default; a new route without a role dependency is a defect.
- Object-level ownership checks are mandatory for every farmer resource.
- Admin access to an individual record requires a reason and writes the audit event before
  returning data.

---

## 15. Data, model and operations placement

| Concern | Document |
|---|---|
| Data strategy, collection, labelling, splits, weather, historical records | `data-foundation.md` |
| Image and forecast model design, evaluation, calibration, combining outputs | `ml-models.md` |
| Testing, pilot, deployment, monitoring, team, metrics | `operations-and-pilot.md` |
| Roadmap, budget and risk rationale | `roadmap-and-resources.md` |
| Templates, checklists, glossary, launch gates | `appendices.md` |

**Operational invariants carried through the architecture**

- Data lineage is stored, not reconstructed: every forecast references an immutable feature
  snapshot; every prediction references its model version and input timestamps.
- Model serving requires an `approved` registry row; training metrics never promote a model.
- Monitoring covers data freshness, abstention rate, forecast no-score rate and delivery
  failure — not only HTTP latency.
- Retraining uses governed, verified data and re-runs the frozen evaluation suite.

---

## 16. Technology selection criteria (chapter 14)

The baseline stack in §2 is chosen against these criteria, not by fashion:

1. **Team skills and maintainability** — one language per surface, one schema authority.
2. **Rural deployment cost** — CPU inference, one VM, managed services, free weather data.
3. **Device constraints** — Android-first, low-RAM, unreliable connectivity.
4. **Ecosystem maturity** — camera, offline storage, mapping and typed API clients.
5. **Reversibility** — a decision that is hard to undo needs a recorded ADR.

Practical guidance from the blueprint:

- Flutter or React Native for Android-first mobile; test native camera and local storage.
- FastAPI or Django REST for the backend; pick one and standardise validation.
- PyTorch or TensorFlow for training; ONNX Runtime or TFLite for deployment.
- PostgreSQL + PostGIS for structured and spatial data; MapLibre or Leaflet for maps.
- Containerised deployment with managed object storage, metrics, logs, backups and a model
  registry.

**Do not** add a dependency or external provider without an ADR (`progress-tracker.md` §5)
and a cost/ownership note.
