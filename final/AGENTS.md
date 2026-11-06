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

Repository status as of 2026-11-06: documentation plus a Phase 2 §5.1 engineering
scaffold (FastAPI, Next.js web client, Flutter shell, compose and CI). No product feature
is implemented; the web app builds and the mobile shell is unverified. Gate 1 is not met.

The full 55-chapter blueprint and Appendices A–H are mapped to repository files in
[README.md](README.md). Coverage is documentation, not scope approval: v1 scope is set by
[update.md](update.md) and recorded in `docs-context/progress-tracker.md` §2 and §4.
