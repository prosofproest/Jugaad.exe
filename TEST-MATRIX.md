# Test matrix — Phase 2 §5.1 engineering foundation

**Scope:** these rows verify the scaffolding, contract and pipeline only. Feature
acceptance tests for capture, review and chat arrive with the feature slices in
Phase 2; rows for those are listed as **planned** and must not be read as evidence.

**Status:** `Verified` (command run in this repository, with the recorded result),
`Defined` (automated check exists but has not run on this machine), `Planned`
(no automated check yet), `Manual` (only a human check exists).

**Last verified:** 2026-11-06 on Windows 11, Python 3.14.5 (runtime target 3.12),
Node 24.14.0, npm 11.9.0, Docker client 29.8.0 (daemon not running), git 2.52.0.
Flutter is not installed.

---

## 1. Foundation checks (implemented in this change)

| ID | Requirement / rule | Scenario | Expected result | Evidence | Status |
|---|---|---|---|---|---|
| FND-01 | AGENTS R1; TRD-O-01 | OpenAPI contract is inspected for merged outputs | No `/v1/forecasts` or `/v1/assessments` path; assessment and outlook stay separate | `backend/tests/test_openapi.py::test_two_outputs_are_not_merged_in_the_contract` | Verified |
| FND-02 | §5.1 “define API versioning” | Every feature route is listed in the published schema | Only `/v1/*` feature routes plus `/health`; no `/v2` | `backend/tests/test_openapi.py::test_single_versioned_prefix_is_used` | Verified |
| FND-03 | TRD §7.2 error format | Request an unknown route | `404`, `application/problem+json`, stable `code`, non-empty `request_id`, `fields: []` | `backend/tests/test_errors.py::test_unknown_route_returns_problem_details` | Verified |
| FND-04 | TRD §7.2 error format | Post an over-long conversation title | `422` with `code=validation_error` and the offending field named | `backend/tests/test_errors.py::test_validation_error_lists_fields` | Verified |
| FND-05 | TRD §15.1 structured logging | Format a log record with an extra field | One JSON line; `ts`, `level`, `event`, extra field; no newline | `backend/tests/test_logging.py::test_log_event_is_one_json_line` | Verified |
| FND-06 | TRD §15.1; CHAT-NF-05 | Log inside a request context / with an exception | `request_id` attached; only `error_type` kept, payload text absent | `backend/tests/test_logging.py` (two tests) | Verified |
| FND-07 | TRD-O-08 observability | Call liveness; supply `X-Request-ID` | `200`; supplied id preserved, otherwise minted and unique per request | `backend/tests/test_request_context.py`, `test_health.py`, `test_errors.py::test_health_is_still_reachable_without_auth` | Verified |
| FND-08 | §5.1 migrations | Generate migration SQL without a live database | `alembic history` shows `0001_baseline`; `alembic upgrade head --sql` emits transactional SQL | `cd backend && alembic history && alembic upgrade head --sql`; CI backend job | Verified |
| FND-09 | §5.1 lint/test runners (backend) | Run the backend suite and linters | 16 tests pass; `ruff check` clean; `ruff format --check` clean | `cd backend && pytest && ruff check app tests && ruff format --check app tests` | Verified |
| FND-10 | §5.1 web app scaffold | Typecheck, lint and production-build the Next.js client | No type errors, no lint errors, build emits `/`, `/_not-found`, `/chat` | `cd frontend && npm run typecheck && npm run lint && npm run build`; CI frontend job | Verified |
| FND-11 | §5.1 mobile app scaffold | Analyze and test the Flutter client | `flutter analyze` clean; widget test passes | `.github/workflows/ci.yml` mobile job (`flutter analyze`, `flutter test`) | Defined — local run blocked (no Flutter SDK) |
| FND-12 | §5.1 local compose | Parse and interpolate the stack with the example env file | Exit `0`, no unresolved variables | `docker compose --env-file deploy/.env.example -f deploy/docker-compose.yml -f deploy/docker-compose.dev.yml config --quiet` | Verified |
| FND-13 | §5.1 secret management | Inspect tracked files for credentials | Only `.env.example`/`.env.staging.example` are tracked; compose fails closed when `POSTGRES_PASSWORD` is unset; the `.env` file is git-ignored | `deploy/docker-compose.yml` `:?` guard; `.gitignore`; CI image build | Verified |
| FND-14 | §5.1 OpenAPI publication | Request `/openapi.json` as a client; boot with `APP_ENVIRONMENT=production` | Schema served in dev with title and version; `docs_url` and `openapi_url` are `None` in production | `backend/tests/test_openapi.py::test_openapi_is_published`; `APP_ENVIRONMENT=production python -c "from app.main import create_app; ..."` → both `None` | Verified |
| FND-15 | §5.1 container images | Build API and web images from a clean checkout | Both builds succeed; containers run non-root | `.github/workflows/ci.yml` `Deploy` job | Defined — local Docker daemon unavailable |
| FND-16 | AGENTS R6; CHAT-06 | Inspect the scaffold chat reply | Assistant reply is `is_demo: true`, `state: abstained`, names `model_version`, contains no diagnosis | `backend/app/modules/conversations/service.py`; manual `POST /v1/conversations/{id}/messages` | Manual |
| FND-17 | §5.1 three coordinated deliverables | Run `uvicorn` and `next start`, load `/` | Home returns `200` and renders “API reachable” from the API `/health` payload | Manual smoke on 2026-11-06: status 200, `API reachable=True`, `PS-03 API=True` | Verified |

---

## 2. Feature requirements touched by the scaffold (not yet accepted)

These rows name the requirement each slice must satisfy. They are **Planned**
unless an automated test is explicitly named, and they do not close Phase 2.

| Requirement | Scenario | Expected result | Planned evidence | Status |
|---|---|---|---|---|
| FR-02-17 / CHAT-03 | Retry a send with the same `client_message_id` | Exactly one user message and one assistant reply; retry returns the stored pair | Automated backend test for `send_message` idempotency; manual smoke on 2026-11-06 returned the same message id and `GET …/messages` listed 2 rows (`user,assistant`) | Manual — automated test planned |
| FR-02-20 / CHAT-04 | Go offline, queue a message, reconnect | Message shows `queued`, is sent once on reconnect with the same key | Mobile/Web offline queue test (no offline store yet) | Planned |
| CHAT-05 / CHAT-06 | Render an assistant reply | Structured card with candidates, confidence band, `model_version`, `generated_at`, `calibrated`; no free-form diagnosis | Component test with a fixture assessment | Planned |
| CHAT-07 | Send an unusable image | Reply is `abstained` with a machine reason, plain-language text and retake action | API test for quality-gate failure (gate not built) | Planned |
| CHAT-08 | Send an unsupported crop | Supported list + escalation; no forced class | API test with unsupported crop fixture | Planned |
| CHAT-10 | Ask for a chemical treatment | Validator blocks the reply; no chemical name, dose, interval or legal-use text | Validator unit test (validator not built) | Planned |
| CHAT-11 / R1 | View a chat reply that has an area outlook available | Two separate cards; the outlook is linked, never merged into the assessment | UI test plus contract assertion (contract half covered by FND-01) | Planned |
| CHAT-14 | Upload or assessment fails | Retry action shown; never a fabricated result | Web/mobile failure-path test | Partially manual (web retry reuses the key) |
| FR-02-23 / FR-02-24 | Open a result screen | `AssessmentCard` and `OutlookCard` are distinct; outcome states drive the card | Component test | Planned |
| FR-04-14 | Reviewer records a decision | Immutable review event + audit event written in the same transaction | API + database test (feature not built) | Planned |
| 03 §3 permission matrix | Farmer reads another owner’s conversation | `404`, never the record; staff access is role-scoped and audited | Auth integration test (auth not built) | Planned |
| TRD-O-08 rollback | Apply migrations from zero, then downgrade/restore | Baseline creates no tables beyond `alembic_version`; every later revision has a rollback note | Migration test against a scratch PostGIS container | Planned |

---

## 3. How to reproduce the verified rows

```bash
# Backend
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt    # POSIX: .venv/bin/python
.venv/Scripts/python -m pytest
.venv/Scripts/python -m ruff check app tests
.venv/Scripts/python -m ruff format --check app tests
.venv/Scripts/python -m alembic history
.venv/Scripts/python -m alembic upgrade head --sql

# Web
cd frontend
npm ci
npm run typecheck
npm run lint
npm run build

# Deploy (client-side parse; needs no daemon)
docker compose --env-file deploy/.env.example \
  -f deploy/docker-compose.yml -f deploy/docker-compose.dev.yml config --quiet

# Mobile (requires the Flutter SDK; not installed here)
cd mobile
flutter pub get && flutter analyze && flutter test
```

Manual smoke (two terminals; both processes were started and stopped by hand):

```bash
cd backend && .venv/Scripts/python -m uvicorn app.main:app --port 8000
cd frontend && npm run start        # http://127.0.0.1:3000
# POST /v1/conversations, then POST the same message twice with one
# client_message_id / Idempotency-Key; GET .../messages must list exactly 2 rows.
```

## 4. Gaps

- No database is running locally, so no integration test exercises PostGIS or an
  actual migration apply. `alembic upgrade head --sql` proves the SQL is
  generated, not that it applies.
- No end-to-end test yet (Playwright, Flutter integration, compose smoke test).
- `mobile/` has no platform runners; CI can analyze/test the Dart package but
  cannot build an APK/IPA until `flutter create .` is run and committed.
- Auth, upload, quality gate, reviewer queue and the chat validator are feature
  work, not foundation work. Their rows stay `Planned` until those slices land.
