# PS-03 mobile client (Flutter)

API-only Flutter client for the PS-03 modular monolith. It consumes the same
versioned `/v1` API as the web app and never connects to the database.

> **Verification status: analyze + test verified (2026-11-06).** `flutter pub get`,
> `flutter analyze` and `flutter test` pass with Flutter 3.47.9 / Dart 3.13.7 on
> Windows 11; the suite is **14 tests**. Platform runners are still absent and no
> device, emulator or APK run has been performed, so camera capture, airplane-mode
> queueing and background/resume flush are **unit-verified only** until
> `flutter create .` is run and an APK is built.

## First run (requires the Flutter SDK)

The Dart package (`pubspec.yaml`, `lib/`, `test/`) is committed. Platform
folders (`android/`, `ios/`) are intentionally **not** hand-written; generate
them once with the Flutter CLI:

```bash
cd mobile
flutter create . --project-name ps03_mobile --platforms=android,ios
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

`flutter create .` is additive: it keeps `lib/` and `test/` and only adds the
missing platform runners. Commit the generated folders once the app runs, so
CI can build it without regeneration.

After generating the runners, add the platform permission strings the image
picker needs before testing capture:

- **Android** — the `image_picker` plugin supplies its own camera/gallery
  intents; no storage permission is required for the picker's cache copy.
- **iOS** — add `NSCameraUsageDescription` and
  `NSPhotoLibraryUsageDescription` to `ios/Runner/Info.plist` with plain-language
  copy. Without them the app is rejected or the picker fails at runtime.

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
| `flutter build apk --debug` | not run — `android/` not generated |

Test coverage:

| File | What it proves |
| --- | --- |
| `test/api_client_test.dart` | Multipart upload targets `/v1/uploads` with field `file` and the declared MIME type; the message sends `upload_id` and `Idempotency-Key`; a non-JSON error becomes a retryable `ApiException`. |
| `test/chat_sync_test.dart` | One upload per turn; a retry reuses the persisted `upload_id`; one conversation for several queued turns; a missing image fails without sending; a text-only turn never uploads. |
| `test/outbox_test.dart` | Round-trip persistence, dedupe by `client_message_id`, update/remove, and corrupt-JSON recovery. |
| `test/widget_test.dart` | Home names both outputs without merging them; chat exposes capture and the honest demo copy. |

Environment: Flutter 3.47.9 (stable), Dart 3.13.7, Windows 11 25H2. Android SDK
36.1.0 and the Android Studio JBR are installed, so an APK build is the next
verification step once the runners exist.

## Not verified

- No APK build, device run or emulator run.
- Camera/gallery permissions on a real device.
- Airplane-mode queue and reconnect on a real network.
- Flush while backgrounded; only page-open and resume are wired.
- A real provider call — the app is demo-labelled until the backend has a key
  and approved labels.
