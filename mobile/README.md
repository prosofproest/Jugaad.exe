# PS-03 mobile client (Flutter)

API-only Flutter client for the PS-03 modular monolith. It consumes the same
versioned `/v1` API as the web app and never connects to the database.

> **Verification status: UNVERIFIED.** Flutter is not installed on the machine
> where this scaffold was authored, so `flutter analyze`, `flutter test` and a
> device run have **not** been executed. Treat this folder as a compile-target
> sketch until CI or a developer with the Flutter SDK confirms it.

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

## Expected checks once Flutter is available

| Command | Expected |
| --- | --- |
| `flutter pub get` | resolves `http` and `flutter_lints` |
| `flutter analyze` | no issues |
| `flutter test` | widget test passes |
| `flutter build apk --debug` | builds with generated `android/` |
