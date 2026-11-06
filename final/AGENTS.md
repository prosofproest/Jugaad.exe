# Repository agent instructions

The authoritative working agreement for this repository is
[docs-context/AGENTS.md](docs-context/AGENTS.md). Read it before making any change.

Short version:

- **Two outputs, never conflated:** photo assessment (one image) and area outlook
  (crop × target × geography × horizon).
- **Abstain instead of guessing.** "No assessment" is a valid, expected result.
- **No report is not proof of absence.** Data coverage and surveillance intensity
  must be visible wherever risk is shown.
- **No chemical prescriptions.** Advisory content is expert-approved, versioned and
  non-chemical; severe or uncertain cases escalate to a human.
- **No fabricated metrics, datasets or predictions.** Demo data must be labelled as
  demo data everywhere it appears.
- **Spec before code.** Update `docs-context/progress-tracker.md` when scope,
  decisions or status change.

Repository status as of 2026-11-06: documentation plus Phase 2 engineering scaffolds
(FastAPI, Next.js web client, Flutter shell, compose and CI), the **persisted demo
chat slice** (image upload + quality gate + deterministic demo engine + optional
mock- and local-stub-tested OpenAI-compatible vision adapter + review requests, Alembic
`0002_chat_persistence`), the **demo-labelled video-reading machinery** (bounded clip
decode, deterministic sampling, `demo-motion-0.1` detector, `bytetrack-lite-0.1`
tracker, per-frame assessments, non-diagnostic summary, Alembic
`0003_video_persistence`), and the **§5.2 identity backend slice** (phone OTP, staff
MFA, five roles, consent, privacy, audit — in memory). No real model is connected by
default, the shipped video detector is a heuristic rather than a pest detector, and
identity state is not durable; the web app builds and its chat flow passed a live
upload → assessment → review smoke test, while the mobile shell passes
`flutter analyze` and `flutter test` (no device or APK run yet). Gate 1 is not met.

The full 55-chapter blueprint and Appendices A–H are mapped to repository files in
[README.md](README.md). Coverage is documentation, not scope approval: v1 scope is set by
[update.md](update.md) and recorded in `docs-context/progress-tracker.md` §2 and §4.
