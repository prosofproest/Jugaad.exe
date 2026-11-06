# Code standards

**Applies to:** `backend/`, `web/`, `mobile/`, `ml/`, `database/`, `deploy/`.
**Principle:** optimise for the next person reading the code at 2 a.m. during a pilot,
not for cleverness.
**Last updated:** 2026-11-06

---

## 1. Universal rules

- **Explicit over implicit.** No hidden global state, no magic configuration lookup in
  business logic.
- **UTC everywhere.** Store `timestamptz`; serialise ISO-8601 with `Z`. Convert only at
  the presentation edge, using the user's locale.
- **No secrets in code, fixtures, logs or client builds.** Environment variables or a
  secret manager only.
- **No PII in logs.** Log identifiers, not names, phone numbers or coordinates.
- **Small, focused changes.** One concern per change. Do not mix refactor with feature.
- **Delete dead code.** No commented-out blocks, no "just in case" flags.
- **Errors are part of the contract.** Every failure path has a defined state and message.
- **Names say what, not how.** `verification_status`, not `status2`; `is_stale`, not
  `flag_a`.
- **No fabricated defaults.** If a value is unknown, represent unknown explicitly.

---

## 2. Python (backend, ML tooling)

**Tooling:** Python 3.12, `ruff` (lint + format), `mypy` (strict for domain modules),
`pytest`, `pytest-asyncio`.

### Style

- Type hints on every public function and method. No bare `Any` in domain code.
- Pydantic v2 models at the boundary; dataclasses or plain classes internally.
- `async def` for I/O paths; no blocking calls inside async code.
- Prefer `pathlib` over string paths.
- Use `Enum` (str-based) for closed sets; store as `text` + check constraint in Postgres.
- Raise domain exceptions (`UnsupportedCropError`, `StaleInputError`); translate to HTTP
  only in the API layer.

### Structure

```
backend/app/
├── api/v1/            # routers: parse, authorise, delegate, serialise
├── core/              # config, security, logging, errors
├── modules/
│   ├── identity/
│   ├── observations/
│   ├── media/
│   ├── inference/
│   ├── forecasts/
│   ├── reviews/
│   ├── advisories/
│   ├── alerts/
│   └── audit/
├── db/                # session, base, models, repositories
└── workers/           # scheduled jobs
```

Rules:

- Routers contain **no business logic** and **no SQL**.
- Repositories contain queries; services contain decisions.
- A module never imports another module's repository or ORM model. It imports the
  module's public service interface.
- Cross-module transactions are explicit and rare; prefer an outbox/job for side effects.

### Database

- `snake_case`, plural table names (`observations`, `image_predictions`).
- Every table: `id` (UUID), `created_at`, `updated_at` (`timestamptz`, default now).
- Foreign keys always declared; `ON DELETE` behaviour explicit.
- Prediction and audit tables are insert-only; enforce with permissions or triggers.
- Use `text` + `CHECK` over native enums for evolvability.
- Store `model_version`, `source_timestamp`, `fetched_at` where applicable.
- Migrations: Alembic, one logical change per revision, forward-only in production,
  with a written rollback note in the PR.

### Tests

- Unit tests for domain rules (abstention, coverage, verification transitions, advisory
  validation, risk-band mapping).
- Integration tests against a real Postgres (testcontainers or compose), not SQLite.
- No network access in unit tests; stub providers behind interfaces.
- Every bug fix gets a regression test.
- Test names describe behaviour: `test_blurry_image_returns_abstained_state`.

---

## 3. TypeScript / Next.js (web portals)

**Tooling:** TypeScript `strict`, ESLint, Prettier, Vitest, Playwright.

- `strict: true`; no `any` without an inline justification comment.
- Types generated from the FastAPI OpenAPI schema (`openapi-typescript`). Do not
  hand-write API response types.
- Server Components by default; client components only for interaction.
- Data fetching through a single typed API client with explicit error handling.
- No database client in the web app. Ever.
- Forms: schema validation (zod) mirrored from the API contract; show field-level errors.
- State: TanStack Query for server state; local state stays local. No global store unless
  proven necessary.
- Accessibility is part of done: labels, focus order, keyboard operation, contrast.
- No inline hex colours or magic spacing; use design tokens (`ui-context.md`).

Component rules:

- One component per file; named export.
- Props typed; no boolean explosions (`isCompact`, `isLoading`, `isError` → model state).
- Presentational components receive data; containers fetch.
- Shared components live in `/components`; feature components live beside their route.

---

## 4. TypeScript / React Native (mobile)

**Tooling:** TypeScript strict, ESLint + Prettier, Zod for runtime schemas, Expo SQLite or
WatermelonDB, Expo Router or React Navigation, Zustand or Redux Toolkit, React Native
Testing Library, Detox or Maestro.

- `strict: true`; no `any` in domain models.
- Discriminated unions for loading/loaded/stale/offline/error.
- Local DB schema versioned with migrations; never drop unsent observations on upgrade.
- All user-facing strings in i18n catalogues (English + Kannada); no hard-coded copy.
- Repository layer abstracts API + local DB; components never call HTTP directly.
- Images: compress before queueing, retain diagnostic detail, record original dimensions.
- Queue operations are idempotent and resumable; persist retry count and last error.
- Component tests for the result cards, quality feedback and stale banner.
- Test on a low-end Android device profile and with airplane mode.

---

## 5. Naming

| Thing | Convention | Example |
|---|---|---|
| Python module | snake_case | `image_predictions.py` |
| Python class | PascalCase | `ForecastService` |
| API path | plural kebab/snake resource | `/v1/observations` |
| JSON field | snake_case | `valid_from` |
| DB table | plural snake_case | `feature_snapshots` |
| TS component | PascalCase file | `RiskBadge.tsx` |
| React Native component | PascalCase | `AssessmentCard` |
| Enum value | snake_case string | `needs_visit` |
| Env var | SCREAMING_SNAKE | `WEATHER_API_KEY` |
| Feature flag | `feature.<area>.<name>` | `feature.forecast.nowcast` |

Boolean names read as assertions: `is_stale`, `has_coverage`, `can_verify`.

---

## 6. API conventions

### Errors

RFC 7807-style, one shape everywhere:

```json
{
  "type": "https://api.example/errors/unsupported-crop",
  "title": "Crop is not supported in this release",
  "status": 422,
  "code": "unsupported_crop",
  "detail": "Supported crops: potato.",
  "request_id": "req_01H...",
  "retryable": false
}
```

- `code` is stable and machine-readable; clients branch on it, never on `detail`.
- Validation errors include a `fields` array.
- Never leak stack traces, SQL or model internals.

### Requests

- `Idempotency-Key` header on any create that can be retried.
- Cursor pagination: `?cursor=&limit=`; response `{items, next_cursor}`.
- Filtering is explicit and whitelisted; no arbitrary query passthrough.
- Uploads: signed Cloudinary upload, content-type and size validated on completion.
- Rate limits per user and per IP on auth and upload endpoints.
- Timestamps are UTC ISO-8601 with `Z`.

### Versioning

- URL version `/v1`; breaking change requires `/v2`, never silent mutation.
- Additive fields are allowed within a version.
- Model version and advisory version are separate from API version and always returned
  where the output depends on them.

---

## 7. Security standards

- Authentication: short-lived access token + rotating refresh token. Staff roles require
  a second factor.
- Authorisation: role dependency on every route; object-level ownership checks for farmer
  resources (a farmer can only read their own observations).
- Passwords (staff): Argon2id. Farmer accounts: phone OTP, rate-limited, no password.
- Uploads: validate magic bytes, size, dimensions; strip EXIF location unless explicitly
  needed and consented; never trust client MIME.
- Image storage: Cloudinary, private by default; signed URLs with short TTL; no public
  delivery URLs.
- Audit: append-only events for review decisions, role changes, exports, config changes
  and sensitive record access.
- Dependencies: pinned, scanned; no unmaintained packages in the request path.
- CORS: explicit allowlist per environment.
- Headers: HSTS, CSP, `X-Content-Type-Options`, frame denial on portals.

---

## 8. Logging and telemetry

Structured JSON, one event per line:

```json
{"ts":"2026-11-06T06:00:00Z","level":"info","event":"forecast.issued",
 "request_id":"req_...","forecast_id":"fcst_...","crop":"potato",
 "target":"late_blight","geo_code":"DEMO_BLOCK","risk_band":"moderate",
 "coverage":"good","model_version":"forecast-0.1.0"}
```

- Include `request_id` on every request; propagate to jobs.
- Log state transitions, not payloads.
- Metrics that must exist: request latency/error rate, upload success, queue depth, sync
  success, inference latency, abstention rate, forecast no-score rate, alert delivery rate.
- Never log image bytes, phone numbers, exact coordinates or free-text notes.

---

## 9. Git and review

- Conventional commits: `feat(forecast): add coverage gate`, `fix(sync): dedupe retry`.
- Branch per change; small PRs (< ~400 changed lines where practical).
- PR description states: requirement IDs, what changed, how tested, risk, rollback.
- No secrets, no real farmer data, no large binaries in git.
- Migration PRs include the rollback note and the data-impact assessment.
- A reviewer checks the `AGENTS.md` definition of done, not just compilation.

---

## 10. Review checklist

- [ ] Requirement ID referenced and implemented.
- [ ] Failure paths handled (unsupported, stale, offline, unauthorised, duplicate).
- [ ] No R1–R10 violation (see `AGENTS.md` §3).
- [ ] Tests added, including one negative case; suite passes.
- [ ] Types complete; no unexplained `Any`/`any`.
- [ ] No PII/secrets in logs, fixtures or commits.
- [ ] Schema change has a migration and rollback note.
- [ ] API change reflected in OpenAPI and the feature spec.
- [ ] User-facing copy follows `ui-context.md`.
- [ ] `progress-tracker.md` updated.

---

## 11. ML and data code standards

Applies to `ml/`, training notebooks that are promoted, and data pipelines.

### 11.1 Reproducibility

- A model artefact records: code commit, dataset version, split version, preprocessing
  config, architecture, hyperparameters, library versions and random seed.
- Training code is a module, not an untracked notebook. Notebooks may explore; only reviewed
  code trains a shipped model.
- Preprocessing is generated from one config shared by training and serving.
- Every artefact has a checksum and a `model_registry` row.

### 11.2 Data handling

- Raw data is immutable; cleaning is reproducible code producing a versioned dataset.
- No `pd.read_csv` of an unversioned path in a training entrypoint.
- No imputation without a recorded flag and method; weather gaps force `insufficient_data`,
  not a filled value.
- No training or evaluation on a dataset without a documented permission record.
- Demo/synthetic rows carry `is_demo = true`; never mix into production automatically.

### 11.3 Evaluation honesty

- Report macro F1, per-class recall, calibration (ECE/reliability), abstention rate and
  sample counts together.
- Evaluate at the shipped abstention threshold, not the best threshold.
- Use grouped image splits and chronological/spatial forecast splits.
- Freeze the test set before model selection; open it once.
- Write "not measured" when a number cannot be computed. Never estimate a metric.

### 11.4 Model serving

- Serving requires a registry status of `approved`; refuse unregistered/unapproved models.
- Predictions are insert-only and carry `model_version`, `generated_at`, input snapshot
  reference and calibration status.
- A model never writes verification status.
- Previous model versions are retained for rollback.

---

## 12. Testing strategy by layer

| Change | Minimum evidence |
|---|---|
| Domain rule | Unit test, positive + negative |
| API endpoint | Contract test + auth test (403 for wrong role) |
| Migration | Apply on empty DB + apply on seeded DB; rollback note |
| Sync/queue | Duplicate retry, interrupted upload, offline start |
| Image pipeline | Quality-gate unit tests; abstention path; version recorded |
| Forecast | Snapshot immutability; no-score on stale input; unverified excluded |
| Map layer | Verified/unverified/risk separation; suppression threshold |
| Advisory | Validator rejects chemical content; approval required before retrieval |
| UI screen | Component/golden test for each state in `ui-context.md` §6 |
| Model training | Reproducible run from recorded config; frozen split hash |

### 12.1 Test data

- Synthetic images and fake identifiers only. No real farmer data in fixtures, screenshots
  or demos.
- Integration tests run against a real PostgreSQL (testcontainers or compose), never SQLite.
- No network access in unit tests; stub providers behind interfaces.
- Every bug fix gets a regression test.

### 12.2 Reporting results

- Report commands exactly as run and the pass/fail counts.
- If a suite was not run, say so and why. "Should work" is not a verification result.

---

## 13. Monitoring code standards

- Emit structured events for state transitions, not payloads.
- Required metrics: request latency/error rate, upload success, queue depth, sync success,
  inference latency, abstention rate, forecast no-score rate, alert delivery rate,
  data freshness lag.
- Never log image bytes, phone numbers, exact coordinates or free-text notes.
- Every metric and alert has an owner and a runbook entry before pilot launch.
- Dashboards distinguish data problems (stale, missing) from model problems (drift,
  calibration) from product problems (latency, failures).
