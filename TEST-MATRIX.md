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
| FND-08 | §5.1 migrations | Generate migration SQL without a live database | `alembic history` shows `0001_baseline` and `0002_chat_persistence`; `alembic upgrade head --sql` emits transactional SQL | `cd backend && alembic history && alembic upgrade head --sql`; CI backend job | Verified |
| FND-09 | §5.1 lint/test runners (backend) | Run the backend suite and linters | 336 tests pass; targeted `ruff check` clean on the identity and chat slices; `ruff format --check` clean on the same slices | `cd backend && pytest && ruff check app/modules/identity app/api/v1/auth.py app/api/v1/me.py app/api/v1/admin.py tests/test_identity_*.py tests/support_identity.py app/core/config.py app/modules/conversations app/api/v1/uploads.py app/api/v1/conversations.py tests/test_chat_api.py tests/test_chat_engine.py tests/test_chat_validator.py` | Verified |
| FND-10 | §5.1 web app scaffold | Typecheck, lint and production-build the Next.js client | No type errors, no lint errors, build emits `/`, `/_not-found`, `/chat`, `/chat/[conversationId]`, `/outlook`, `/review` | `cd frontend && npm run typecheck && npm run lint && npm run build`; CI frontend job | Verified |
| FND-11 | §5.1 mobile app scaffold | Analyze, test, build and smoke-test the Flutter client | `flutter analyze` clean; widget test passes; debug APK is produced; the capture/offline path completes on an emulator | Local run on 2026-11-06 with Flutter 3.47.9 / Dart 3.13.7: `flutter pub get`, `flutter analyze` → “No issues found!”, `flutter test` → **14 tests passed**, `flutter build apk --debug` → `build/app/outputs/flutter-apk/app-debug.apk` (~166 MB, all ABIs, default `http://10.0.2.2:8000`); headless `Medium_Phone_API_36.1` smoke on a separate port-8010 server + fresh Alembic SQLite DB exercised gallery upload, photo-assessment chat, airplane-mode queueing and the 15 s reconnect flush; `.github/workflows/ci.yml` mobile job mirrors pub get/analyze/test | Verified (analyze + test + debug APK + headless emulator smoke; no physical device or iOS run) |
| FND-12 | §5.1 local compose | Parse and interpolate the stack with the example env file | Exit `0`, no unresolved variables | `docker compose --env-file deploy/.env.example -f deploy/docker-compose.yml -f deploy/docker-compose.dev.yml config --quiet` | Verified |
| FND-13 | §5.1 secret management | Inspect tracked files for credentials | Only `.env.example`/`.env.staging.example` are tracked; compose fails closed when `POSTGRES_PASSWORD` is unset; the `.env` file is git-ignored | `deploy/docker-compose.yml` `:?` guard; `.gitignore`; CI image build | Verified |
| FND-14 | §5.1 OpenAPI publication | Request `/openapi.json` as a client; boot with `APP_ENVIRONMENT=production` | Schema served in dev with title and version; `docs_url` and `openapi_url` are `None` in production | `backend/tests/test_openapi.py::test_openapi_is_published`; `APP_ENVIRONMENT=production python -c "from app.main import create_app; ..."` → both `None` | Verified |
| FND-15 | §5.1 container images | Build API and web images from a clean checkout | Both builds succeed; containers run non-root | `.github/workflows/ci.yml` `Deploy` job | Defined — local Docker daemon unavailable |
| FND-16 | AGENTS R6; CHAT-05/06 | Inspect a demo chat reply | A passing image yields `state: assessed`, `is_demo: true`, `calibrated: false`, three synthetic candidates and `model_version: demo-chat-0.1`; a text-only or failed-quality turn abstains | `backend/tests/test_chat_api.py`; live smoke on 2026-11-06 | Verified |
| FND-17 | §5.1 three coordinated deliverables | Run `uvicorn` and `next start`, load `/` | Home returns `200` and renders “API reachable” from the API `/health` payload | Manual smoke on 2026-11-06: status 200, `API reachable=True`, `PS-03 API=True` | Verified |
| FND-18 | §5.7 web chat surface (demo engine) | Upload a photo, send it, open the thread and request review | `/chat` lists the conversation; `/chat/{id}` renders the uploaded preview, demo assessment, quality flags and review status; delete returns the empty state | Live smoke on 2026-11-06 (uvicorn + SQLite + `next start`); `npm run build` emits both routes | Verified (manual) |
| FND-19 | R1/R3/R4; §5.7 boundary | Open the two non-chat output surfaces | `/outlook` shows "not available" and issues no score; `/review` is locked and renders no fabricated cases; both routes are in the production build | `frontend/app/outlook/page.tsx`, `frontend/app/review/page.tsx`; `npm run build` on 2026-11-06 | Verified (source + build) |
| FND-20 | §5.7; CHAT-02 | Upload a non-image and a corrupt image | `415 unsupported_media_type` and `422 invalid_image`; no file is stored | `backend/tests/test_chat_api.py::test_upload_rejects_a_non_image`, `test_upload_rejects_corrupt_bytes` | Verified |
| FND-21 | CHAT-07 | Upload a dark or too-small image and send it | Reply is `abstained` with `quality_gate_failed`, the quality flag and a retake step; no candidates | `backend/tests/test_chat_api.py::test_dark_image_fails_the_demo_quality_gate`, `test_quality_failure_abstains_with_a_retake`, `test_small_image_is_low_resolution` | Verified (demo gate) |
| FND-22 | CHAT-09; CHAT-18 | Request expert review twice on one assistant message | One persisted review request; replay returns the same id; the assessment is unchanged; a user message is rejected with `400` | `backend/tests/test_chat_api.py::test_review_request_is_persisted_and_idempotent`, `test_review_on_a_user_message_is_rejected` | Verified |
| FND-23 | §5.1 schema authority; ADR-002 | Import the domain ORM and the chat ORM into one metadata, then create the schema on SQLite | Both modules import together; no duplicate-table error; `Base.metadata.create_all` creates 48 tables including `chat_review_requests`; the observation `review_requests` table is separate | `python -c "import app.db.models"`; `python -c "from app.db.base import Base; import app.db.models; ...create_all..."` on 2026-11-06 | Verified |
| FND-24 | CHAT-10; AGENTS R5 | Make the assessment engine return chemical advice, then send the turn | The unsafe reply is withheld before storage; the stored assistant message is `failed` with `unsafe_content_blocked`, no candidates, no chemical text; one `validator_rejected` event records the validator version and rule categories only | `backend/tests/test_chat_validator.py` (19 tests); `backend/tests/test_chat_api.py::test_unsafe_reply_is_withheld_before_storage`, `test_unsafe_candidate_name_is_withheld`, `test_safe_engine_reply_is_stored` | Verified |
| FND-25 | CHAT-06; §5.7 engine seam | Call the OpenAI-compatible adapter through a mock transport, then a live HTTP stub | Only configured labels are returned; unknown labels are dropped; malformed output, timeouts and HTTP failures are explicit `failed` states; a model abstention is `abstained`; `is_demo` follows label approval; the stored image is sent as a bounded JPEG and the result is persisted | `backend/tests/test_chat_engine.py` (19 tests); `backend/tests/test_chat_api.py::test_provider_engine_reply_is_persisted`; live uvicorn + local OpenAI-compatible stub: upload → `assessed`, `is_demo=false`, `model_version=stub-vision-1`, one approved candidate, safe text, persisted review, 2 messages | Verified (mock transport + live local stub; no real vendor call) |
| FND-26 | VID-02/03; 09 §7 | Upload a non-video, a corrupt file, an oversized clip and an over-dimension clip | `415 unsupported_media_type`, `415 video_decode_failed`, `413 video_too_large` and `422 video_too_large`; no row or stored file is left behind | `backend/tests/test_video_api.py::test_unsupported_type_is_rejected`, `test_corrupt_video_is_rejected_without_a_row`, `test_oversized_video_is_rejected`, `test_dimension_ceiling_is_enforced` | Verified (synthetic clips) |
| FND-27 | VID-04/05/07/08/09 | Upload a synthetic clip with one growing region, then read it | Deterministic sampling within the frame cap; the quality gate passes; `demo-motion-0.1` and `bytetrack-lite-0.1` versions are reported; one stable track spans ≥2 frames; ≤3 frames carry `assessed` per-frame photo assessments; the summary is non-diagnostic | `backend/tests/test_video_pipeline.py::test_sampling_is_deterministic_and_bounded`, `test_tracker_keeps_one_id_across_low_score_frames`; `backend/tests/test_video_api.py::test_upload_and_read_tracks_a_region`, `test_preview_is_the_first_sampled_frame` | Verified (synthetic clips) |
| FND-28 | VID-06/10; AGENTS R2 | Read a clip with no motion, then a clip that fails the quality gate | `abstained`/`no_stable_region` and `abstained`/`insufficient_usable_frames`; no candidates; `requires_review=true` | `backend/tests/test_video_api.py::test_static_clip_abstains_with_no_stable_region`, `test_dark_clip_abstains_with_insufficient_usable_frames`; `backend/tests/test_video_pipeline.py::test_summary_abstains_without_a_stable_region`, `test_summary_abstains_with_no_frames` | Verified (synthetic clips) |
| FND-29 | VID-11/12/14; CHAT-10; R5/R7 | Crash the assessment engine, return an unsafe candidate, and read the same clip twice | Engine crash → `failed`/`model_unavailable`; unsafe summary → `failed`/`unsafe_content_blocked` with the text withheld; two reads create two append-only rows; every reading is `is_demo=true`, `calibrated=false`, `confidence_band=not_calibrated`, `requires_review=true`; a missing clip is `404` | `backend/tests/test_video_api.py::test_engine_crash_fails_closed`, `test_unsafe_summary_is_blocked`, `test_readings_are_append_only`, `test_missing_video_is_404`, `test_upload_and_read_tracks_a_region` | Verified (synthetic clips) |
| FND-30 | CHAT-02; CHAT-04; spec 08 §10 | Capture an image and send it from the mobile client, then force an offline retry | Multipart upload targets `/v1/uploads` with field `file`; the message carries `image.upload_id` and `Idempotency-Key`; a retry reuses the persisted upload id and one conversation; a missing local image fails without a fabricated reply; the outbox round-trips and a corrupt queue is treated as empty | `mobile/test/api_client_test.dart`, `chat_sync_test.dart`, `outbox_test.dart`, `widget_test.dart`; `flutter analyze` clean; `flutter test` → 14 passed on 2026-11-06; headless emulator smoke uploaded `scaled_38.jpg` (`quality_result=pass`), rendered a demo assessment, then queued in airplane mode and flushed once on reconnect | Verified (unit + headless emulator smoke; no physical device) |

---

## 2. Feature requirements touched by the scaffold (not yet accepted)

These rows name the requirement each slice must satisfy. They are **Planned**
unless an automated test is explicitly named, and they do not close Phase 2.

| Requirement | Scenario | Expected result | Planned evidence | Status |
|---|---|---|---|---|
| FR-02-17 / CHAT-03 | Retry a send with the same `client_message_id` | Exactly one user message and one assistant reply; retry returns the stored pair | `backend/tests/test_chat_api.py::test_assessed_turn_is_persisted_and_idempotent`; live smoke on 2026-11-06 returned the same message ids and `GET …/messages` listed 2 rows (`user,assistant`) | Verified (API + manual) |
| CHAT-01 | Open the conversation list and a thread on web | Both routes render; list is served by `/v1/conversations` | FND-18 live smoke; `frontend/app/chat/page.tsx`, `[conversationId]/page.tsx` | Verified (manual) |
| CHAT-02 | Attach an image in the web composer | File picker and drag-and-drop show a preview; the file is uploaded first and the message references `upload_id` | `frontend/components/chat-composer.tsx`, `chat-thread.tsx`, `lib/api.ts`; `backend/tests/test_chat_api.py` upload tests; live smoke | Verified (API + manual UI; no component test) |
| CHAT-04 | Go offline, queue a message, reconnect | Message shows `queued`, is sent once on reconnect with the same key | Mobile: persisted outbox (`ps03.chat.outbox.v1`), `queued`/`failed` bubbles with Retry/Delete, flush on manual action, 15 s page timer and app resume; `mobile/test/chat_sync_test.dart`, `outbox_test.dart`, FND-30; headless emulator: airplane-mode send stayed `queued` with no fabricated reply, then the 15 s reconnect flush left exactly one user row for that `client_message_id` and one assistant reply. Web: offline notice and manual retry only | Verified (mobile unit + headless emulator; no physical device; web has no durable queue) |
| CHAT-05 / CHAT-06 | Render an assistant reply | Structured card with candidates, quality flags, confidence band, `model_version`, `generated_at`, `calibrated`; no free-form diagnosis | `frontend/components/assessment-card.tsx`; FND-16 API tests; FND-18 SSR smoke | Verified (API + manual SSR; no component test) |
| CHAT-07 | Send an unusable image | Reply is `abstained` with a machine reason, plain-language text and retake action | `backend/tests/test_chat_api.py` quality-gate tests (FND-21); demo gate only | Verified (demo gate) |
| CHAT-09 | Request expert review from a reply | One persisted review request; status visible in the thread; the assessment is unchanged | `backend/tests/test_chat_api.py` review tests (FND-22); `frontend/components/assessment-card.tsx` | Verified (API + manual SSR) |
| CHAT-08 | Send an unsupported crop | Supported list + escalation; no forced class | API test with unsupported crop fixture | Planned |
| CHAT-10 | Ask for a chemical treatment | Validator blocks the reply; no chemical name, dose, interval or legal-use text | `backend/tests/test_chat_validator.py`; `backend/tests/test_chat_api.py` safety-gate tests (FND-24) | Verified |
| CHAT-11 / R1 | View a chat reply that has an area outlook available | Two separate cards; the outlook is linked, never merged into the assessment | UI test plus contract assertion (contract half covered by FND-01) | Planned |
| CHAT-14 | Upload or assessment fails | Retry action shown; never a fabricated result | `test_upload_rejects_a_non_image`, `test_upload_rejects_corrupt_bytes`, `test_quality_failure_abstains_with_a_retake`; web retry reuses the same `client_message_id` | Verified (API + manual UI) |
| CHAT-15 | Conversation list context | Title, last-activity time and an open link | FND-18 live smoke; `frontend/components/chat-index.tsx` | Verified (manual) |
| CHAT-16 | Delete a conversation | Confirm step, `DELETE`, item removed and empty state shown | FND-18 live smoke; `frontend/components/chat-index.tsx` | Verified (manual) |
| FR-02-23 / FR-02-24 | Open a result screen | `AssessmentCard` and `OutlookCard` are distinct; outcome states drive the card | Component test | Planned |
| FR-04-14 | Reviewer records a decision | Immutable review event + audit event written in the same transaction | API + database test (feature not built) | Planned |
| 03 §3 permission matrix | Farmer reads another owner’s conversation | `404`, never the record; staff access is role-scoped and audited | Conversation rows carry `owner_id` and the service scopes every lookup to the fixed `demo_user`; the chat routes are still unauthenticated, so a second user cannot be represented yet. Staff access is not built (IDN-03 covers only the new `/v1/me` and `/v1/admin` routes) | Planned |
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
# dependencies resolved; analyze clean; 14 tests passed
# APK build still needs platform runners: flutter create . --platforms=android,ios
```

Manual smoke (two terminals; both processes were started and stopped by hand):

```bash
cd backend && .venv/Scripts/python -m uvicorn app.main:app --port 8000
cd frontend && npm run start        # http://127.0.0.1:3000
# Upload first, then reference the returned id in the message.
curl -F "file=@leaf.png;type=image/png" http://localhost:8000/v1/uploads
# POST /v1/conversations, then POST the message with {"image":{"upload_id":"..."}}
# twice with one client_message_id / Idempotency-Key; GET .../messages must list
# exactly 2 rows. POST .../messages/{assistant_id}/review, then GET the preview URL.
```

## 4. Gaps

- No PostgreSQL server is running locally, so no integration test exercises PostGIS
  or an actual migration apply. `alembic upgrade head --sql` proves the SQL is
  generated, not that it applies. The chat slice was smoke-tested against a
  file-backed SQLite database using the same SQLAlchemy models.
- No end-to-end test yet (Playwright, Flutter integration, compose smoke test).
- The web chat surface is wired to the persisted demo backend: uploads, demo quality
  gate, deterministic demo engine and review requests work, but there is no real
  inference, no auth and no component/E2E test. Its live-smoke rows are manual.
- `design/tokens.json` exists but has no generator yet; `frontend/app/globals.css`
  mirrors the values by hand and must be updated in the same change.
- `mobile/` analyze and test now pass locally, but there are no platform runners;
  neither CI nor this machine can build an APK/IPA until `flutter create .` is run
  and committed. No device or emulator run has been performed.
- Auth, the reviewer queue and the remaining CHAT requirements are still feature work.
  The chat content-safety validator (CHAT-10) now runs before storage. Upload
  and a demo quality gate now exist; the §5.2 identity slice is implemented in
  memory (IDN-01…IDN-09) but the demo chat/assessment/advisory/map routes are still
  unauthenticated, so no object-level isolation claim can be made for them.
