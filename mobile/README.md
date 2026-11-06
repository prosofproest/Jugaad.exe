# PS-03 mobile client (Flutter)

API-only Flutter client for the PS-03 modular monolith. It consumes the same
versioned `/v1` API as the web app and never connects to the database.

> **Verification status: analyze, test, debug APK and emulator smoke verified
> (2026-11-06).** `flutter pub get`, `flutter analyze`, `flutter test` and
> `flutter build apk --debug` pass with Flutter 3.47.9 / Dart 3.13.7 on
> Windows 11; the suite is **14 tests** and the APK is produced at
> `build/app/outputs/flutter-apk/app-debug.apk`. A headless Android emulator
> smoke exercised gallery capture → `/v1/uploads` → photo-assessment chat,
> airplane-mode queueing, and the 15 s reconnect flush against a fresh
> SQLite/Alembic database. Real-device camera capture and iOS remain
> unverified.

## First run (requires the Flutter SDK)

The platform runners (`android/`, `ios/`) are generated from the Flutter 3.47
templates and committed, so a fresh checkout only needs:

```bash
cd mobile
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Build the debug APK with `flutter build apk --debug`. Regenerating the runners
with `flutter create . --project-name ps03_mobile --platforms=android,ios` is
additive and keeps `lib/`, `test/` and the committed permission entries.

Platform capture configuration (already applied):

- **Android** — `android/app/src/main/AndroidManifest.xml` declares the
  `INTERNET` permission for the `/v1` API. The `image_picker` plugin supplies
  its own camera/gallery intents, so no storage or `CAMERA` permission is
  required for the picker's cache copy.
- **iOS** — `ios/Runner/Info.plist` has `NSCameraUsageDescription` and
  `NSPhotoLibraryUsageDescription` with plain-language copy. Without them the
  app is rejected or the picker fails at runtime.

## Configuration

| Define | Default | Purpose |
| --- | --- | --- |
| `API_BASE_URL` | `http://10.0.2.2:8000` | API root. `10.0.2.2` is the host machine as seen from an Android emulator; use `http://localhost:8000` for iOS simulator and the machine's LAN address for a physical device. |

No secrets are compiled into the app and no provider key is stored on the
device. Authentication is a later phase, so the chat routes currently run as
the demo owner.

## Scope implemented (2026-11-06)

- **Home:** API reachability (unauthenticated `/health`) and the two separate
  outputs (`photo assessment` vs `area outlook`) with no merged risk number.
- **Chat capture:** take a photo or choose from the gallery, preview it, remove
  it, and send it with optional text. JPEG, PNG and WebP are accepted up to
  10 MB; the picker downscales to 1600 px at quality 85 before the size check.
- **Upload-first contract:** the image is uploaded with `POST /v1/uploads`
  (multipart field `file`) and the JSON message only carries
  `image.upload_id`. Raw bytes never travel in the message body.
- **Idempotent send:** one `client_message_id` is generated per turn and sent
  both in the body and as `Idempotency-Key`; retries reuse it.
- **Assessment card:** state, reason text, up to three candidate display names,
  confidence band (or `not_calibrated`), calibration flag, model version and
  generated time. Raw scores are not shown; `is_demo` renders as a visible
  badge; no free-form diagnosis is displayed.
- **Offline queue:** see below.

## Offline queue (spec 08 §10 / CHAT-04)

The outbox is persisted as JSON under `ps03.chat.outbox.v1` using
`shared_preferences`; no database access is involved.

| Condition | Behaviour |
| --- | --- |
| Network/server unreachable on send | The turn is saved locally and shown as `queued`, retaining the text, image path and conversation id. |
| Retry | Manual **Retry now**, a 15-second flush while the chat page is open, and a flush on app resume. |
| Image | Uploaded once; the resulting `upload_id` is persisted so a retry does not create a second upload. |
| Server failure (`5xx`, `408`, `429`) | Treated as retryable; the ordered flush stops and resumes on the next attempt. |
| Non-retryable failure (`4xx`) | The turn is kept as `failed` so the user can read the error and **Delete** it; it is never presented as a reply. |
| Image file no longer available | The turn becomes `failed` with Retry/Delete; the app never fabricates a reply. |
| Reconnect | Turns are flushed in order with their original `client_message_id`, so the server returns the stored pair instead of duplicating. |

Known limits, deliberately accepted for this slice:

- The picker returns a cache copy; the OS may evict it before a reconnect. That
  is handled as a non-retryable failed turn, not hidden.
- There is no background worker and no `connectivity_plus` listener. Flush
  happens on the manual action, the page timer and app resume only.
- Queued turns live on one device and are not encrypted at rest; they contain
  only the user's text, a local image path and upload metadata.

## Dependencies

Added for this slice (all on the approved list):

| Package | Version resolved | Purpose |
| --- | --- | --- |
| `image_picker` | 1.2.4 | Camera and gallery capture |
| `shared_preferences` | 2.5.6 | Durable outbox JSON |
| `http_parser` | 4.1.2 | Multipart `MediaType` (already transitive via `http`) |

## Verification checks

| Command | Result (2026-11-06) |
| --- | --- |
| `flutter pub get` | pass — dependencies resolved |
| `flutter analyze` | pass — “No issues found!” |
| `flutter test` | pass — **14 tests** |
| `flutter build apk --debug` | pass — `build/app/outputs/flutter-apk/app-debug.apk` (~166 MB debug, all ABIs, default `http://10.0.2.2:8000`) |

Test coverage:

| File | What it proves |
| --- | --- |
| `test/api_client_test.dart` | Multipart upload targets `/v1/uploads` with field `file` and the declared MIME type; the message sends `upload_id` and `Idempotency-Key`; a non-JSON error becomes a retryable `ApiException`. |
| `test/chat_sync_test.dart` | One upload per turn; a retry reuses the persisted `upload_id`; one conversation for several queued turns; a missing image fails without sending; a text-only turn never uploads. |
| `test/outbox_test.dart` | Round-trip persistence, dedupe by `client_message_id`, update/remove, and corrupt-JSON recovery. |
| `test/widget_test.dart` | Home names both outputs without merging them; chat exposes capture and the honest demo copy. |

Environment: Flutter 3.47.9 (stable), Dart 3.13.7, Windows 11 25H2, Android SDK
36.1.0, Android Studio JBR (Java 21), Gradle/AGP from the Flutter 3.47 template.

## Emulator smoke (2026-11-06)

Run on the headless AVD `Medium_Phone_API_36.1` with the debug APK built for
`http://10.0.2.2:8010`, a separate uvicorn process on port 8010 and a fresh
Alembic-built SQLite database (`APP_DATABASE_URL` pointed at a scratch file), so
the shared development database was untouched.

| Step | Observed |
| --- | --- |
| Home screen | `PS-03 API 0.1.0`, `Environment: dev` fetched from `/health` |
| Text-only turn | Demo-labelled abstained assessment (`scaffold-demo-0.1`); no photo invented |
| Gallery capture | Picker returned `scaled_38.jpg`; `POST /v1/uploads` returned `quality_result=pass`; the JSON message referenced `upload_id`; demo assessment rendered (`demo-chat-0.1`) |
| Airplane mode on, send | Bubble showed `queued`; outbox persisted `state=queued`, `retryable=true`; no assistant reply was fabricated |
| Airplane mode off | The 15 s flush sent the turn, the outbox emptied, and the database held exactly one user message with that `client_message_id` plus one assistant reply |

This smoke also exposed a backend persistence bug: the request dependency
closed the session without committing while the chat/upload/video repositories
only `flush()`, so a `201` response could lose its rows. It was fixed at the
`get_session` unit-of-work boundary (commit on success, rollback on exception)
with a cross-request regression test; the backend suite then reported
**375 passed**.

After the smoke, the debug APK was rebuilt without a `--dart-define`, so the
on-disk artifact again uses the source default `http://10.0.2.2:8000` (the
server on port 8010 was only a scratch instance).

## Not verified

- Real-device camera capture (the emulator smoke used the gallery picker).
- iOS build or run; only the generated runner and usage strings are committed.
- A real mobile network; the emulator reached the host through `10.0.2.2`
  and airplane mode was toggled with `adb`.
- Flush while backgrounded; only page-open and app resume are wired.
- A real provider call — the app is demo-labelled until the backend has a key
  and approved labels.
