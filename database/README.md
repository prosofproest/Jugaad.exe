# Database, data governance and archive — Phase 1 workspace

**Status:** Draft governance, collection and archive artifacts for review.
**Last updated:** 2026-11-06
**Scope:** Phase 1 — Data foundation: governance and permissions (§4.1), image
collection network (§4.2), archive acquisition (§4.3) and the labelling system (§4.4)
(`final/docs-context/phase-plan.md`).

> **This folder does not contain acquired data, executed agreements, a signed DPIA, an
> approved labelling handbook, or a released capture protocol.** It contains the registers,
> drafts and procedures needed to reach Gate 1. No dataset may be used until its permission
> record is signed and its register status is `cleared`; no field data may be collected until
> the protocol, consent and DPIA are approved. No archive may be ingested without a signed
> permission record, and no archive data may enter a field dataset version or the frozen field
> test set. No reviewer may label until trained and signed off against the approved handbook.

---

## 1. Authority and boundaries

| Concern | Authority |
|---|---|
| Schema, constraints, storage | `final/feature-specs/05-data-layer.md` |
| Data strategy, collection, labelling, splits | `final/docs-context/data-foundation.md` |
| Phase 1 deliverables and Gate 1 | `final/docs-context/phase-plan.md` §4 |
| Product safety rules R1–R10 | `final/docs-context/AGENTS.md` §3 |
| Privacy and retention | `final/feature-specs/03-auth-and-roles.md` §5–7 |
| Hosting and technical controls | `final/TRD.md` §6, §13 |

This folder is a working area for governance artifacts. It does **not** replace the
authoritative documents above. The executable schema is owned by the SQLAlchemy models
and Alembic migrations under `backend/app/db/` (ADR-002); `deploy/` applies it with
`alembic upgrade head` before starting the API.

---

## 2. Contents

| File | Purpose | Status |
|---|---|---|
| [`governance/01-dataset-register.md`](governance/01-dataset-register.md) | Register of every dataset, owner, permitted use, retention, update schedule and quality check | Draft — no dataset cleared |
| [`governance/02-mou-licence-tracker.md`](governance/02-mou-licence-tracker.md) | Per-dataset agreement tracker and required clauses | Draft — zero agreements executed |
| [`governance/03-consent-wording-and-capture.md`](governance/03-consent-wording-and-capture.md) | Plain-language consent drafts and consent-capture design | Draft — legal/local-language review required; build in Phase 2 |
| [`governance/04-dpia.md`](governance/04-dpia.md) | Data protection impact assessment | Draft — DPO/legal sign-off required |
| [`governance/05-retention-and-deletion.md`](governance/05-retention-and-deletion.md) | Retention matrix and deletion procedure | Draft — periods pending legal/programme decision |
| [`governance/06-quarantine-policy.md`](governance/06-quarantine-policy.md) | Quarantine path and the no-silent-drop rule | Draft |
| [`data-dictionary/data-dictionary-v1.md`](data-dictionary/data-dictionary-v1.md) | Field-level dictionary for training and forecasting | Draft v1 — crop/target/horizon values blocked on D1/D2 |
| [`schema/01-schema.sql`](schema/01-schema.sql) | Reference PostgreSQL 16 + PostGIS DDL for 14 schema slices (39 tables, constraints, triggers) | Implemented |
| [`schema/02-demo-seed.sql`](schema/02-demo-seed.sql) | Coherent demo dataset for testing (all rows flagged `is_demo = true`, R5 compliant) | Implemented |
| [`alembic/`](alembic/) | Alembic migration framework and revision `0001_initial_schema.py` with clean upgrade/downgrade | Implemented |
| [`storage/01-object-storage-and-presigned-urls.md`](storage/01-object-storage-and-presigned-urls.md) | Canonical S3 layout, presigned URL TTL (≤ 10m) & RBAC authorization matrix | Implemented |
| [`storage/storage_rules.py`](storage/storage_rules.py) | Python validation engine for storage keys, presigned URLs, MIME types and payload limits | Implemented |
| [`backup/01-backup-and-recovery-design.md`](backup/01-backup-and-recovery-design.md) | Backup design: daily base backup, continuous WAL (RPO ≤ 15m, RTO ≤ 2h), CRR & quarterly drill | Implemented |
| [`backup/verify_backup.py`](backup/verify_backup.py) | Backup manifest and cryptographic checksum verification tool | Implemented |
| [`backup/backup_runbook.sh`](backup/backup_runbook.sh) | Executable backup and manifest generation drill runbook | Implemented |
| [`tests/`](tests/) | Unit & integration test suites validating schema slices, constraints, seed isolation and rules | Implemented |
| [`collection/01-capture-protocol.md`](collection/01-capture-protocol.md) | Device, shot list, distance, angle, lighting, background, plant part, severity, multiple images, metadata | Draft v1.0 — not issued to collectors |
| [`collection/02-sampling-matrix.md`](collection/02-sampling-matrix.md) | Matrix across districts, seasons, varieties, ages, lighting, backgrounds, severity, devices; special strata | Draft v1.0 — strata and quotas partly blocked on D1 |
| [`collection/03-enumerator-training-and-pilot.md`](collection/03-enumerator-training-and-pilot.md) | Training curriculum, competency sign-off, pilot batch, throughput and reject metrics, revision rules | Draft — no training delivered, no pilot run |
| [`collection/04-secure-upload-and-retention.md`](collection/04-secure-upload-and-retention.md) | Secure upload, originals vs derivatives, access control, backup and restore | Draft — no storage provisioned; retention periods TBD |
| [`collection/05-collection-progress-tracking.md`](collection/05-collection-progress-tracking.md) | Coverage tracking against the matrix, funnel, gaps and anti-gaming rules | Draft — no collection started |
| [`archive/01-archive-acquisition.md`](archive/01-archive-acquisition.md) | Archive permission gate, eligibility, intake, separation from field data | Draft — no archive approached or acquired |
| [`archive/02-label-reconciliation.md`](archive/02-label-reconciliation.md) | Taxonomy pinning, mapping statuses, pathologist review, unmappable-record handling | Draft — blocked on D1 taxonomy |
| [`archive/03-archive-provenance.md`](archive/03-archive-provenance.md) | Source links, original labels, reviewer identity, checksums and chain of custody | Draft — no archive record in hand |
| [`labelling/01-labelling-handbook.md`](labelling/01-labelling-handbook.md) | Crop-specific taxonomy, class kinds, uncertainty, severity, evidence tiers, provenance, revision history | Draft v1.0 — crop-specific classes blocked on D1; not approved |
| [`labelling/02-reviewer-calibration.md`](labelling/02-reviewer-calibration.md) | Representative subset, blinding, agreement measures, adjudication and the revision loop | Draft — no round run; subset size/threshold blocked on D8 |
| [`labelling/03-reviewer-training-and-audit.md`](labelling/03-reviewer-training-and-audit.md) | Reviewer curriculum, competency sign-off, quality sampling and label-audit cadence | Draft — no reviewer trained or audited |
| [`labelling/04-abstention-and-hard-negatives.md`](labelling/04-abstention-and-hard-negatives.md) | Retention and use of hard negatives, ambiguous images and uncertainty classes | Draft — no set assembled |

---

## 3. Phase 1 status

### 3.1 Governance and permissions (§4.1)

| Phase 1 requirement | Status | Note |
|---|---|---|
| Dataset register with owner, permitted use, retention, update schedule, quality check | `[~]` | Register created; all rows are candidates and none are cleared |
| MoUs/licences executed for every dataset | `[ ]` | **Cannot be executed by an AI agent.** Tracker and clause checklist prepared; signatures require authorised humans |
| Consent wording finalised | `[~]` | English draft prepared; local-language and legal review required |
| Consent capture designed | `[~]` | Data model and flow drafted; implementation is Phase 2 |
| DPIA completed | `[~]` | Draft prepared; not a completed or signed DPIA |
| Retention/deletion procedure recorded | `[~]` | Procedure drafted; retention periods are TBD |
| Quarantine path defined | `[x]` | Policy drafted |
| Data dictionary v1 written | `[~]` | Field contract drafted; crop/target/horizon-specific values blocked on D1/D2 |

### 3.2 Image collection network (§4.2)

| Phase 1 requirement | Status | Note |
|---|---|---|
| Capture protocol published | `[~]` | `v1.0-draft` written; not approved or issued; distance/device/severity values pending D1 and device trial |
| Sampling matrix defined | `[~]` | Dimensions and tiers defined; strata and `n_min` blocked on D1 |
| Enumerators trained | `[ ]` | Curriculum and competency sign-off defined; no training delivered |
| Pilot collection batch run | `[ ]` | Design and metrics defined; not run |
| Throughput and reject rate measured | `[ ]` | Metric definitions exist; no measurements |
| Protocol revised from pilot | `[ ]` | Revision rules defined; no revision yet |
| Secure upload, backup and original retention | `[~]` | Control design written; no storage provisioned; retention periods TBD |
| Derivatives kept separate and regenerable | `[~]` | Layout and rules defined; not implemented |
| Progress tracked against the matrix | `[~]` | Tracking model defined; no collection to track |

### 3.3 Archive acquisition (§4.3)

| Phase 1 requirement | Status | Note |
|---|---|---|
| Plant-clinic/university archives ingested where permitted | `[ ]` | Permission gate and intake process defined; no institution named, no access requested, no data in hand |
| Archive labels reconciled to the project taxonomy | `[ ]` | Reconciliation process and statuses defined; blocked on D1 taxonomy |
| Unmappable records flagged | `[~]` | Quarantine code and handling defined; no records to flag |
| Source links, original labels, reviewer identity and provenance preserved | `[~]` | Required fields and custody rules defined; no schema or records yet |
| Archive data kept separate from fresh field data in the register | `[x]` | Separation rule, `ARC-001`/`ARC-002` sub-register and no-mixing rules written |

### 3.4 Labelling system (§4.4)

| Phase 1 requirement | Status | Note |
|---|---|---|
| Labelling handbook: crop-specific taxonomy, class kinds, uncertainty, severity, provenance, revision history | `[~]` | Framework and required structures written; crop-specific classes/severity blocked on D1; not approved |
| Suspected, expert-confirmed and laboratory-confirmed labels separated | `[x]` | Three `label_origin` tiers defined with evidence and use rules |
| Reviewer calibration round run | `[ ]` | Protocol, subset design and adjudication defined; no round run |
| Inter-reviewer agreement measured | `[ ]` | Measures defined; no data; subset size/threshold blocked on D8 |
| Disagreements adjudicated and definitions revised | `[~]` | Adjudication and revision process defined; no disagreements yet |
| Reviewer training, quality sampling and audit cadence | `[~]` | Curriculum, sign-off, sampling and cadence defined; no reviewer trained or audited |
| Hard negatives and ambiguous images retained for abstention | `[x]` | Retention, coding, use and no-deletion rules defined |

### 3.5 Data platform and schema (§4.5)

| Phase 1 requirement | Status | Note |
|---|---|---|
| Implement schema slices from `05-data-layer.md` | `[x]` | 14 slices, 39 tables, stable UUIDs, status CHECKs, source timestamps, triggers |
| Append-only prediction/review/audit rows | `[x]` | Enforced via `reject_mutation()` and `labels_guard_mutation()` triggers |
| PostGIS only where spatial queries are needed | `[x]` | Restricted to `geographies.geom`, `growing_areas.geom`, `sentinel_sites.geom` |
| Set up migrations (Alembic) | `[x]` | Configured in `alembic/` with revision `0001_initial_schema.py` |
| Object storage layout & presigned URL rules | `[x]` | Layout, TTL ≤ 10m, verb restrictions, RBAC matrix & Python validator |
| Backup and disaster recovery design | `[x]` | Architecture (RPO ≤ 15m, RTO ≤ 2h), WAL archiving, manifest verifier & drill runbook |
| Seed only clearly labelled `is_demo` data | `[x]` | Comprehensive demo seed `02-demo-seed.sql` with `is_demo = true` and R5 non-chemical compliance |

---

## 4. What an AI agent must not do here

The following are outside an AI agent's authority and must be performed by the named
human owner:

- sign, execute or vary an MoU, licence, data-sharing agreement or terms of use;
- give legal advice, assert regulatory compliance, or sign off a DPIA;
- approve retention periods or a lawful basis;
- assert that a partner, dataset, permission or date exists when it does not;
- approve advisory content or any chemical guidance;
- use real farmer data, images, phone numbers or farm locations in examples, tests or
  fixtures;
- mark a dataset `cleared` without a signed permission record.

If a required fact is unknown, the artifact uses `TBD` and records the owner who must
resolve it. It is never filled with a plausible-looking value.

---

## 5. Non-negotiable rules carried into these artifacts

- **R1:** photo assessment and area outlook remain separate.
- **R2:** abstain rather than force a result.
- **R3:** no report is not evidence of absence; coverage is first-class.
- **R4:** human verification is mandatory; models never verify.
- **R5:** no chemical advice, ever.
- **R6:** no fabricated data, metrics, partners or permissions; demo data is labelled.
- **R7:** every prediction is traceable to a model version and input snapshot.
- **R8:** offline-first is core; client IDs and idempotency prevent duplicates.
- **R9:** privacy by default; approximate location; small counts suppressed.
- **R10:** spec before code; changes to scope or semantics update the spec and tracker.

---

## 6. Gate 1 readiness checklist

Gate 1 requires all of the following. This folder supports, but does not by itself
satisfy, the gate.

- [ ] Documented permission for every dataset used.
- [ ] Ingestion reproducible from raw source to model-ready version.
- [ ] Labelling handbook approved by a pathologist.
- [ ] Data dictionary and quality checks exist for every field.
- [ ] Frozen field test set created before model selection.
- [ ] Unverified reports excluded from forecast features (tested).
- [ ] Weather gaps produce `insufficient_data`, never imputed values.
- [ ] DPIA reviewed and signed by the responsible legal/privacy owner.
- [ ] Consent wording approved in the pilot language(s).
- [ ] Retention and deletion procedure approved.

### 6.1 Collection deliverables (Phase 1 §4.2)

These support Gate 1 but are not themselves gate criteria in `phase-plan.md`.

- [ ] Capture protocol approved by the agronomist and field operations lead and issued with
      training.
- [ ] Sampling matrix v1 approved with `n_min` set before collection.
- [ ] Enumerators trained and competency-signed.
- [ ] Pilot batch completed; throughput and reject rate recorded with denominators.
- [ ] Protocol revised from pilot evidence with a versioned change log.
- [ ] Secure upload, backup and restore tested; originals immutable; derivatives separate.
- [ ] Collection progress reported as matrix coverage, not total image count.

### 6.2 Archive deliverables (Phase 1 §4.3)

These support Gate 1 but are not themselves gate criteria in `phase-plan.md`.

- [ ] A signed permission record exists for every archive source (`ARC-###`).
- [ ] Archive labels are reconciled against a pinned taxonomy version and every mapping has
      a pathologist reviewer.
- [ ] Unmappable and conflicting records are quarantined, preserved and counted.
- [ ] Every archive record has a source link, original label, content hash and provenance
      status, or a recorded reason why not.
- [ ] Archive and field counts are reported separately; archive records are absent from
      field dataset versions, split manifests and the frozen field test set.
- [ ] Archive provenance and mapping tables exist in the schema (or a documented sidecar)
      before ingest.

### 6.3 Labelling deliverables (Phase 1 §4.4)

These support Gate 1 but are not themselves gate criteria in `phase-plan.md`.

- [ ] Labelling handbook approved by a pathologist, with a complete class card for every
      class and a validated crop-specific severity scale.
- [ ] Crop-specific taxonomy recorded after D1; no class invented or left implicit.
- [ ] `suspected`, `expert_confirmed` and `lab_confirmed` labels stored separately and used
      per their evidence tier.
- [ ] Calibration round run on a fixed, stratified subset; agreement reported with
      denominators and class-level results at the D8 threshold.
- [ ] Disagreements adjudicated by a third qualified reviewer; handbook revised and
      reviewers re-trained.
- [ ] Reviewer competency sign-off recorded per handbook version.
- [ ] Quality sampling and label-audit cadence approved and running.
- [ ] Hard negatives and ambiguous images retained, coded and excluded from positive
      training and forecast negatives.

---

## 7. Change control

- Every register or policy change records the date, owner and reason.
- A dataset may move to `cleared` only when a signed permission record is attached and
  the permitted use is explicit.
- Material changes to consent wording, retention or the DPIA require re-review.
- **"Published" means approved and issued with training, not merely written.** The capture
  protocol and sampling matrix here are drafts (`v1.0-draft`) and must not be described as
  released until the pre-issue checklists are complete.
- Protocol and matrix versions are recorded on every case; historical records are never
  rewritten to a newer version.
- The Phase-1 artifacts and this workspace are tracked in
  `final/docs-context/progress-tracker.md`; update the tracker alongside any material
  change to scope, status or evidence here.
- Archive labels are never overwritten by mapped labels; re-mapping creates a new version.
- Archive and field datasets never share a dataset version, split manifest or frozen field
  test set.
- Every label records its handbook and taxonomy version; a material handbook revision
  triggers reviewer re-training and, where class meaning changes, a re-labelling plan.
