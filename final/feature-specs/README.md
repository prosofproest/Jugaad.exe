# Feature specifications

Specs are the implementation contract. Read `../docs-context/AGENTS.md` first, then the
spec for the feature you are changing. Every requirement has a stable ID used in commits,
tests and the tracker.

Supporting domain documents:

| Document | Use when |
|---|---|
| `../docs-context/data-foundation.md` | Collecting, labelling, cleaning or splitting data |
| `../docs-context/ml-models.md` | Training, evaluating, calibrating or combining models |
| `../docs-context/operations-and-pilot.md` | Testing, piloting, deploying or monitoring |
| `../docs-context/appendices.md` | Templates, checklists, glossary, launch gates |
| `../README.md` | Finding the document for a blueprint chapter |

| # | Spec | Covers | Primary surface | Blueprint chapters | Status |
|---|---|---|---|---|---|
| 01 | [Design system](01-design-system.md) | Tokens, components, states, accessibility | All | 15–17, 32 | Draft |
| 02 | [Reporting and capture](02-reporting-and-capture.md) | Context, camera, quality gate, offline queue, result, history | Mobile | 15, 19, 27, 42; App. B | Draft |
| 03 | [Auth, roles and consent](03-auth-and-roles.md) | Identity, sessions, RBAC, consent, privacy requests | All | 43, 44 | Draft |
| 04 | [Expert review](04-expert-review.md) | Queue, triage, verification states, evidence, audit | Expert portal | 16, 20, 45 | Draft |
| 05 | [Data layer](05-data-layer.md) | Schema, constraints, PostGIS, storage, migrations, registry | Backend | 21–26, 47; App. C–E | Draft |
| 06 | [Forecast and risk map](06-forecast-and-risk-map.md) | Area outlook, no-score gate, risk bands, map layers | Dashboard + SMS | 23, 33–39; App. C | Draft |
| 07 | [Advisory and alerts](07-advisory-and-alerts.md) | Approved content, trigger policy, dedupe, delivery | SMS/WhatsApp + portal | 40, 41; App. A | Draft |

## Dependency order

```
01 ─┬─► 02 ─┬─► 04 ─┬─► 06 ─► 07
    │      │       │
03 ─┴──────┴───────┴─► 05 (schema underlies all)
```

`05` is written last in the list but is a dependency of every other spec. Implement the
schema slices needed by a feature, not the whole schema up front.

## Spec template

Every spec uses the same shape:

1. Status, owner, dependencies, implemented requirements
2. Goal and users
3. Flow / state machine
4. Functional requirements with IDs and priority
5. API touchpoints
6. Data model touchpoints
7. Edge cases
8. Non-functional requirements
9. Acceptance criteria (testable)
10. Telemetry and audit
11. Out of scope
12. Open questions

## Rules

- Requirement IDs are stable. Do not renumber; deprecate with a note.
- Acceptance criteria must be testable without reading the implementation.
- A spec cannot weaken a rule in `../docs-context/AGENTS.md` §3.
- Decisions that block implementation are recorded in
  `../docs-context/progress-tracker.md` §4, not invented in a spec.
- All thresholds and example payloads are illustrative until locally validated. Demo
  payloads carry `is_demo: true`.
