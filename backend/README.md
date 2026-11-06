# Backend — FastAPI modular monolith

**Status:** engineering scaffold (Phase 2 §5.1), the persisted demo chat slice
(§5.7: uploads, demo quality gate, pluggable assessment engine with an optional
OpenAI-compatible vision adapter, content-safety validator, review requests), the
demo-labelled video-reading machinery (`09-video-reading.md`: bounded decode,
frame sampling, motion-region detector, `bytetrack-lite-0.1`, per-frame
assessments, non-diagnostic summary) and the in-memory §5.2 identity slice. No
product feature is served against real data; chat and video output are
demo-labelled unless an operator supplies an approved label set, and identity
state is lost on restart.
**Stack:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL
(see `../final/docs-context/architecture-context.md`).

## Layout

```
backend/
├── app/
│   ├── main.py                 # app factory, middleware, error handlers, OpenAPI
│   ├── api/v1/                 # routers: parse, authorise, delegate, serialise
│   ├── core/                   # config, logging, errors, request middleware
│   ├── modules/                # identity, observations, media, inference, ...
│   ├── db/
│   │   ├── base.py             # declarative base + naming conventions
│   │   ├── session.py          # lazy engine + request-scoped session
│   │   └── migrations/         # Alembic env, template, versions
│   └── workers/                # scheduled jobs
├── tests/
├── alembic.ini
├── Dockerfile
├── pyproject.toml
└── requirements.txt
```

## Commands (verified on this machine, 2026-11-06)

Run from `backend/` (Windows paths shown; POSIX uses `.venv/bin/python`):

| Task | Command |
|---|---|
| Create venv | `python -m venv .venv` |
| Install | `.venv\Scripts\python -m pip install -r requirements.txt` (POSIX: `.venv/bin/pip install -r requirements.txt`) |
| Tests | `.venv\Scripts\python -m pytest` |
| Lint | `.venv\Scripts\python -m ruff check app tests` |
| Format check | `.venv\Scripts\python -m ruff format --check app tests` |
| Migration history | `.venv\Scripts\python -m alembic history` |
| Review migration SQL offline | `.venv\Scripts\python -m alembic upgrade head --sql` |
| Apply migrations | `.venv\Scripts\python -m alembic upgrade head` (needs a live database) |
| Dev server | `.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000` |

`GET /health` and `GET /v1/health` return process liveness. OpenAPI/`/docs` are
served in dev and hidden when `APP_ENVIRONMENT=production` (unless
`APP_DOCS_ENABLED=true`). Every failure returns the problem-details envelope
(`application/problem+json`) with a stable `code` and `request_id`.

## Configuration

Environment variables use the `APP_` prefix (or an untracked `.env`); see
`.env.example`. No secrets in source control.

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENVIRONMENT` | `dev` | `dev`, `staging` or `production` |
| `APP_LOG_LEVEL` | `INFO` | Root log level for the JSON stream |
| `APP_DOCS_ENABLED` | `true` | Serve `/docs` and `/openapi.json` outside production |
| `APP_DATABASE_URL` | local compose URL | SQLAlchemy URL; never logged |
| `APP_CHAT_ENGINE` | `demo` | `demo` serves the labelled deterministic engine; `openai_compatible` calls a vision provider; any other value fails closed with `model_not_configured` |
| `APP_CHAT_API_KEY` | unset | Bearer key for the provider; never logged. Unset fails closed |
| `APP_CHAT_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible endpoint; `/chat/completions` is appended |
| `APP_CHAT_MODEL` | unset | Provider model id; unset fails closed |
| `APP_CHAT_LABELS` | `[]` | JSON list of `{"label","display_name"}` the model may choose from; empty fails closed |
| `APP_CHAT_LABELS_APPROVED` | `false` | `false` keeps `is_demo=true`; set `true` only for the approved D1/D2 taxonomy |
| `APP_CHAT_TIMEOUT_S` | `30` | Provider request timeout in seconds |
| `APP_CHAT_MAX_IMAGE_SIDE` | `1024` | Downscale bound for the JPEG sent to the provider; the stored original is unchanged |
| `APP_MEDIA_ROOT` | `var/media` | Local image storage root; a deployment replaces this with object storage |
| `APP_MAX_UPLOAD_BYTES` | `10485760` | Upload ceiling (10 MB) |
| `APP_MAX_IMAGE_DIMENSION` | `8000` | Decoded image dimension ceiling |
| `APP_VIDEO_MAX_BYTES` | `52428800` | Video upload ceiling (50 MB) |
| `APP_VIDEO_MAX_DURATION_S` | `30` | Clip duration ceiling, enforced during decode |
| `APP_VIDEO_MAX_DIMENSION` | `1920` | Decoded video dimension ceiling |
| `APP_VIDEO_SAMPLE_FPS` | `2` | Target frame-sampling rate |
| `APP_VIDEO_MAX_FRAMES` | `24` | Hard cap on sampled frames; widens the stride for long clips |
| `APP_VIDEO_FRAME_MAX_SIDE` | `1024` | Downscale bound for sampled frames and the preview |
| `APP_VIDEO_MIN_USABLE_FRAMES` | `3` | Below this the reading abstains |
| `APP_VIDEO_MIN_DURATION_MS` | `500` | Shorter clips abstain |
| `APP_VIDEO_ASSESS_FRAMES` | `3` | Maximum frames sent to the assessment engine |
| `APP_VIDEO_TRACK_IOU` / `APP_VIDEO_TRACK_MAX_AGE` | `0.3` / `5` | Tracker association threshold and coasting age |
| `APP_VIDEO_MOTION_THRESHOLD` / `APP_VIDEO_MOTION_MIN_AREA_FRACTION` | `25` / `0.005` | Demo motion-detector sensitivity and minimum region area |
| `APP_CORS_ORIGINS` | `["http://localhost:3000"]` | JSON list of allowed browser origins |
| `APP_AUTH_SECRET` | dev-only value | HS256 secret for access/MFA tokens and OTP hashing; production requires ≥32 chars and refuses the dev default |
| `APP_AUTH_*_TTL_*` / limits | see `core/config.py` | Access/refresh/MFA/OTP lifetimes, OTP and lockout limits |
| `APP_AUTH_DELETION_RETENTION_DAYS` | unset | D10 is open; unset means soft delete with no hard-delete date |
| `APP_AUTH_BOOTSTRAP_ADMIN_*` | unset | One-time first-admin email/password/TOTP seed; all three required together and never logged |

## Identity (spec 03 §5.2)

`app/modules/identity/` provides phone OTP for farmers, provisioned staff accounts,
five roles, password + TOTP staff login, rotating refresh tokens, versioned consent,
privacy requests/self-export/soft deletion and audit events. Routes are
`/v1/auth/*`, `/v1/me/*` and `/v1/admin/*`.

This slice is **in memory** and has no Alembic migration yet; restarting the process
clears users, sessions and consents. The pre-existing demo chat/assessment/advisory/map
routes are still unauthenticated. Real SMS delivery and password reset need providers
that are not chosen; production OTP delivery fails closed. Passwords use stdlib
`scrypt` rather than Argon2id to avoid an unapproved dependency. D10 (retention) and
D11 (on-behalf/offline sessions) remain open.

## Chat (spec 08 §5.7)

`app/modules/conversations/` serves the persisted chat slice: conversation list,
thread, message send, retry and expert-review request. Routes are
`/v1/conversations*` and `/v1/uploads*`; unlike identity, this state survives a
restart.

1. `POST /v1/uploads` decodes the image, enforces `APP_MAX_UPLOAD_BYTES` and
   `APP_MAX_IMAGE_DIMENSION`, stores it under `APP_MEDIA_ROOT` and returns an
   `upload_id`. The chat message references that id — it never carries image
   bytes.
2. `POST /v1/conversations/{id}/messages` runs the demo quality gate, then the
   pluggable `AssessmentEngine`. `APP_CHAT_ENGINE=demo` serves the labelled
   `demo-chat-0.1` engine; `APP_CHAT_ENGINE=openai_compatible` calls a vision
   model; any other value returns `model_not_configured` instead of guessing.
3. Replies are structured assessment cards (`state`, reason, candidates,
   confidence band, model version, `generated_at`, `is_demo`). Photo assessment is
   never merged with area outlook, and abstention is a first-class state.
4. `chat-safety-0.1` validates reply text before storage. A blocked reply is
   stored as `failed` with `unsafe_content_blocked`, no candidates and
   `next_steps=["request_review"]`; the text is withheld, not softened.
5. `POST /v1/conversations/{id}/messages/{message_id}/review` writes to
   `chat_review_requests`, deliberately separate from the observation
   `review_requests` table.

Sends are idempotent per `Idempotency-Key`, so a retried request replays the
stored turn. `DELETE /v1/conversations/{id}` is a soft delete (`deleted_at`);
image files are not reclaimed yet because no retention job exists. The slice is
unauthenticated and demo-only: `plant_presence` is a green-pixel heuristic, not a
detector, and no real model is connected.

### Real provider (OpenAI-compatible)

Set `APP_CHAT_ENGINE=openai_compatible` plus `APP_CHAT_API_KEY`,
`APP_CHAT_MODEL` and `APP_CHAT_LABELS` in the untracked `.env`. The adapter
posts a downscaled JPEG and the allowed label list to
`{APP_CHAT_BASE_URL}/chat/completions` and accepts JSON-only candidates. It does
not serve free-form model text: the server renders the reply from fixed
templates, and `chat-safety-0.1` still runs before storage. Unknown labels are
dropped; a model abstention becomes `abstained`/`model_abstained`; timeouts,
HTTP failures and malformed output become explicit `failed` states with no
candidates.

`APP_CHAT_LABELS` is the approved taxonomy, not a code default (D1/D2 are open).
Until it is the approved set and `APP_CHAT_LABELS_APPROVED=true`, every result
keeps `is_demo=true` and says so in the reason text. The adapter is verified with
a mock transport and a live uvicorn run against a local OpenAI-compatible stub;
no real vendor call has been made from this repository.

## Video reading (spec 09)

`app/modules/video/` serves a bounded, non-diagnostic reading of a short clip.
Routes are `POST /v1/videos`, `GET /v1/videos/{id}`,
`GET /v1/videos/{id}/preview` and `POST /v1/videos/{id}/read`. Uploading is
separate from reading so the client controls when decode and model work runs.

1. `POST /v1/videos` accepts MP4, MOV or WebM, enforces `APP_VIDEO_MAX_BYTES`,
   probes the clip and rejects anything over the duration or dimension ceiling
   before storing it under `APP_MEDIA_ROOT`. A clip that cannot be decoded is
   deleted and no row is written.
2. Reading samples frames deterministically (`APP_VIDEO_SAMPLE_FPS`, capped by
   `APP_VIDEO_MAX_FRAMES`), runs each through the existing image-quality gate,
   then the `demo-motion-0.1` frame-difference detector and the
   `bytetrack-lite-0.1` tracker.
3. At most `APP_VIDEO_ASSESS_FRAMES` usable frames go through the configured
   `AssessmentEngine`. The response contains per-frame photo assessments and
   track summaries, plus a template-only summary — never a video-level
   diagnosis, severity, yield loss, area outlook or pest identity from a
   tracker id.
4. A clip with too few usable frames, no stable region or too short a duration
   returns `abstained` with a machine reason. Decode, engine and content-safety
   failures are explicit `failed` states with no candidates.
5. Readings are append-only (`video_readings`); re-reading a clip creates a new
   row. Every reading is `is_demo=true`, `calibrated=false`,
   `requires_review=true` and `confidence_band=not_calibrated` while the shipped
   detector is a demo heuristic (D15). `chat-safety-0.1` validates the summary
   and candidate names before storage.

`demo-motion-0.1` is a frame-difference heuristic, not a pest detector, and
`bytetrack-lite-0.1` is a dependency-light reimplementation rather than the
official ByteTrack package. No trained detector, retention job (D14) or
chat-composer video UI exists yet.

## Migrations

`0001_baseline` is intentionally empty: it exists so later feature tables are
additive revisions with a parent. `0002_chat_persistence` adds the five chat
tables (`conversations`, `messages`, `message_events`, `image_uploads`,
`chat_review_requests`). `0003_video_persistence` adds `video_uploads` and the
append-only `video_readings`, with a downgrade that drops the readings before
the uploads and leaves the chat tables untouched. The collaborator domain tables
in `app/db/models.py` are still not migrated. Review every autogenerated
revision; production is forward-only and each migration carries a rollback note.

```bash
.venv\Scripts\python -m alembic revision --autogenerate -m "add observations"
.venv\Scripts\python -m alembic upgrade head
```

## Container

`Dockerfile` builds a runtime-only image (no pytest/ruff), runs as a non-root
user and probes `/health`. `../deploy/docker-compose.yml` applies migrations
before starting uvicorn. Local image builds were **not** verified here because
the Docker daemon was unavailable; CI builds both images.

## Rules

- Routers parse, authorise, delegate and serialise. No business logic, no SQL.
- Repositories hold queries; services hold decisions.
- A module never imports another module's repository or ORM model.
- No endpoint returns model scores as a diagnosis; no chemical advice.
- Logs are one JSON event per line and never include payloads, image bytes,
  coordinates, free-text notes or secrets.
