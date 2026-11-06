# Architecture Decision Records

This directory holds the ADRs that change the baseline architecture, scope or safety
semantics. `../progress-tracker.md` §5 is the canonical index; each file here is the
durable record.

## Rules

- One decision per file. ADRs are append-only: supersede, never rewrite history.
- An ADR is **Accepted** only when it names a decider and a date.
- Code that depends on a **Proposed** ADR must not be merged.
- Any change to the data platform, roles, crop/target policy, forecast horizon,
  advisory policy or AI-output semantics requires an ADR.
- Link the ADR from `../progress-tracker.md` §5 and from every spec it changes.

## Index

| ID | Title | Status | Date |
|---|---|---|---|
| ADR-001 | Modular monolith over microservices | Accepted | 2026-11-06 |
| ADR-002 | FastAPI + SQLAlchemy/Alembic as single schema authority | Accepted | 2026-11-06 |
| ADR-003 | Web portals are API-only clients | Accepted | 2026-11-06 |
| ADR-004 | Rules-based forecast before ML | Accepted | 2026-11-06 |
| ADR-005 | ONNX Runtime CPU inference for pilot | Proposed | 2026-11-06 |
| ADR-006 | Flutter capture + SMS/WhatsApp delivery | Superseded by ADR-009 / ADR-010 | 2026-11-06 |
| ADR-007 | Full-stack delivery: one API, web app and mobile app in scope | Accepted | 2026-11-06 |
| ADR-008 | Chat is a `conversations` wrapper, not a generative diagnosis | Accepted | 2026-11-06 |
| [ADR-009](0009-data-platform.md) | PostgreSQL/PostGIS + Cloudinary as the v1 data platform | Accepted | 2026-11-06 |
| [ADR-010](0010-v1-roles.md) | v1 roles: farmer, extension_worker, admin | Accepted | 2026-11-06 |
| [ADR-011](0011-open-crop-catalogue.md) | Open crop catalogue with a validated-target allowlist | Accepted | 2026-11-06 |

## Open ADRs

- ADR-005 (ONNX serving) stays **Proposed** until the Phase 3 model export exists.
