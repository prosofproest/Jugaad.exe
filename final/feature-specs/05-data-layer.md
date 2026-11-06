# 05 — Data layer

**Status:** Draft
**Owner:** Data engineer (TBD)
**Depends on:** `architecture-context.md`
**Implements:** relational schema, geospatial storage, object storage, migrations, model
registry, audit, retention.

---

## 1. Goal

One authoritative schema that makes the safety invariants structural:

- predictions are append-only and versioned;
- verification is a human projection with full history;
- forecasts are reproducible from an immutable feature snapshot;
- unverified reports can never be read as confirmed evidence;
- precise locations are restricted by design.

**Schema authority:** SQLAlchemy models + Alembic migrations in `backend/`.
**No Prisma, no second ORM, no manual prod DDL.** The web app never connects to the
database.

---

## 2. Conventions

- PostgreSQL 16 + PostGIS 3.x.
- UUID primary keys (`gen_random_uuid()`); human-readable prefixed IDs only in API
  responses if needed.
- `created_at`, `updated_at` `timestamptz not null default now()`.
- `text` + `CHECK` for closed sets (not native enums) so values can evolve with a
  migration.
- All timestamps UTC. All external data carries `source_timestamp` and `fetched_at`.
- Money not applicable. Counts are integers; rates are numeric with explicit scale.
- Soft delete only for user-facing entities (`deleted_at`); predictions, reviews, audit
  and forecasts are never soft-deleted.
- Every FK has an index. Every queue/filter path has a covering index (see §7).
- JSONB only for heterogeneous payloads (candidates, drivers, evidence blobs) with a
  documented shape; not for anything queried relationally.

---

## 3. Entity map

```
users ─┬─ user_roles ── roles
       ├─ consents
       ├─ devices
       └─ user_area_assignments ── geographies

growing_areas ── crop_cycles ── observations ─┬─ image_assets ─┬─ image_quality_results
                                              │                └─ image_predictions
                                              ├─ review_requests
                                              └─ reviews ─┬─ review_evidence
                                                          └─ review_events
observations ── observation_verification (projection)

geographies (versioned boundaries)
sentinel_sites ── sentinel_visits (forecast negatives, D7)
weather_snapshots
forecasts ── feature_snapshots
advisories ── advisory_versions ── advisory_approvals
alerts ── alert_deliveries
model_registry
audit_events
```

---

## 4. Core tables

### 4.1 Identity

| Table | Key columns | Notes |
|---|---|---|
| `users` | id, phone_e164 (unique, nullable), email (unique, nullable), password_hash, status, locale, token_version, created_at, deleted_at | Farmer has phone; staff has email |
| `roles` | code (`farmer`,`extension_worker`,`pathologist`,`agronomist`,`admin`), description | Seeded |
| `user_roles` | user_id, role_code, granted_by, granted_at, revoked_at | History preserved |
| `devices` | id, user_id, platform, app_version, last_seen_at, push_token | No advertising IDs |
| `consents` | id, user_id, type, version, granted, text_hash, channel, created_at | Append-only |
| `user_area_assignments` | user_id, geo_code, level, active_from, active_to | Drives staff scoping |
| `sessions` | id, user_id, refresh_hash, family_id, expires_at, revoked_at, ip_hash, user_agent | Refresh rotation |

### 4.2 Geography and crop context

| Table | Key columns | Notes |
|---|---|---|
| `geographies` | id, code, level (`block`,`mandal`,`district`,`state`), name, parent_code, boundary_version, geom (MultiPolygon, 4326), valid_from, valid_to | Stable code + versioned boundary |
| `crop_calendars` | crop_code, geo_code, season, planting_window, stage_windows | Used by forecast features |
| `crops` | code, name, supported (bool), supported_from | Config |
| `targets` | code, crop_code, name, kind (`disease`,`pest`,`abiotic`,`healthy`,`unknown`), supported, taxonomy_note | Config |
| `growing_areas` | id, owner_user_id, geo_code, precision (`block` default), geom (Point/Polygon, 4326) nullable, label, created_at | Approximate by default |
| `crop_cycles` | id, growing_area_id, crop_code, variety, planting_date, stage, stage_updated_at | Stage history appended separately if needed |

### 4.3 Observations and media

| Table | Key columns | Notes |
|---|---|---|
| `observations` | id, client_report_id, user_id (creator), subject_user_id (on-behalf), growing_area_id, crop_code, variety, growth_stage, notes, captured_at, submitted_at, status, created_at | `unique(user_id, client_report_id)` |
| `image_assets` | id, observation_id, storage_key, original_width, original_height, bytes, content_hash, mime, source (`camera`,`gallery`), compression (jsonb), upload_status, created_at | Private bucket |
| `image_quality_results` | id, image_id, gate_version, result, flags (jsonb), thresholds (jsonb), created_at | Insert-only |
| `image_predictions` | id, image_id, model_version, candidates (jsonb), probabilities (jsonb), confidence_band, calibrated (bool), calibration_version, abstained (bool), abstain_reason, decision_thresholds (jsonb: per-class `τ_c`, margin `m`, entropy `h`, `ood_max`), ood_score, generated_at | Insert-only; thresholds and OOD stored per row so the decision is reproducible (D8) |
| `review_requests` | id, observation_id, requested_by, reason, status, created_at | |

Observation status values:
`draft`, `pending_upload`, `uploaded`, `assessing`, `assessed`, `abstained`, `failed`,
`pending_review`, `reviewed`.

### 4.4 Review and verification

| Table | Key columns | Notes |
|---|---|---|
| `reviews` | id, observation_id, reviewer_id, decision, reason_code, corrected_label, severity, note, created_at | Insert-only |
| `review_evidence` | id, review_id, type (`image_note`,`field_observation`,`lab_result`), value, source, created_at | |
| `review_events` | id, observation_id, from_status, to_status, actor_id, reason, created_at | Immutable |
| `observation_verification` | observation_id (PK), status, evidence_tier (`confirmed`,`probable`,`unverified`,`rejected`,`duplicate`,`needs_visit`,`unresolved`), verified_at, verified_by, review_id | Derived projection; rebuildable |
| `review_assignments` | observation_id, user_id, assigned_at, expires_at | Soft lock |
| `sentinel_sites` | id, crop_code, geo_code, precision, geom, active_from, active_to, panel_version, approved_by | Pre-registered absence-sampling panel (D7); no post-hoc selection |
| `sentinel_visits` | id, site_id, visit_date, scheduled (bool), observer_id, target_code, observed (`present`,`absent`,`indeterminate`), evidence_ref, created_at | Sole source of forecast negatives; a missing visit is never a negative |

**Forecast label eligibility (D7):** a case enters forecast features only when its status is
`confirmed` or `probable`, `verified_at <= cutoff`, and its event date is `<= cutoff`.
`probable` retains its `evidence_tier` as a lower-confidence flag. `unverified`,
`needs_visit`, `duplicate`, `unresolved` and `rejected` are never eligible. A `sentinel_visits`
row is a negative only when `scheduled = true`, `observed = 'absent'`, the target is
supported, the visit is inside the label window, and the D9 coverage gate passed.

### 4.5 Forecast and weather

| Table | Key columns | Notes |
|---|---|---|
| `weather_snapshots` | id, grid_id/geo_code, source, source_timestamp, fetched_at, variables (jsonb), completeness, is_stale | One row per ingest unit |
| `feature_snapshots` | id, crop_code, target_code, geo_code, horizon_days, issue_time, features (jsonb), source_refs (jsonb), created_at | Immutable; referenced by forecasts |
| `forecasts` | id, crop_code, target_code, geo_code, horizon_days, issue_time, valid_from, valid_to, risk_band, probability (numeric nullable), confidence_band, coverage, drivers (jsonb), model_version, feature_snapshot_id, is_demo, created_at | Insert-only per run |
| `forecast_runs` | id, started_at, finished_at, status, model_version, areas_total, areas_scored, areas_insufficient, error | Job audit |

`risk_band` values: `low`, `moderate`, `high`, `urgent`, `insufficient_data`.
`coverage` values: `good`, `partial`, `low`, `unknown`.

### 4.6 Advisory and alerts

| Table | Key columns | Notes |
|---|---|---|
| `advisories` | id, crop_code, target_code, geo_scope, language, title, current_version_id, status | Logical advisory |
| `advisory_versions` | id, advisory_id, version, body_md, action_types (jsonb), author_id, valid_from, valid_to, content_hash, created_at | Immutable |
| `advisory_approvals` | id, version_id, approver_id, role, approved_at, notes | Required before serving |
| `alert_policies` | id, geo_code, target_code, min_band, min_coverage, cooldown_hours, channels, approved_by, active | Config |
| `alerts` | id, forecast_id, geo_code, target_code, band, window_from, window_to, message_version, created_at, dedupe_key (unique) | |
| `alert_deliveries` | id, alert_id, user_id, channel, status, provider_ref, sent_at, delivered_at, error | |

### 4.7 Registry and audit

| Table | Key columns | Notes |
|---|---|---|
| `model_registry` | id, kind (`image_gate`,`image_classifier`,`forecast`), version, artefact_key, checksum, metrics (jsonb), status (`draft`,`validated`,`approved`,`retired`), approved_by, approved_at, created_at | Serving requires `approved` |
| `audit_events` | id, actor_id, actor_role, action, entity_type, entity_id, reason, request_id, ip_hash, created_at | Insert-only; no PII payloads |
| `export_jobs` | id, requested_by, purpose, filters (jsonb), status, row_count, created_at | Audited |

---

## 5. Enforced constraints (examples)

```sql
-- Predictions are immutable
CREATE TRIGGER image_predictions_no_update
BEFORE UPDATE OR DELETE ON image_predictions
FOR EACH ROW EXECUTE FUNCTION reject_mutation();

-- A prediction requires a quality result for the same image
ALTER TABLE image_predictions
  ADD CONSTRAINT fk_prediction_image FOREIGN KEY (image_id) REFERENCES image_assets(id);

-- An abstention must carry a reason; the threshold set must be stored for reproduction
ALTER TABLE image_predictions
  ADD CONSTRAINT ck_abstain_has_reason
    CHECK (abstained = false OR abstain_reason IS NOT NULL),
  ADD CONSTRAINT ck_prediction_thresholds
    CHECK (decision_thresholds IS NOT NULL),
  ADD CONSTRAINT ck_calibration_version
    CHECK (calibrated = false OR calibration_version IS NOT NULL);

-- Idempotent observation creation
ALTER TABLE observations
  ADD CONSTRAINT uq_observation_client UNIQUE (user_id, client_report_id);

-- Verified evidence only from human decisions
ALTER TABLE observation_verification
  ADD CONSTRAINT ck_verified_requires_review
  CHECK (status = 'unverified' OR review_id IS NOT NULL);

-- Forecast must carry lineage
ALTER TABLE forecasts
  ADD CONSTRAINT ck_forecast_lineage
  CHECK (feature_snapshot_id IS NOT NULL AND model_version IS NOT NULL);

-- No probability without calibration approval
ALTER TABLE forecasts
  ADD CONSTRAINT ck_probability_nullable CHECK (probability IS NULL OR probability BETWEEN 0 AND 1);
```

Additional rules enforced in services:

- A forecast with `coverage = 'low'` must be `insufficient_data`, not a scored band.
- `confirmed` verification requires a review with a `lab_result` or `field_observation`
  evidence row and a `pathologist` actor.
- Advisory serving requires at least one `advisory_approvals` row and `valid_to` in the
  future.

---

## 6. Geospatial policy

- `geographies.geom` is authoritative for aggregation; `boundary_version` is stored with
  every forecast and export.
- Observation location defaults to `precision = 'block'` and `geo_code`; precise geometry
  is nullable and never required.
- Precise geometry columns are excluded from API serialisers for roles without
  `view_precise_location`.
- Map endpoints aggregate in SQL (`ST_AsMVT` / `ST_Intersection`) — never ship raw points
  to the browser for public layers.
- Distance-weighted features use geography type and a documented decay; computed in the
  forecast pipeline, not on the client.
- Small-count suppression is implemented in a view/function, not in the UI.

---

## 7. Indexing baseline

| Query | Index |
|---|---|
| Observation history by user, newest first | `(user_id, created_at desc)` |
| Queue by area/status/urgency | `(geo_code, status, urgency_score desc, created_at)` |
| Forecast lookup | `(crop_code, target_code, geo_code, issue_time desc)` |
| Alerts dedupe | `unique(dedupe_key)` |
| Audit by entity | `(entity_type, entity_id, created_at desc)` |
| Weather freshness | `(geo_code, source_timestamp desc)` |
| Image hash dedupe | `(content_hash)` |

---

## 8. Object storage layout

```
s3://<private-bucket>/
  observations/<yyyy>/<mm>/<observation_id>/<image_id>/original.<ext>
  observations/<yyyy>/<mm>/<observation_id>/<image_id>/preview.jpg
  advisories/<advisory_id>/<version>/<file>
  models/<kind>/<version>/<artefact>
  exports/<export_job_id>/<file>
```

Rules:

- Private bucket; access only via short-lived presigned URLs (≤ 10 min).
- Content-addressed checksum stored; duplicates detected by hash.
- Original retained; derivatives separate and regenerable.
- EXIF GPS stripped unless explicitly consented and needed.
- Lifecycle policy per data class; deletion propagates to derivatives and previews.
- No public read ACLs; no directory listing.

---

## 9. Migrations

- Alembic, one logical change per revision, descriptive message.
- Forward-only in production; rollback is a restore or a compensating migration, documented
  in the PR.
- Every migration states: data impact, lock risk, expected duration, backfill plan.
- Destructive changes require a two-step deploy (expand → migrate → contract).
- Migrations run in CI against a seeded database and against an empty database.
- No migration may import application code that can change later.

---

## 10. Seeds and demo data

- Seed reference data: roles, crops, targets, geographies (demo boundary version), risk-band
  config, alert policies.
- Demo observations/forecasts are created only by an explicit `seed-demo` command.
- Every demo row carries `is_demo = true` (or a `demo_` ID prefix) and is rendered with a
  visible demo badge.
- Demo data must never be mixed into a production environment automatically.
- Fixtures use synthetic images and fake identifiers only. No real farmer data in tests.

---

## 11. Retention and deletion

| Data class | Retention | Deletion behaviour |
|---|---|---|
| Observations + images | Programme policy (TBD with legal) | Soft delete → hard delete job; derivatives removed |
| Predictions/reviews/audit | Longer than case data; audit immutable | Never hard-deleted except legal order |
| Weather/feature snapshots | Retain for forecast reproducibility | Archive after configured period |
| Sessions/OTP/presigned URLs | Short TTL | Purged by job |
| Exports | Short TTL | Deleted after download window |
| Backups | Documented rotation | Deletion propagates on next restore cycle |

Deletion request flow: verify identity → mark `deleted_at` → revoke sessions → schedule
hard delete → retain audit and non-identifying aggregates → record completion.

---

## 12. Backup and recovery

- Daily automated Postgres backup + WAL archiving where available.
- Object storage versioning enabled; deletion protected by lifecycle rules.
- Restore tested before pilot; document RTO/RPO.
- Model artefacts and registry exported with each backup set.
- Quarterly restore drill; result recorded in `progress-tracker.md`.

---

## 13. Acceptance criteria

- [ ] Schema creates from zero via migrations on an empty database.
- [ ] Migrations apply cleanly to a seeded database.
- [ ] `unique(user_id, client_report_id)` prevents duplicate observations.
- [ ] Update/delete on prediction, review and audit tables is rejected.
- [ ] A forecast cannot be inserted without a feature snapshot and model version.
- [ ] Forecast label queries exclude `unverified`, `needs_visit`, `duplicate`, `unresolved` and
      `rejected`, include `confirmed` and `probable` with evidence tier, and enforce
      `verified_at <= cutoff` plus event date `<= cutoff` (test).
- [ ] A `sentinel_visits` row is a negative only when scheduled, absent, in-window and
      coverage-passing; a missing visit is not a negative (test).
- [ ] Every `image_predictions` row stores `decision_thresholds` (per-class `τ_c`, margin,
      entropy, `ood_max`) and `ood_score`; the abstention decision is reproducible from them.
- [ ] An abstained prediction has a reason code; a calibrated prediction has a
      `calibration_version` (test the check constraints).
- [ ] Precise geometry is absent from API responses for unauthorised roles (test).
- [ ] Small-count suppression is enforced in the query layer (test).
- [ ] Advisory retrieval fails when no approval exists (test).
- [ ] Serving an unapproved model version is refused (test).
- [ ] Demo rows are distinguishable and never returned by default production queries.
- [ ] Backup restore drill completed and documented before pilot.

---

## 14. Out of scope

- Data warehouse / lakehouse.
- Streaming ingestion.
- Multi-region replication.
- Graph database for spread modelling.
- Client-side database access.
- A second ORM or schema-generation tool.

---

## 15. Open questions

1. Final retention periods (legal/programme decision).
2. Do we need historical boundary versions beyond the current pilot period?
3. What is the target RTO/RPO for the pilot?
4. Is a read replica needed for dashboard load at pilot scale? (Likely no.)

---

## 16. Blueprint traceability

| Blueprint chapter | Where this spec uses it |
|---|---|
| 21 — Data cleaning and preprocessing | §2 conventions, §10 seeds |
| 22 — Dataset splitting and leakage prevention | §5 enforced constraints, §13 acceptance |
| 23 — Weather and environmental data | §4.5 weather snapshots |
| 24 — Historical records | §4.4 verification projection |
| 25 — Database design | Whole spec |
| 26 — Backend API design | §9 migrations, §13 acceptance |
| 47 — Deployment and infrastructure | §12 backup and recovery |
| App. C — Example forecast API response | §4.5 forecasts |
| App. D — Database entity checklist | §3 entity map, §4 core tables |
| App. E — API and integration checklist | §9 migrations, §13 acceptance |

Data-quality and governance rules are in `../docs-context/data-foundation.md` §2. The
append-only and lineage invariants are stated in
`../docs-context/architecture-context.md` §7.
