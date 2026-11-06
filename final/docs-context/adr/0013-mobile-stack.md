# ADR-013 — Flutter is the single mobile client; the Expo prototype is not adopted

- **Status:** Accepted
- **Date:** 2026-11-06
- **Deciders:** Project owner
- **Related:** ADR-003 (API-only clients), ADR-006 (Flutter capture), ADR-007 (one API,
  web app and mobile app in scope), ADR-012 (`frontend/` naming), R8 (offline-first)
- **Affects:** `mobile/`, `frontend/mobile/`, `frontend/tsconfig.json`,
  `frontend/eslint.config.mjs`, `docs-context/AGENTS.md` §4, `progress-tracker.md` §5

---

## Context

A merge of remote `main` (`ebcc5df`) introduced a second mobile application at
`frontend/mobile/` — an Expo / React Native workspace — alongside the existing Flutter
client at `mobile/`. The repository therefore contained two clients for the same product,
which conflicts with ADR-007 (one mobile app in scope) and with the "no scaffolding that
implies an undecided decision" rule in `AGENTS.md` §4.

The two candidates were assessed on shipped evidence, not preference:

| Criterion | Flutter `mobile/` | Expo `frontend/mobile/` |
|---|---|---|
| Backend integration | `/health`, `/v1/conversations`, `/v1/messages`, multipart `POST /v1/uploads` | no network calls (`fetch`/`axios` absent) |
| Data source | live `/v1` API | `seedState` mock persisted to AsyncStorage |
| Offline-first (R8) | durable outbox + reconnect flush (15 s) | none |
| Tests | 14 passing (`api_client`, `chat_sync`, `outbox`, widget) | none |
| Build evidence | debug APK built; emulator smoke run | never run |
| Platform runners | `android/` (19 files) + `ios/` (40 files) committed | n/a |
| Git history | three feature commits | one bulk import commit |
| Web CI impact | none | breaks `tsc`/`next build` when swept into `frontend/tsconfig.json` |

## Decision

**Adopt the Flutter client at `mobile/` as the single mobile client for v1.**
Do **not** adopt the Expo application at `frontend/mobile/`; it is treated as a UI
prototype and must not be maintained as a second client.

The Expo prototype contains UI ideas not yet present in Flutter (farm map, hotspot map,
analysis report, i18n scaffolding). Those are recorded here as **porting candidates for
Flutter**, gated behind the relevant feature specs — they are not a reason to keep a
second runtime.

## Rationale

- R8 (offline-first) is non-negotiable, and only the Flutter client implements a durable
  outbox with reconnect flush.
- Only the Flutter client speaks the accepted `/v1` API contract; the Expo app cannot
  demonstrate any slice end-to-end because it has no network layer.
- The Flutter client carries real verification evidence (14 tests, APK, emulator smoke)
  and committed platform runners, so it can be tested on a device today.
- A second client doubles the surface that must satisfy R1–R10 and the parity contract,
  with no corresponding product value at this phase.

### Documentation conflict this ADR resolves

The repository never actually decided the mobile stack. Before this ADR:

- **Flutter** is named in `PRD.md`, `TRD.md`, `docs-context/AGENTS.md`,
  `progress-tracker.md`, ADR-006 and `final/AGENTS.md`.
- **React Native** is named in `architecture-context.md` (§ component table, diagram,
  implementation notes), `ui-context.md`, `code-standards.md` §4, `phase-plan.md` §5.1,
  `project-overview.md`, `components/README.md`, `feature-specs/01-design-system.md` and
  `feature-specs/08-conversational-capture.md`.
- `summary.md` and `totalcontent.md` say "Flutter or React Native".

This ADR selects Flutter and therefore **requires** the React Native statements above to be
reconciled in the same change cycle (see "Documentation reconciliation" below). ADR-006 is
also mis-indexed as "Superseded by ADR-009/010"; ADR-009/010 concern the data platform and
roles, not the mobile stack, and that index entry must be corrected.

## Consequences

- `frontend/mobile/` is removed from the repository; it remains recoverable at commit
  `ebcc5df` if the UI work is needed for porting.
- `frontend/tsconfig.json` and `frontend/eslint.config.mjs` exclude `mobile/**` so the web
  app never compiles or lints an Expo tree again.
- Any future mobile work targets `mobile/` only. A second mobile stack would require a
  superseding ADR.
- Porting farm map, hotspot map, analysis report and i18n into Flutter is **not** approved
  by this ADR; each requires its feature spec and, for map/location work, the privacy rules
  in R9.

## Documentation reconciliation (applied 2026-11-06)

The following statements were changed from React Native to Flutter in the same change
cycle as this ADR:

| File | Statement reconciled |
|---|---|
| `architecture-context.md` | § technology table, component diagram, implementation notes; correct the ADR-006 index entry |
| `ui-context.md` | "React Native theme provider", component inventory, mobile section, i18n note |
| `code-standards.md` §4 | "TypeScript / React Native (mobile)" tooling section |
| `phase-plan.md` §5.1, §5.7 | React Native deliverables and `frontend/mobile/` scaffold path |
| `project-overview.md` | product summary line |
| `components/README.md` | "React Native equivalents live in `frontend/mobile/…`" |
| `feature-specs/01-design-system.md` | mobile token consumer and storybook target |
| `feature-specs/08-conversational-capture.md` | "mobile (React Native + TypeScript)" |
| `README.md` (final) | code-standards description |
| `summary.md`, `totalcontent.md` | "Flutter or React Native" → Flutter |

## Alternatives considered

1. **Adopt React Native/Expo to match the majority of the specs.** Rejected *for v1*: the
   Expo app is a seeded prototype with no network layer, no offline queue, no tests and no
   device evidence. Adopting it means discarding the only working, offline-capable client
   and rebuilding its API/sync layer before any gate can advance. It remains the correct
   choice only if the owner prefers TypeScript parity with the web app over time-to-gate,
   in which case this ADR should be superseded before further mobile work.
2. **Keep both.** Rejected: two clients for one product, permanent parity debt, and both
   would have to satisfy R1–R10.
3. **Keep Expo as an in-repo design reference.** Rejected in favour of git history; dead
   trees imply a decision that was not made.
