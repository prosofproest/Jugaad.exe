# ADR-011 — Open crop catalogue with a validated-target allowlist

- **Status:** Accepted
- **Date:** 2026-11-06
- **Deciders:** Project owner, ML lead, Agronomist
- **Related:** R2 (abstain), R3 (no report is not absence), R6 (no fabricated metrics),
  D1, D8

---

## Context

The product owner asked for a system that is "open for all crop diseases". A model that
claims universal disease coverage cannot be validated: every claim needs a labelled
dataset, a frozen field test set and a measured per-class recall. Claiming coverage that
has not been measured would violate R6, and forcing a result for an unseen crop would
violate R2.

## Decision

The **catalogue** is open and crop-agnostic. The **assessment allowlist** is narrow,
versioned and evidence-backed.

1. Any crop and any condition can be registered in the catalogue without a schema change.
2. A photo is assessed only when its `crop × target` pair is in the **supported allowlist**
   for the current release.
3. Otherwise the API returns an explicit abstention:
   - `unsupported_crop` — crop not in the release;
   - `unsupported_target` — crop supported, condition not validated;
   - `insufficient_quality` — image fails the quality gate.
4. An allowlist entry requires: dataset reference and licence, label handbook entry,
   frozen evaluation set, measured per-class recall and calibration, approving agronomist,
   and a date.
5. The allowlist is admin-managed, versioned and auditable. Removing an entry does not
   delete historical predictions.
6. The UI must always show whether the submitted crop is supported, and must never present
   an abstention as a negative result.

## What this is not

- It is **not** a claim of universal diagnosis.
- It is **not** permission to map an unknown input onto the nearest known class.
- It does **not** relax R2, R3 or R6.

## Consequences

- The first release can ship with a small allowlist (for example one crop and 3–5
  conditions) and grow without a schema migration.
- `GET /v1/config/crops` must return support status and the abstention reason vocabulary.
- Model evaluation is needed **per allowlist entry**, not once globally.
- D1 is answered at the architecture level. The first concrete allowlist is tracked as
  **D1a** and must be fixed before Gate 3.

## Follow-ups

1. Add `crops`, `targets`, `supported_config` and `allowlist` versioning to the data layer.
2. Add the abstention-reason enum to the API contract and UI.
3. Record D1a (first validated crop/target set) in `progress-tracker.md` §4 before Phase 3.
