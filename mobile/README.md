# PS-03 mobile client (Flutter)

API-only Flutter client for the PS-03 modular monolith. It consumes the same
versioned `/v1` API as the web app and never connects to the database.

> **Verification status: analyze + test verified (2026-11-06).** `flutter pub get`,
> `flutter analyze` and `flutter test` pass with Flutter 3.47.9 / Dart 3.13.7 on
> Windows 11. Platform runners are still absent and no device or APK run has been
> performed, so device behaviour remains unverified until `flutter create .` is run
> and an APK is built.

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

## Configuration

| Define | Default | Purpose |
| --- | --- | --- |
| `API_BASE_URL` | `http://10.0.2.2:8000` | API root. `10.0.2.2` is the host machine as seen from an Android emulator; use `http://localhost:8000` for iOS simulator and the machine's LAN address for a physical device. |

No secrets are compiled into the app. Auth and media upload are later phases.

## Scope in Phase 2 §5.1

- Home: API reachability (unauthenticated `/health`) and the two separate
  outputs (`photo assessment` vs `area outlook`) with no merged risk number.
- Chat: sends text to `/v1/conversations`, reuses `client_message_id` (also
  sent as `Idempotency-Key`) on retry, and labels demo replies.

## Verification checks

| Command | Result (2026-11-06) |
| --- | --- |
| `flutter pub get` | pass — resolved 30 packages (`http` 1.6.0, `flutter_lints` 5.0.0) |
| `flutter analyze` | pass — “No issues found!” |
| `flutter test` | pass — 1 widget test |
| `flutter build apk --debug` | not run — `android/` not generated |

Environment: Flutter 3.47.9 (stable), Dart 3.13.7, Windows 11 25H2. Android SDK
36.1.0 and the Android Studio JBR are installed, so an APK build is the next
verification step once the runners exist.
