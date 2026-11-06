# ADR-009 — PostgreSQL/PostGIS + Cloudinary as the v1 data platform

- **Status:** Accepted
- **Date:** 2026-11-06
- **Deciders:** Project owner, Engineering lead
- **Supersedes:** S3-compatible object storage in `architecture-context.md` §2 and
  `feature-specs/05-data-layer.md` §8
- **Related:** ADR-002 (single SQL schema authority), ADR-004 (rules-based forecast),
  D1, D2, D6

---

## Context

The repository documented a PostgreSQL 16 + PostGIS system of record with private
S3-compatible object storage. The original audit request described a Firebase Firestore +
Cloudinary architecture. The two cannot both be built, and the conflict blocked every
downstream decision.

The product's core needs are:

- geospatial aggregation of verified reports by administrative boundary;
- reproducible forecast feature snapshots;
- append-only predictions, reviews and audit;
- relational integrity across users, roles, observations, images, diagnoses, alerts and
  audit;
- private image storage with signed access and transformations;
- a training pipeline that can read structured, labelled data efficiently.

## Decision

Adopt **PostgreSQL 16 + PostGIS 3.x** as the single system of record, accessed only by the
FastAPI backend through SQLAlchemy 2.0 + Alembic (ADR-002). Adopt **Cloudinary** as the
image store, used through short-lived signed uploads and authenticated delivery.

**Not adopted:** Firestore, Firebase Storage, dual-write, a second schema authority, or
client-side database access.

## Rationale

| Requirement | PostgreSQL/PostGIS | Firestore |
|---|---|---|
| Spatial aggregation by boundary | Native (`ST_AsMVT`, `ST_Intersects`) | Weak; requires external GIS |
| Multi-entity transactions | Native | Limited |
| Reproducible feature snapshots | Natural with relational snapshots | Awkward |
| Analytics on verified reports | SQL | Poor |
| Image delivery with transforms | Cloudinary alongside | Firebase Storage is weaker |

Cloudinary satisfies the image requirement from the target architecture without giving up
the relational and geospatial capabilities the outbreak pipeline depends on.

## Consequences

- All Firestore references in the target diagram are **out of scope** for v1.
- `database/` becomes the migration and seed home; `backend/app/db/` holds models and
  session management.
- Cloudinary credentials live in the secret manager and are never committed.
- Image keys are stored in `image_assets`; Cloudinary `public_id` and delivery URLs are
  derived, never trusted from the client.
- If Cloudinary is unavailable, uploads fail closed and the report is queued locally; the
  system does not fall back to a public bucket.

## Follow-ups

1. Replace every S3/presigned-URL reference in `architecture-context.md` and
   `feature-specs/05-data-layer.md`.
2. Define the Cloudinary folder, transformation and deletion-lifetime policy.
3. Add the Cloudinary client to the `media` module with a provider interface so the
   backend can be tested against a fake.
4. Record the Cloudinary data-processing terms before real farmer images are stored.

## Compliance

This ADR does not change R1–R10. Image privacy obligations in R9 still apply: private
storage, short-lived URLs, EXIF stripping and no public buckets.
