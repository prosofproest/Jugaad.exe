# ADR-0001 — Target architecture

- **Status:** Accepted (consolidates ADR-001…ADR-009)
- **Date:** 2026-11-06
- **Deciders:** Engineering lead, product lead
- **Supersedes:** none
- **Source of truth:** `final/docs-context/progress-tracker.md` §5 (ADR log)

## Context

The project started from a maximal 55-chapter blueprint and was narrowed to a
realistic v1: one crop, one agro-climatic zone, 3–5 targets, assistive image
triage, extension-worker verification, a rules-based weather risk model, and
SMS/WhatsApp delivery. Two incompatible stacks appeared during the audit
(Firestore/Cloudinary/Prisma vs. PostgreSQL/PostGIS/S3/FastAPI). Gate 0 exists to
record one architecture before any domain feature is built.

This ADR is the single architecture record required by Gate 0.1. It does not
resolve product decisions D1–D6 or data-policy decisions D9–D12; those remain in
`progress-tracker.md` §4.

## Decision

### Application shape

- **Modular monolith** — one FastAPI application with feature modules, not
  microservices (ADR-001).
- **FastAPI + SQLAlchemy + Alembic** are the single schema authority. No Prisma,
  no second ORM, no manual DDL (ADR-002).
- **Web portals are API-only clients**; they never touch the database (ADR-003).

### Data and storage

- **PostgreSQL 16 + PostGIS** for structured and spatial data. Firestore is
  rejected.
- **S3-compatible private object storage** for images. Cloudinary is rejected.
- Images are private; retrieval is through short-lived signed URLs.

### Clients

- **Next.js web app** in `frontend/` (the source documents say `web/`; the folder
  name follows the repository layout — ADR-009).
- **Flutter mobile app** for field capture (camera + offline), not a
  farmer-facing native app for all users.
- Full-stack delivery is in scope: one API, a web app and a mobile app
  (ADR-007).

### Identity and roles

- **Auth mechanism:** phone OTP for farmers; provisioned staff accounts; MFA for
  pathologist, agronomist and admin.
- **Five roles:** farmer, extension worker, pathologist, agronomist, admin (D13).
  The agronomist can author/approve advisory content and risk bands and read area
  data, but cannot verify cases.
- Access is deny-by-default; every protected route needs an authorisation
  dependency.

### Language

- **One local language plus English** for staff tooling. The specific local
  language is not yet named (open decision). v1 does not ship multi-language
  beyond this pair.

### Model outputs

- Two outputs are never merged: **photo assessment** (one image) and **area
  outlook** (crop × target × geography × horizon).
- Photo assessment returns candidate classes, quality flags, a qualitative
  confidence band, an abstention state and a model version. It never claims
  laboratory confirmation.
- Numeric probability is shown only when calibration is approved; otherwise it is
  `null`.
- Area outlook returns a risk band, drivers, coverage, issue/expiry times and a
  model version. It never claims a confirmed outbreak.

### Forecast approach

- **Rules-based nowcast first** (weather thresholds + crop stage), versioned and
  expert-approved. ML is an overlay only after at least two seasons of verified
  outcomes (ADR-004).
- No-score / `insufficient_data` is a first-class outcome for stale weather, low
  coverage, missing calendar or boundary mismatch.

### Guidance and chat

- Advisory content is **curated, expert-approved, versioned and non-chemical**.
  No LLM generates advice (ADR-008).
- Chat is a `conversations` wrapper over the photo-assessment contract, not a new
  model and not a generative diagnosis path.

### Delivery channels

- A channel adapter interface for **SMS / WhatsApp / push**. SMS/WhatsApp carry
  farmer-facing outlook and alerts; the native app is for capture (ADR-006,
  still Proposed).

### Maps

- **MapLibre GL JS + PostGIS** with vector tiles or GeoJSON from our own API.
  Do not build a custom GIS platform.

## Rejected alternatives

| Alternative | Why rejected |
|---|---|
| Firestore | No PostGIS spatial querying or relational integrity for the verification/audit model |
| Cloudinary | Third-party image custody and weaker control over signed access |
| Prisma | Would create a second schema authority alongside SQLAlchemy/Alembic |
| Microservices | Operational overhead for a 7–9 person pilot team |
| Generative-AI advisory / free-form diagnosis | Liability; violates the non-chemical and "not a diagnosis" boundaries |
| Spatiotemporal deep learning for v1 | No dense longitudinal data; rules nowcast is defensible now |
| Custom GIS renderer | Duplicates MapLibre and increases correctness/privacy risk |
| Multi-crop / universal diagnosis | Scope creep; expansion is evidence-gated |

## Consequences

- The backend remains one deployable unit; feature modules must not reach into
  each other's storage.
- Every schema change needs an Alembic forward migration and a rollback note.
- Auth and authorisation must exist before any data-bearing endpoint is exposed;
  this is Gate 1.
- Until D1–D6 are resolved, code may only be decision-independent machinery and
  must not encode crop, target, geography, horizon or advisory values.
- ADR-005 (ONNX Runtime CPU inference) and ADR-006 (Flutter + SMS/WhatsApp) are
  still **Proposed**, not accepted; infrastructure work must not assume them as
  settled.
