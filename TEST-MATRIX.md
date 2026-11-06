# Test matrix — Phase 2 §5.1 engineering foundation

**Scope:** these rows verify the scaffolding, contract and pipeline only. Feature
acceptance tests for capture, review and chat arrive with the feature slices in
Phase 2; rows for those are listed as **planned** and must not be read as evidence.

**Status:** `Verified` (command run in this repository, with the recorded result),
`Defined` (automated check exists but has not run on this machine), `Planned`
(no automated check yet), `Manual` (only a human check exists).

**Last verified:** 2026-11-06 on Windows 11, Python 3.14.5 (runtime target 3.12),
Node 24.14.0, npm 11.9.0, Docker client 29.8.0 (daemon not running), git 2.52.0,
Flutter 3.47.9 / Dart 3.13.7.

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
| FND-09 | §5.1 lint/test runners (backend) | Run the backend suite and linters | 294 tests pass; targeted `ruff check` clean (identity slice); `ruff format --check` clean on the identity slice | `cd backend && pytest && ruff check app/modules/identity app/api/v1/auth.py app/api/v1/me.py app/api/v1/admin.py tests/test_identity_*.py tests/support_identity.py` | Verified |
| FND-10 | §5.1 web app scaffold | Typecheck, lint and production-build the Next.js client | No type errors, no lint errors, build emits `/`, `/_not-found`, `/chat`, `/chat/[conversationId]`, `/outlook`, `/review` | `cd frontend && npm run typecheck && npm run lint && npm run build`; CI frontend job | Verified |
| FND-11 | §5.1 mobile app scaffold | Analyze and test the Flutter client | `flutter analyze` clean; widget test passes | Local run on 2026-11-06 with Flutter 3.47.9 / Dart 3.13.7: `flutter pub get` (30 packages), `flutter analyze` → “No issues found!”, `flutter test` → 1 test passed; `.github/workflows/ci.yml` mobile job mirrors the same commands | Verified (analyze + test; no APK or device run) |
| FND-12 | §5.1 local compose | Parse and interpolate the stack with the example env file | Exit `0`, no unresolved variables | `docker compose --env-file deploy/.env.example -f deploy/docker-compose.yml -f deploy/docker-compose.dev.yml config --quiet` | Verified |
| FND-13 | §5.1 secret management | Inspect tracked files for credentials | Only `.env.example`/`.env.staging.example` are tracked; compose fails closed when `POSTGRES_PASSWORD` is unset; the `.env` file is git-ignored | `deploy/docker-compose.yml` `:?` guard; `.gitignore`; CI image build | Verified |
| FND-14 | §5.1 OpenAPI publication | Request `/openapi.json` as a client; boot with `APP_ENVIRONMENT=production` | Schema served in dev with title and version; `docs_url` and `openapi_url` are `None` in production | `backend/tests/test_openapi.py::test_openapi_is_published`; `APP_ENVIRONMENT=production python -c "from app.main import create_app; ..."` → both `None` | Verified |
| FND-15 | §5.1 container images | Build API and web images from a clean checkout | Both builds succeed; containers run non-root | `.github/workflows/ci.yml` `Deploy` job | Defined — local Docker daemon unavailable |
| FND-16 | AGENTS R6; CHAT-06 | Inspect the scaffold chat reply | Assistant reply is `is_demo: true`, `state: abstained`, names `model_version`, contains no diagnosis | `backend/app/modules/conversations/service.py`; manual `POST /v1/conversations/{id}/messages` | Manual |
| FND-17 | §5.1 three coordinated deliverables | Run `uvicorn` and `next start`, load `/` | Home returns `200` and renders “API reachable” from the API `/health` payload | Manual smoke on 2026-11-06: status 200, `API reachable=True`, `PS-03 API=True` | Verified |
| FND-18 | §5.7 web chat surface (demo backend) | Create a conversation, list it, open the thread and delete it | `/chat` lists the conversation; `/chat/{id}` renders title, `demo` badge and the abstained assessment; delete returns the empty state | Manual smoke on 2026-11-06 against the local API; `npm run build` emits both routes | Verified (manual) |
| FND-19 | R1/R3/R4; §5.7 boundary | Open the two non-chat output surfaces | `/outlook` shows "not available" and issues no score; `/review` is locked and renders no fabricated cases; both routes are in the production build | `frontend/app/outlook/page.tsx`, `frontend/app/review/page.tsx`; `npm run build` on 2026-11-06 | Verified (source + build) |

---

## 2. Feature requirements touched by the scaffold (not yet accepted)

These rows name the requirement each slice must satisfy. They are **Planned**
unless an automated test is explicitly named, and they do not close Phase 2.

| Requirement | Scenario | Expected result | Planned evidence | Status |
|---|---|---|---|---|
| FR-02-17 / CHAT-03 | Retry a send with the same `client_message_id` | Exactly one user message and one assistant reply; retry returns the stored pair | Automated backend test for `send_message` idempotency; manual smoke on 2026-11-06 returned the same message id and `GET …/messages` listed 2 rows (`user,assistant`) | Manual — automated test planned |
| CHAT-01 | Open the conversation list and a thread on web | Both routes render; list is served by `/v1/conversations` | FND-18 live smoke; `frontend/app/chat/page.tsx`, `[conversationId]/page.tsx` | Verified (manual) |
| CHAT-02 | Attach an image in the web composer | File picker and drag-and-drop show a preview; filename metadata is sent, no bytes | Manual UI check; `frontend/components/chat-composer.tsx` | Partially verified — upload pipeline not built |
| CHAT-04 | Go offline, queue a message, reconnect | Message shows `queued`, is sent once on reconnect with the same key | Mobile offline queue test (no offline store yet); web shows an offline notice and retries by hand | Planned |
| CHAT-05 / CHAT-06 | Render an assistant reply | Structured card with candidates, confidence band, `model_version`, `generated_at`, `calibrated`; no free-form diagnosis | `frontend/components/assessment-card.tsx`; FND-18 live smoke | Manual — component test planned |
| CHAT-07 | Send an unusable image | Reply is `abstained` with a machine reason, plain-language text and retake action | API test for quality-gate failure (gate not built) | Planned |
| CHAT-08 | Send an unsupported crop | Supported list + escalation; no forced class | API test with unsupported crop fixture | Planned |
| CHAT-10 | Ask for a chemical treatment | Validator blocks the reply; no chemical name, dose, interval or legal-use text | Validator unit test (validator not built) | Planned |
| CHAT-11 / R1 | View a chat reply that has an area outlook available | Two separate cards; the outlook is linked, never merged into the assessment | UI test plus contract assertion (contract half covered by FND-01) | Planned |
| CHAT-14 | Upload or assessment fails | Retry action shown; never a fabricated result | Web retry reuses the same `client_message_id`; no automated failure-path test | Partially verified (manual) |
| CHAT-15 | Conversation list context | Title, last-activity time and an open link | FND-18 live smoke; `frontend/components/chat-index.tsx` | Verified (manual) |
| CHAT-16 | Delete a conversation | Confirm step, `DELETE`, item removed and empty state shown | FND-18 live smoke; `frontend/components/chat-index.tsx` | Verified (manual) |
| FR-02-23 / FR-02-24 | Open a result screen | `AssessmentCard` and `OutlookCard` are distinct; outcome states drive the card | Component test | Planned |
| FR-04-14 | Reviewer records a decision | Immutable review event + audit event written in the same transaction | API + database test (feature not built) | Planned |
| 03 §3 permission matrix | Farmer reads another owner’s conversation | `404`, never the record; staff access is role-scoped and audited | Conversation ownership is still unimplemented: the demo chat store has no owner field and its routes are unauthenticated (IDN-03 covers only the new `/v1/me` and `/v1/admin` routes) | Planned |
| TRD-O-08 rollback | Apply migrations from zero, then downgrade/restore | Baseline creates no tables beyond `alembic_version`; every later revision has a rollback note | Migration test against a scratch PostGIS container | Planned |

---

## 2a. Identity, roles, consent and privacy slice (Phase 2 §5.2)

Implemented in memory on 2026-11-06. These rows prove the service/HTTP contract only;
they do **not** prove durability, real SMS delivery, case retention/deletion, or
object-level scoping on the still-unauthenticated demo feature routes.

| ID | Requirement / rule | Scenario | Expected result | Evidence | Status |
|---|---|---|---|---|---|
| IDN-01 | 03 §4.1 | Request then verify a farmer OTP | Farmer created/reused; code expires, is single-use, attempt-capped and rate-limited; code never appears in a response, log or audit detail | `test_identity_otp.py`, `test_identity_api.py::test_otp_http_flow_never_returns_the_code` | Verified (in-memory) |
| IDN-02 | 03 §2, §4.2 | Provision staff; log in with password then TOTP | Only the four staff roles can be provisioned; `pathologist`/`agronomist`/`admin` require MFA; wrong TOTP and lockout are refused | `test_identity_staff.py`, `support_identity.py` | Verified (in-memory) |
| IDN-03 | 03 §2, §6 | Call `/v1/me` and `/v1/admin/users` without/with the wrong role | `401` without a token, `403` for `farmer` on admin routes | `test_identity_api.py::test_protected_routes_reject_a_missing_token`, `test_farmer_can_read_own_profile_but_not_the_admin_surface` | Verified (new routes only) |
| IDN-04 | 03 §4.3, §9 | Reuse a rotated refresh token; change a role or disable an account | The family is revoked, old access/refresh tokens fail, and re-login is required | `test_identity_otp.py::test_refresh_rotates_and_reuse_revokes_the_whole_family`, `test_identity_staff.py` role/status tests | Verified (in-memory) |
| IDN-05 | 03 §5 | Read/accept/withdraw versioned consent | Version, timestamp, channel and text hash are recorded; required consent gates actions; optional research consent does not; a version change forces re-consent | `test_identity_consent_privacy.py` | Verified (in-memory) |
| IDN-06 | 03 §7 | Export own data; file a privacy request; delete the account | Export requires a written purpose and contains only the caller's records; queued reports must be resolved; deletion is soft unless D10 supplies a retention policy | `test_identity_consent_privacy.py`, `test_identity_api.py` | Verified (soft delete only) |
| IDN-07 | 03 §11 | Change a role, view a user record, run an export, run retention | Each writes an audit event with actor and reason/purpose; no full phone, email, password, OTP or MFA secret is present | `test_identity_staff.py`, `test_identity_consent_privacy.py` | Verified (in-memory) |
| IDN-08 | 03 §8 | Inspect the OpenAPI document | Auth/me/admin paths are published; bearer security is declared; public OTP/login/MFA/refresh routes have no security requirement | `test_identity_api.py::test_identity_routes_are_published_with_bearer_security` | Verified |
| IDN-09 | AGENTS R9; D10 | Run the retention job | Only expired OTP/refresh/MFA credentials are purged; case/image/derived-data retention is explicitly **not** implemented | `test_identity_consent_privacy.py::test_retention_job_purges_only_short_lived_credentials_and_records_a_reason` | Verified (credential-only) |

**Known gaps:** process-local storage; no Alembic identity migration; demo feature
routes are not authenticated; no real SMS/email provider (production OTP fails closed);
no password reset; scrypt rather than Argon2id; D10/D11 behaviour intentionally absent.

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

# Mobile (verified 2026-11-06 with Flutter 3.47.9 / Dart 3.13.7)
cd mobile
flutter pub get && flutter analyze && flutter test
# APK build still needs platform runners: flutter create . --platforms=android,ios
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
- The web chat surface is wired to the in-memory demo backend: no image upload, no
  inference, no auth, and no component/E2E test. Its live-smoke rows are manual.
- `design/tokens.json` exists but has no generator yet; `frontend/app/globals.css`
  mirrors the values by hand and must be updated in the same change.
- `mobile/` analyze and test now pass locally, but there are no platform runners;
  neither CI nor this machine can build an APK/IPA until `flutter create .` is run
  and committed. No device or emulator run has been performed.
- Auth, upload, quality gate, reviewer queue and the chat validator are feature
  work. The §5.2 identity slice is implemented in memory (IDN-01…IDN-09) but the
  demo chat/assessment/advisory/map routes are still unauthenticated, so no
  object-level isolation claim can be made for them.
