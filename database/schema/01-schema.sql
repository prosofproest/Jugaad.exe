-- =============================================================================
-- AI-Based Early Pest and Disease — reference schema v1
-- =============================================================================
-- Status:   DRAFT — reference DDL for review, not a production migration.
-- Authority: final/feature-specs/05-data-layer.md
-- Owner:     Data engineer (TBD)
-- Updated:   2026-11-06
--
-- This file implements the schema slices named in phase-plan.md §4.5. It is the
-- reference for the SQLAlchemy models + Alembic migrations that will live in
-- backend/ (05-data-layer.md §1, §9). It is NOT a second schema authority and
-- must never be applied to production by hand.
--
-- Conventions (05-data-layer.md §2):
--   * PostgreSQL 16 + PostGIS 3.x
--   * UUID primary keys via gen_random_uuid()
--   * text + CHECK for closed sets (not native enums)
--   * timestamptz, UTC; external data carries source_timestamp + fetched_at
--   * predictions, reviews, review evidence/events, audit, feature snapshots,
--     advisory versions, consents and forecasts are append-only (triggers)
--   * PostGIS geometry is used only where spatial queries are needed
--   * values marked TBD are decisions, not implementation details; do not
--     replace them with plausible guesses (R6)
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- -----------------------------------------------------------------------------
-- 0. Helper functions
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION reject_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION
    'Table % is append-only; % is not permitted', TG_TABLE_NAME, TG_OP
    USING ERRCODE = 'restrict_violation';
END;
$$;

-- Labels are append-only in content, but the previous row must be marked
-- superseded when a correction is appended. Only label_status may change, and only
-- along the documented transitions.
CREATE OR REPLACE FUNCTION labels_guard_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'labels are append-only; DELETE is not permitted'
      USING ERRCODE = 'restrict_violation';
  END IF;

  IF (to_jsonb(NEW) - 'label_status') IS DISTINCT FROM (to_jsonb(OLD) - 'label_status') THEN
    RAISE EXCEPTION 'labels are append-only; only label_status may change'
      USING ERRCODE = 'restrict_violation';
  END IF;

  IF NOT (
    (OLD.label_status = 'active' AND NEW.label_status IN ('superseded', 'ambiguous'))
    OR (OLD.label_status = 'ambiguous' AND NEW.label_status IN ('superseded', 'adjudicated'))
  ) THEN
    RAISE EXCEPTION 'invalid label_status transition: % -> %',
      OLD.label_status, NEW.label_status
      USING ERRCODE = 'restrict_violation';
  END IF;

  RETURN NEW;
END;
$$;

-- Small-count suppression mechanism (D9 sets the threshold; no default is
-- invented here). Returns NULL when the count is below the supplied threshold.
CREATE OR REPLACE FUNCTION suppress_small_count(n integer, threshold integer)
RETURNS integer
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT CASE
    WHEN n IS NULL THEN NULL
    WHEN threshold IS NULL THEN NULL
    WHEN n < threshold THEN NULL
    ELSE n
  END;
$$;

COMMENT ON FUNCTION suppress_small_count(integer, integer) IS
  'Small-count suppression. The threshold is a D9 decision and must be passed by the caller; this function asserts no default.';

-- =============================================================================
-- 1. Identity
-- =============================================================================

CREATE TABLE roles (
  code        text PRIMARY KEY,
  description text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ck_roles_code CHECK (code IN (
    'farmer', 'extension_worker', 'pathologist', 'agronomist', 'admin'
  ))
);

CREATE TABLE users (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  phone_e164    text UNIQUE,
  email         text UNIQUE,
  password_hash text,
  status        text NOT NULL DEFAULT 'active',
  locale        text NOT NULL DEFAULT 'en',
  token_version integer NOT NULL DEFAULT 1,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  deleted_at    timestamptz,
  is_demo       boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_users_status CHECK (status IN ('active', 'suspended', 'deleted')),
  CONSTRAINT ck_users_contact CHECK (
    phone_e164 IS NOT NULL OR email IS NOT NULL OR status = 'deleted'
  ),
  CONSTRAINT ck_users_token_version CHECK (token_version >= 1)
);

COMMENT ON COLUMN users.status IS
  'Proposed closed set; confirm against 03-auth-and-roles.md when the identity module is built.';
COMMENT ON COLUMN users.deleted_at IS
  'Soft delete. Hard-delete jobs anonymise the row and retain the UUID so audit FKs stay valid.';

CREATE TABLE user_roles (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  role_code  text NOT NULL REFERENCES roles(code) ON DELETE RESTRICT,
  granted_by uuid REFERENCES users(id) ON DELETE RESTRICT,
  granted_at timestamptz NOT NULL DEFAULT now(),
  revoked_at timestamptz,
  CONSTRAINT ck_user_roles_dates CHECK (revoked_at IS NULL OR revoked_at >= granted_at)
);

CREATE UNIQUE INDEX uq_user_roles_active
  ON user_roles (user_id, role_code)
  WHERE revoked_at IS NULL;

CREATE TABLE devices (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  platform    text NOT NULL,
  app_version text,
  last_seen_at timestamptz,
  push_token  text,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ck_devices_platform CHECK (platform IN ('android', 'ios', 'web'))
);

COMMENT ON TABLE devices IS 'No advertising IDs or device fingerprints are stored.';

CREATE TABLE consents (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  type       text NOT NULL,
  version    text NOT NULL,
  granted    boolean NOT NULL,
  text_hash  text NOT NULL,
  channel    text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  is_demo    boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_consents_type CHECK (type IN (
    'service_privacy', 'image_assessment', 'approximate_location',
    'research_model_improvement', 'extension_contact'
  )),
  CONSTRAINT ck_consents_channel CHECK (channel IN ('mobile', 'web', 'staff', 'paper'))
);

COMMENT ON TABLE consents IS 'Append-only consent event log. Withdrawal is a new row, never an update.';

CREATE TABLE user_area_assignments (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  geo_code    text NOT NULL,
  level       text NOT NULL,
  active_from timestamptz NOT NULL DEFAULT now(),
  active_to   timestamptz,
  CONSTRAINT ck_user_area_level CHECK (level IN ('block', 'mandal', 'district', 'state')),
  CONSTRAINT ck_user_area_dates CHECK (active_to IS NULL OR active_to > active_from)
);

CREATE TABLE sessions (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  refresh_hash text NOT NULL UNIQUE,
  family_id    uuid NOT NULL,
  expires_at   timestamptz NOT NULL,
  revoked_at   timestamptz,
  ip_hash      text,
  user_agent   text,
  created_at   timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE sessions IS 'Refresh tokens are stored hashed; raw tokens are never stored or logged.';

-- =============================================================================
-- 2. Geography and crop context
-- =============================================================================

CREATE TABLE geographies (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code             text NOT NULL,
  level            text NOT NULL,
  name             text NOT NULL,
  parent_code      text,
  boundary_version text NOT NULL,
  geom             geometry(MultiPolygon, 4326),
  valid_from       date NOT NULL,
  valid_to         date,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  is_demo          boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_geographies_level CHECK (level IN ('block', 'mandal', 'district', 'state')),
  CONSTRAINT ck_geographies_dates CHECK (valid_to IS NULL OR valid_to > valid_from),
  CONSTRAINT uq_geographies_code_version UNIQUE (code, boundary_version)
);

COMMENT ON COLUMN geographies.parent_code IS
  'Stable parent code. No single-column FK because geographies.code is versioned by boundary_version.';
COMMENT ON COLUMN geographies.geom IS
  'Authoritative geometry for aggregation. Keep boundary_version with every forecast/export.';

CREATE TABLE crops (
  code           text PRIMARY KEY,
  name           text NOT NULL,
  supported      boolean NOT NULL DEFAULT false,
  supported_from date,
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now(),
  is_demo        boolean NOT NULL DEFAULT false
);

COMMENT ON TABLE crops IS
  'Reference data. No crop row is seeded until D1 is recorded; supported = false by default.';

CREATE TABLE targets (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code          text NOT NULL,
  crop_code     text NOT NULL REFERENCES crops(code) ON DELETE RESTRICT,
  name          text NOT NULL,
  kind          text NOT NULL,
  class_kind    text,
  supported     boolean NOT NULL DEFAULT false,
  taxonomy_note text,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  is_demo       boolean NOT NULL DEFAULT false,
  CONSTRAINT uq_targets_crop_code UNIQUE (crop_code, code),
  CONSTRAINT ck_targets_kind CHECK (kind IN ('disease', 'pest', 'abiotic', 'healthy', 'unknown')),
  CONSTRAINT ck_targets_class_kind CHECK (
    class_kind IS NULL OR class_kind IN (
      'pathogen_identity', 'symptom_pattern', 'pest_damage', 'non_condition'
    )
  )
);

COMMENT ON COLUMN targets.class_kind IS
  'Label-architecture class kind from database/labelling/01-labelling-handbook.md §4.1. NULL until the taxonomy is approved under D1.';

CREATE TABLE crop_calendars (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_code       text NOT NULL REFERENCES crops(code) ON DELETE RESTRICT,
  geo_code        text NOT NULL,
  season          text NOT NULL,
  planting_window jsonb NOT NULL,
  stage_windows   jsonb NOT NULL,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  is_demo         boolean NOT NULL DEFAULT false,
  CONSTRAINT uq_crop_calendars UNIQUE (crop_code, geo_code, season)
);

CREATE TABLE growing_areas (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  geo_code      text NOT NULL,
  precision     text NOT NULL DEFAULT 'block',
  geom          geometry(Geometry, 4326),
  label         text,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  deleted_at    timestamptz,
  is_demo       boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_growing_areas_precision CHECK (precision IN ('block', 'field', 'exact')),
  CONSTRAINT ck_growing_areas_geom CHECK (
    geom IS NULL OR GeometryType(geom) IN ('POINT', 'POLYGON', 'MULTIPOLYGON')
  )
);

COMMENT ON COLUMN growing_areas.geom IS
  'Precise geometry is optional and never required. Approximate block precision is the default; access is role-gated.';

CREATE TABLE crop_cycles (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  growing_area_id  uuid NOT NULL REFERENCES growing_areas(id) ON DELETE RESTRICT,
  crop_code        text NOT NULL REFERENCES crops(code) ON DELETE RESTRICT,
  variety          text,
  planting_date    date,
  stage            text,
  stage_updated_at timestamptz,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now(),
  is_demo           boolean NOT NULL DEFAULT false
);

COMMENT ON COLUMN crop_cycles.stage IS
  'Crop-specific stage set is TBD — D1. Stage history is appended in the events/audit layer if required.';

-- =============================================================================
-- 3. Observations and media
-- =============================================================================

CREATE TABLE observations (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  client_report_id text NOT NULL,
  user_id          uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  subject_user_id  uuid REFERENCES users(id) ON DELETE RESTRICT,
  growing_area_id  uuid REFERENCES growing_areas(id) ON DELETE RESTRICT,
  crop_code        text NOT NULL REFERENCES crops(code) ON DELETE RESTRICT,
  variety          text,
  growth_stage     text,
  notes            text,
  captured_at      timestamptz NOT NULL,
  submitted_at     timestamptz NOT NULL DEFAULT now(),
  event_date       date,
  status           text NOT NULL DEFAULT 'draft',
  geo_code         text NOT NULL,
  urgency_score    numeric(8,3),
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  deleted_at       timestamptz,
  is_demo          boolean NOT NULL DEFAULT false,
  CONSTRAINT uq_observation_client UNIQUE (user_id, client_report_id),
  CONSTRAINT ck_observations_status CHECK (status IN (
    'draft', 'pending_upload', 'uploaded', 'assessing', 'assessed',
    'abstained', 'failed', 'pending_review', 'reviewed'
  )),
  CONSTRAINT ck_observations_notes_no_pii CHECK (notes IS NULL OR length(notes) <= 4000)
);

COMMENT ON COLUMN observations.geo_code IS
  'Denormalised from growing_areas for area-scoped queue filtering. Maintained by the service layer.';
COMMENT ON COLUMN observations.urgency_score IS
  'Computed server-side from the triage formula in 04-expert-review.md §5. No client writes.';
COMMENT ON COLUMN observations.event_date IS
  'Earliest observed/onset date. Null means unknown; never substitute submitted_at for forecast eligibility (D7).';

CREATE TABLE image_assets (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  observation_id     uuid NOT NULL REFERENCES observations(id) ON DELETE RESTRICT,
  storage_key        text NOT NULL UNIQUE,
  original_width     integer NOT NULL,
  original_height    integer NOT NULL,
  bytes              integer NOT NULL,
  content_hash       text NOT NULL,
  mime               text NOT NULL,
  source             text NOT NULL,
  compression        jsonb,
  upload_status      text NOT NULL DEFAULT 'pending',
  exif_gps_present   boolean NOT NULL DEFAULT false,
  exif_stripped      boolean NOT NULL DEFAULT false,
  created_at         timestamptz NOT NULL DEFAULT now(),
  is_demo            boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_image_assets_source CHECK (source IN ('camera', 'gallery')),
  CONSTRAINT ck_image_assets_upload_status CHECK (upload_status IN (
    'pending', 'uploading', 'complete', 'failed'
  )),
  CONSTRAINT ck_image_assets_dimensions CHECK (original_width > 0 AND original_height > 0),
  CONSTRAINT ck_image_assets_bytes CHECK (bytes > 0),
  CONSTRAINT ck_image_assets_mime CHECK (mime IN ('image/jpeg', 'image/png', 'image/webp')),
  CONSTRAINT ck_image_assets_exif CHECK (exif_stripped = false OR exif_gps_present = true)
);

COMMENT ON TABLE image_assets IS
  'Originals only. Derivatives live in object storage and are not rows here. Never edit an original.';
COMMENT ON COLUMN image_assets.compression IS
  'Client compression settings recorded per FR-02-10, documented JSONB shape.';

CREATE TABLE image_quality_results (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  image_id     uuid NOT NULL REFERENCES image_assets(id) ON DELETE RESTRICT,
  gate_version text NOT NULL,
  result       text NOT NULL,
  flags        jsonb NOT NULL DEFAULT '{}'::jsonb,
  thresholds   jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at   timestamptz NOT NULL DEFAULT now(),
  is_demo      boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_image_quality_result CHECK (result IN ('pass', 'fail', 'abstain'))
);

COMMENT ON TABLE image_quality_results IS 'Insert-only quality-gate result.';

CREATE TABLE image_predictions (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  image_id           uuid NOT NULL REFERENCES image_assets(id) ON DELETE RESTRICT,
  model_version      text NOT NULL,
  candidates         jsonb NOT NULL,
  probabilities      jsonb,
  confidence_band    text NOT NULL,
  calibrated         boolean NOT NULL DEFAULT false,
  calibration_version text,
  abstained          boolean NOT NULL DEFAULT false,
  abstain_reason     text,
  decision_thresholds jsonb NOT NULL,
  ood_score          numeric NOT NULL,
  generated_at       timestamptz NOT NULL DEFAULT now(),
  is_demo            boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_prediction_confidence_band CHECK (confidence_band IN (
    'low', 'medium', 'high', 'not_calibrated'
  )),
  CONSTRAINT ck_prediction_abstain_reason CHECK (
    abstained = false OR abstain_reason IN (
      'below_class_threshold', 'low_margin', 'high_entropy',
      'out_of_distribution', 'unsupported_crop', 'quality_gate_failed'
    )
  ),
  CONSTRAINT ck_prediction_thresholds CHECK (decision_thresholds IS NOT NULL),
  CONSTRAINT ck_prediction_calibration CHECK (
    calibrated = false OR calibration_version IS NOT NULL
  )
);

COMMENT ON TABLE image_predictions IS
  'Append-only. decision_thresholds stores per-class tau_c, margin, entropy and ood_max so the abstention decision is reproducible (D8).';

CREATE TABLE review_requests (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  observation_id uuid NOT NULL REFERENCES observations(id) ON DELETE RESTRICT,
  requested_by  uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  reason        text NOT NULL,
  status        text NOT NULL DEFAULT 'open',
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ck_review_requests_status CHECK (status IN ('open', 'fulfilled', 'declined', 'expired'))
);

-- =============================================================================
-- 4. Review and verification
-- =============================================================================

CREATE TABLE reviews (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  observation_id   uuid NOT NULL REFERENCES observations(id) ON DELETE RESTRICT,
  reviewer_id      uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  decision         text NOT NULL,
  reason_code      text,
  corrected_label  text,
  severity         text,
  note             text,
  created_at       timestamptz NOT NULL DEFAULT now(),
  is_demo          boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_reviews_decision CHECK (decision IN (
    'confirmed', 'probable', 'rejected', 'duplicate', 'needs_visit', 'unresolved'
  )),
  CONSTRAINT ck_reviews_note CHECK (note IS NULL OR length(note) <= 4000)
);

COMMENT ON TABLE reviews IS
  'Append-only review decision. A correction is a new row; history is never overwritten.';

CREATE TABLE review_evidence (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  review_id  uuid NOT NULL REFERENCES reviews(id) ON DELETE RESTRICT,
  type       text NOT NULL,
  value      text NOT NULL,
  source     text,
  created_at timestamptz NOT NULL DEFAULT now(),
  is_demo    boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_review_evidence_type CHECK (type IN (
    'image_note', 'field_observation', 'lab_result'
  ))
);

-- Extension to 05-data-layer.md §4.4, required by
-- database/labelling/01-labelling-handbook.md §8. The review records the human
-- decision; the label is the append-only, training-facing record with provenance.
-- They are separate so an untrained or unaudited decision can never be mistaken for a
-- usable label.
CREATE TABLE labels (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  observation_id        uuid NOT NULL REFERENCES observations(id) ON DELETE RESTRICT,
  image_id              uuid REFERENCES image_assets(id) ON DELETE RESTRICT,
  review_id             uuid NOT NULL REFERENCES reviews(id) ON DELETE RESTRICT,
  target_code           text NOT NULL,
  class_kind            text NOT NULL,
  label_origin          text NOT NULL,
  verification_tier     text NOT NULL,
  severity              text,
  severity_basis        text,
  reviewer_id           uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  reviewed_at           timestamptz NOT NULL,
  handbook_version      text NOT NULL,
  taxonomy_version      text NOT NULL,
  label_status          text NOT NULL DEFAULT 'active',
  supersedes_label_id   uuid REFERENCES labels(id) ON DELETE RESTRICT,
  hard_negative         boolean NOT NULL DEFAULT false,
  hard_negative_code    text,
  abstention_role       text NOT NULL DEFAULT 'none',
  ambiguity_reason      text,
  retain_for_abstention boolean NOT NULL DEFAULT true,
  is_demo               boolean NOT NULL DEFAULT false,
  created_at            timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ck_labels_class_kind CHECK (class_kind IN (
    'pathogen_identity', 'symptom_pattern', 'pest_damage', 'non_condition'
  )),
  CONSTRAINT ck_labels_origin CHECK (label_origin IN (
    'suspected', 'expert_confirmed', 'lab_confirmed'
  )),
  CONSTRAINT ck_labels_tier CHECK (verification_tier IN (
    'confirmed', 'probable', 'unverified', 'rejected', 'duplicate',
    'needs_visit', 'unresolved'
  )),
  CONSTRAINT ck_labels_status CHECK (label_status IN (
    'active', 'superseded', 'adjudicated', 'ambiguous'
  )),
  CONSTRAINT ck_labels_hard_negative CHECK (
    hard_negative = false OR hard_negative_code IS NOT NULL
  ),
  CONSTRAINT ck_labels_hard_negative_code CHECK (
    hard_negative_code IS NULL OR hard_negative_code IN (
      'HN-HEALTHY', 'HN-ABIOTIC', 'HN-OTHER-CONDITION', 'HN-OTHER-CROP',
      'HN-NON-PLANT', 'HN-POOR-IMAGE', 'HN-LOOK-ALIKE', 'HN-ARCHIVE-NEAR'
    )
  ),
  CONSTRAINT ck_labels_abstention_role CHECK (abstention_role IN (
    'insufficient_evidence', 'unknown', 'mixed', 'out_of_domain',
    'hard_negative', 'none'
  )),
  CONSTRAINT ck_labels_supersedes CHECK (
    supersedes_label_id IS NULL OR supersedes_label_id <> id
  ),
  CONSTRAINT ck_labels_training_origin CHECK (
    verification_tier <> 'confirmed'
    OR label_origin IN ('expert_confirmed', 'lab_confirmed')
  )
);

COMMENT ON TABLE labels IS
  'Append-only label record. A suspected label may be stored but is never a training label; corrections supersede, never update. target_code is validated against the approved taxonomy by the service layer because the taxonomy also contains uncertainty classes that are not rows in targets.';

CREATE TABLE review_events (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  observation_id uuid NOT NULL REFERENCES observations(id) ON DELETE RESTRICT,
  from_status   text,
  to_status     text NOT NULL,
  actor_id      uuid REFERENCES users(id) ON DELETE RESTRICT,
  reason        text,
  created_at    timestamptz NOT NULL DEFAULT now(),
  is_demo       boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_review_events_from CHECK (from_status IS NULL OR from_status IN (
    'pending_review', 'confirmed', 'probable', 'rejected', 'duplicate',
    'needs_visit', 'unresolved'
  )),
  CONSTRAINT ck_review_events_to CHECK (to_status IN (
    'pending_review', 'confirmed', 'probable', 'rejected', 'duplicate',
    'needs_visit', 'unresolved'
  ))
);

COMMENT ON TABLE review_events IS 'Immutable verification state-transition log.';

CREATE TABLE observation_verification (
  observation_id uuid PRIMARY KEY REFERENCES observations(id) ON DELETE RESTRICT,
  status         text NOT NULL DEFAULT 'unverified',
  evidence_tier  text,
  verified_at    timestamptz,
  verified_by    uuid REFERENCES users(id) ON DELETE RESTRICT,
  review_id      uuid REFERENCES reviews(id) ON DELETE RESTRICT,
  updated_at     timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ck_observation_verification_status CHECK (status IN (
    'confirmed', 'probable', 'unverified', 'rejected', 'duplicate',
    'needs_visit', 'unresolved'
  )),
  CONSTRAINT ck_observation_verification_tier CHECK (evidence_tier IS NULL OR evidence_tier IN (
    'confirmed', 'probable', 'unverified', 'rejected', 'duplicate',
    'needs_visit', 'unresolved'
  )),
  CONSTRAINT ck_verified_requires_review CHECK (status = 'unverified' OR review_id IS NOT NULL)
);

COMMENT ON TABLE observation_verification IS
  'Derived projection, rebuildable from reviews and review_events. Not a retention source of truth.';

CREATE TABLE review_assignments (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  observation_id uuid NOT NULL UNIQUE REFERENCES observations(id) ON DELETE CASCADE,
  user_id       uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  assigned_at   timestamptz NOT NULL DEFAULT now(),
  expires_at    timestamptz NOT NULL,
  CONSTRAINT ck_review_assignments_expiry CHECK (expires_at > assigned_at)
);

COMMENT ON TABLE review_assignments IS 'Soft lock only; one current assignment per observation.';

CREATE TABLE sentinel_sites (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_code     text NOT NULL REFERENCES crops(code) ON DELETE RESTRICT,
  geo_code      text NOT NULL,
  precision     text NOT NULL,
  geom          geometry(Point, 4326),
  active_from   date NOT NULL,
  active_to     date,
  panel_version text NOT NULL,
  approved_by   uuid REFERENCES users(id) ON DELETE RESTRICT,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  is_demo       boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_sentinel_sites_precision CHECK (precision IN ('approximate', 'exact')),
  CONSTRAINT ck_sentinel_sites_dates CHECK (active_to IS NULL OR active_to > active_from)
);

COMMENT ON TABLE sentinel_sites IS
  'Pre-registered absence-sampling panel (D7). No post-hoc site selection; panel_version is monotonic.';

CREATE TABLE sentinel_visits (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  site_id       uuid NOT NULL REFERENCES sentinel_sites(id) ON DELETE RESTRICT,
  visit_date    date NOT NULL,
  scheduled     boolean NOT NULL,
  observer_id   uuid REFERENCES users(id) ON DELETE RESTRICT,
  target_code   text NOT NULL,
  observed      text NOT NULL,
  evidence_ref  text,
  coverage_pass boolean,
  created_at    timestamptz NOT NULL DEFAULT now(),
  is_demo       boolean NOT NULL DEFAULT false,
  CONSTRAINT uq_sentinel_visit UNIQUE (site_id, visit_date, target_code),
  CONSTRAINT ck_sentinel_visits_observed CHECK (observed IN ('present', 'absent', 'indeterminate'))
);

COMMENT ON COLUMN sentinel_visits.scheduled IS
  'Must be true for a visit to yield a negative. A visit triggered by a report is not scheduled.';
COMMENT ON COLUMN sentinel_visits.coverage_pass IS
  'Set by the D9 coverage gate. NULL means the gate has not been evaluated and the visit is not a negative.';
COMMENT ON TABLE sentinel_visits IS
  'Sole source of forecast negatives. A missing visit is never a negative.';

-- Historical plant clinic, extension and survey records
CREATE TABLE historical_occurrences (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_code         text NOT NULL REFERENCES crops(code) ON DELETE RESTRICT,
  target_code       text NOT NULL,
  geo_code          text NOT NULL,
  boundary_version  text NOT NULL,
  verification_tier text NOT NULL,
  event_date        date NOT NULL,
  report_date       date NOT NULL,
  source_link       text NOT NULL,
  source_dataset    text NOT NULL,
  dedupe_key        text NOT NULL,
  dedupe_history    jsonb NOT NULL DEFAULT '[]'::jsonb,
  severity          text,
  evidence_summary  text,
  notes             text,
  created_at        timestamptz NOT NULL DEFAULT now(),
  is_demo           boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_hist_dates CHECK (report_date >= event_date),
  CONSTRAINT ck_hist_tier CHECK (verification_tier IN (
    'confirmed', 'probable', 'unverified', 'rejected', 'historical_clinic', 'survey'
  )),
  CONSTRAINT uq_hist_dedupe_key UNIQUE (dedupe_key)
);

COMMENT ON TABLE historical_occurrences IS
  'Historical extension records, plant clinics and field surveys. Verification tier, source link, report vs event date and dedupe history preserved. Append-only.';

-- =============================================================================
-- 5. Weather and forecast
-- =============================================================================

CREATE TABLE weather_snapshots (
  id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  grid_id                 text,
  geo_code                text NOT NULL,
  boundary_version        text NOT NULL,
  spatial_matching_method text NOT NULL DEFAULT 'centroid_nearest_station',
  station_id              text,
  station_distance_km     numeric(6,2),
  source                  text NOT NULL,
  source_timestamp        timestamptz NOT NULL,
  fetched_at              timestamptz NOT NULL DEFAULT now(),
  freshness_seconds       integer,
  variables               jsonb NOT NULL,
  completeness            numeric,
  is_stale                boolean NOT NULL DEFAULT false,
  created_at              timestamptz NOT NULL DEFAULT now(),
  is_demo                 boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_weather_completeness CHECK (
    completeness IS NULL OR (completeness >= 0 AND completeness <= 1)
  ),
  CONSTRAINT ck_weather_spatial_method CHECK (spatial_matching_method IN (
    'centroid_nearest_station', 'grid_areal_weighted_mean', 'station_idw', 'admin_polygon_intersection', 'station_exact'
  ))
);

COMMENT ON TABLE weather_snapshots IS
  'One row per ingest unit. Missing/stale weather produces insufficient_data; never impute for a scored forecast. Stores spatial matching method and boundary version.';

CREATE TABLE feature_snapshots (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_code        text NOT NULL REFERENCES crops(code) ON DELETE RESTRICT,
  target_code      text NOT NULL,
  geo_code         text NOT NULL,
  boundary_version text NOT NULL DEFAULT 'demo-2026-11',
  horizon_days     integer NOT NULL,
  issue_time       timestamptz NOT NULL,
  features         jsonb NOT NULL,
  source_refs      jsonb NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),
  is_demo          boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_feature_snapshots_horizon CHECK (horizon_days >= 0)
);

COMMENT ON TABLE feature_snapshots IS
  'Immutable feature payload referenced by forecasts. Every feature must be computable at issue_time. Stores boundary version.';

CREATE TABLE forecasts (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_code           text NOT NULL REFERENCES crops(code) ON DELETE RESTRICT,
  target_code         text NOT NULL,
  geo_code            text NOT NULL,
  boundary_version    text NOT NULL DEFAULT 'demo-2026-11',
  horizon_days        integer NOT NULL,
  issue_time          timestamptz NOT NULL,
  valid_from          timestamptz NOT NULL,
  valid_to            timestamptz NOT NULL,
  risk_band           text NOT NULL,
  probability         numeric(4,3),
  confidence_band     text NOT NULL,
  coverage            text NOT NULL,
  drivers             jsonb NOT NULL DEFAULT '[]'::jsonb,
  model_version       text NOT NULL,
  feature_snapshot_id uuid NOT NULL REFERENCES feature_snapshots(id) ON DELETE RESTRICT,
  is_demo             boolean NOT NULL DEFAULT false,
  created_at          timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ck_forecasts_risk_band CHECK (risk_band IN (
    'low', 'moderate', 'high', 'urgent', 'insufficient_data'
  )),
  CONSTRAINT ck_forecasts_confidence_band CHECK (confidence_band IN (
    'low', 'medium', 'high', 'not_calibrated'
  )),
  CONSTRAINT ck_forecasts_coverage CHECK (coverage IN ('good', 'partial', 'low', 'unknown')),
  CONSTRAINT ck_forecasts_horizon CHECK (horizon_days >= 0),
  CONSTRAINT ck_forecasts_window CHECK (valid_to > valid_from),
  CONSTRAINT ck_forecast_lineage CHECK (
    feature_snapshot_id IS NOT NULL AND model_version IS NOT NULL
  ),
  CONSTRAINT ck_probability_nullable CHECK (probability IS NULL OR probability BETWEEN 0 AND 1),
  CONSTRAINT ck_forecasts_low_coverage CHECK (
    coverage <> 'low' OR risk_band = 'insufficient_data'
  ),
  CONSTRAINT ck_forecasts_no_imputation CHECK (
    risk_band <> 'insufficient_data' OR probability IS NULL
  )
);

COMMENT ON TABLE forecasts IS
  'Insert-only per run. A scored band requires lineage; low coverage cannot produce a scored band.';

CREATE TABLE forecast_runs (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  started_at         timestamptz NOT NULL DEFAULT now(),
  finished_at        timestamptz,
  status             text NOT NULL DEFAULT 'queued',
  model_version      text NOT NULL,
  areas_total        integer NOT NULL DEFAULT 0,
  areas_scored       integer NOT NULL DEFAULT 0,
  areas_insufficient integer NOT NULL DEFAULT 0,
  error              text,
  created_at         timestamptz NOT NULL DEFAULT now(),
  is_demo            boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_forecast_runs_status CHECK (status IN (
    'queued', 'running', 'succeeded', 'partial', 'failed'
  )),
  CONSTRAINT ck_forecast_runs_counts CHECK (
    areas_total >= 0 AND areas_scored >= 0 AND areas_insufficient >= 0
  ),
  CONSTRAINT ck_forecast_runs_finished CHECK (
    finished_at IS NULL OR finished_at >= started_at
  )
);

-- =============================================================================
-- 6. Advisory and alerts
-- =============================================================================

CREATE TABLE advisories (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_code          text NOT NULL REFERENCES crops(code) ON DELETE RESTRICT,
  target_code        text NOT NULL,
  geo_scope          text NOT NULL,
  language           text NOT NULL,
  title              text NOT NULL,
  current_version_id uuid,
  status             text NOT NULL DEFAULT 'draft',
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now(),
  is_demo            boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_advisories_status CHECK (status IN (
    'draft', 'review', 'approved', 'published', 'expired', 'withdrawn'
  ))
);

CREATE TABLE advisory_versions (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  advisory_id  uuid NOT NULL REFERENCES advisories(id) ON DELETE RESTRICT,
  version      integer NOT NULL,
  body_md      text NOT NULL,
  action_types jsonb NOT NULL DEFAULT '[]'::jsonb,
  author_id    uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  valid_from   timestamptz NOT NULL,
  valid_to     timestamptz NOT NULL,
  content_hash text NOT NULL,
  created_at   timestamptz NOT NULL DEFAULT now(),
  is_demo      boolean NOT NULL DEFAULT false,
  CONSTRAINT uq_advisory_versions UNIQUE (advisory_id, version),
  CONSTRAINT ck_advisory_versions_window CHECK (valid_to > valid_from),
  CONSTRAINT ck_advisory_versions_body CHECK (length(body_md) > 0)
);

COMMENT ON TABLE advisory_versions IS
  'Immutable. Serving requires at least one advisory_approvals row and valid_to in the future.';

CREATE TABLE advisory_approvals (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version_id  uuid NOT NULL REFERENCES advisory_versions(id) ON DELETE RESTRICT,
  approver_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  role        text NOT NULL,
  approved_at timestamptz NOT NULL DEFAULT now(),
  notes       text,
  created_at  timestamptz NOT NULL DEFAULT now(),
  is_demo     boolean NOT NULL DEFAULT false,
  CONSTRAINT uq_advisory_approvals UNIQUE (version_id, approver_id),
  CONSTRAINT ck_advisory_approvals_role CHECK (role IN ('agronomist', 'pathologist'))
);

ALTER TABLE advisories
  ADD CONSTRAINT fk_advisories_current_version
  FOREIGN KEY (current_version_id) REFERENCES advisory_versions(id)
  ON DELETE RESTRICT;

CREATE TABLE alert_policies (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  geo_code       text NOT NULL,
  target_code    text NOT NULL,
  min_band       text NOT NULL,
  min_coverage   text NOT NULL,
  cooldown_hours integer NOT NULL,
  channels       jsonb NOT NULL DEFAULT '[]'::jsonb,
  approved_by    uuid REFERENCES users(id) ON DELETE RESTRICT,
  active         boolean NOT NULL DEFAULT false,
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now(),
  is_demo        boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_alert_policies_band CHECK (min_band IN ('low', 'moderate', 'high', 'urgent')),
  CONSTRAINT ck_alert_policies_coverage CHECK (min_coverage IN ('good', 'partial', 'low', 'unknown')),
  CONSTRAINT ck_alert_policies_cooldown CHECK (cooldown_hours >= 0),
  CONSTRAINT ck_alert_policies_channels CHECK (jsonb_typeof(channels) = 'array')
);

CREATE TABLE alerts (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  forecast_id     uuid NOT NULL REFERENCES forecasts(id) ON DELETE RESTRICT,
  geo_code        text NOT NULL,
  target_code     text NOT NULL,
  band            text NOT NULL,
  window_from     timestamptz NOT NULL,
  window_to       timestamptz NOT NULL,
  message_version text NOT NULL,
  dedupe_key      text NOT NULL UNIQUE,
  created_at      timestamptz NOT NULL DEFAULT now(),
  is_demo         boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_alerts_band CHECK (band IN ('low', 'moderate', 'high', 'urgent')),
  CONSTRAINT ck_alerts_window CHECK (window_to > window_from)
);

CREATE TABLE alert_deliveries (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  alert_id     uuid NOT NULL REFERENCES alerts(id) ON DELETE RESTRICT,
  user_id      uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  channel      text NOT NULL,
  status       text NOT NULL DEFAULT 'queued',
  provider_ref text,
  sent_at      timestamptz,
  delivered_at timestamptz,
  error        text,
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now(),
  is_demo      boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_alert_deliveries_channel CHECK (channel IN ('sms', 'whatsapp', 'push', 'ivr')),
  CONSTRAINT ck_alert_deliveries_status CHECK (status IN (
    'queued', 'sent', 'delivered', 'failed', 'suppressed', 'opted_out'
  ))
);

-- =============================================================================
-- 7. Registry, audit and exports
-- =============================================================================

CREATE TABLE model_registry (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kind        text NOT NULL,
  version     text NOT NULL,
  artefact_key text NOT NULL,
  checksum    text NOT NULL,
  metrics     jsonb NOT NULL DEFAULT '{}'::jsonb,
  status      text NOT NULL DEFAULT 'draft',
  approved_by uuid REFERENCES users(id) ON DELETE RESTRICT,
  approved_at timestamptz,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  is_demo     boolean NOT NULL DEFAULT false,
  CONSTRAINT uq_model_registry_kind_version UNIQUE (kind, version),
  CONSTRAINT ck_model_registry_kind CHECK (kind IN (
    'image_gate', 'image_classifier', 'forecast'
  )),
  CONSTRAINT ck_model_registry_status CHECK (status IN (
    'draft', 'validated', 'approved', 'retired'
  )),
  CONSTRAINT ck_model_registry_approved CHECK (
    status <> 'approved' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)
  )
);

COMMENT ON TABLE model_registry IS
  'Serving requires status = approved. Artefacts are checksummed and backed up with the database.';

CREATE TABLE audit_events (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id    uuid REFERENCES users(id) ON DELETE RESTRICT,
  actor_role  text,
  action      text NOT NULL,
  entity_type text NOT NULL,
  entity_id   text NOT NULL,
  reason      text,
  request_id  text,
  ip_hash     text,
  created_at  timestamptz NOT NULL DEFAULT now(),
  is_demo     boolean NOT NULL DEFAULT false
);

COMMENT ON TABLE audit_events IS
  'Append-only. No PII payloads: store identifiers and reason codes, never message bodies, phone numbers or coordinates.';

CREATE TABLE export_jobs (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  requested_by uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  purpose      text NOT NULL,
  filters      jsonb NOT NULL DEFAULT '{}'::jsonb,
  status       text NOT NULL DEFAULT 'queued',
  row_count    integer,
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now(),
  is_demo      boolean NOT NULL DEFAULT false,
  CONSTRAINT ck_export_jobs_status CHECK (status IN (
    'queued', 'running', 'complete', 'failed', 'expired'
  )),
  CONSTRAINT ck_export_jobs_row_count CHECK (row_count IS NULL OR row_count >= 0),
  CONSTRAINT ck_export_jobs_purpose CHECK (length(purpose) > 0)
);

-- =============================================================================
-- 8. Append-only guards
-- =============================================================================

CREATE TRIGGER trg_image_predictions_immutable
  BEFORE UPDATE OR DELETE ON image_predictions
  FOR EACH ROW EXECUTE FUNCTION reject_mutation();

CREATE TRIGGER trg_image_quality_results_immutable
  BEFORE UPDATE OR DELETE ON image_quality_results
  FOR EACH ROW EXECUTE FUNCTION reject_mutation();

CREATE TRIGGER trg_reviews_immutable
  BEFORE UPDATE OR DELETE ON reviews
  FOR EACH ROW EXECUTE FUNCTION reject_mutation();

CREATE TRIGGER trg_review_evidence_immutable
  BEFORE UPDATE OR DELETE ON review_evidence
  FOR EACH ROW EXECUTE FUNCTION reject_mutation();

CREATE TRIGGER trg_labels_immutable
  BEFORE UPDATE OR DELETE ON labels
  FOR EACH ROW EXECUTE FUNCTION labels_guard_mutation();

CREATE TRIGGER trg_review_events_immutable
  BEFORE UPDATE OR DELETE ON review_events
  FOR EACH ROW EXECUTE FUNCTION reject_mutation();

CREATE TRIGGER trg_consents_immutable
  BEFORE UPDATE OR DELETE ON consents
  FOR EACH ROW EXECUTE FUNCTION reject_mutation();

CREATE TRIGGER trg_feature_snapshots_immutable
  BEFORE UPDATE OR DELETE ON feature_snapshots
  FOR EACH ROW EXECUTE FUNCTION reject_mutation();

CREATE TRIGGER trg_forecasts_immutable
  BEFORE UPDATE OR DELETE ON forecasts
  FOR EACH ROW EXECUTE FUNCTION reject_mutation();

CREATE TRIGGER trg_historical_occurrences_immutable
  BEFORE UPDATE OR DELETE ON historical_occurrences
  FOR EACH ROW EXECUTE FUNCTION reject_mutation();

CREATE TRIGGER trg_advisory_versions_immutable
  BEFORE UPDATE OR DELETE ON advisory_versions
  FOR EACH ROW EXECUTE FUNCTION reject_mutation();

CREATE TRIGGER trg_advisory_approvals_immutable
  BEFORE UPDATE OR DELETE ON advisory_approvals
  FOR EACH ROW EXECUTE FUNCTION reject_mutation();

CREATE TRIGGER trg_audit_events_immutable
  BEFORE UPDATE OR DELETE ON audit_events
  FOR EACH ROW EXECUTE FUNCTION reject_mutation();

-- updated_at maintenance
CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_geographies_updated_at BEFORE UPDATE ON geographies
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_crops_updated_at BEFORE UPDATE ON crops
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_targets_updated_at BEFORE UPDATE ON targets
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_crop_calendars_updated_at BEFORE UPDATE ON crop_calendars
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_growing_areas_updated_at BEFORE UPDATE ON growing_areas
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_crop_cycles_updated_at BEFORE UPDATE ON crop_cycles
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_observations_updated_at BEFORE UPDATE ON observations
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_observation_verification_updated_at BEFORE UPDATE ON observation_verification
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_review_requests_updated_at BEFORE UPDATE ON review_requests
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sentinel_sites_updated_at BEFORE UPDATE ON sentinel_sites
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_advisories_updated_at BEFORE UPDATE ON advisories
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_alert_policies_updated_at BEFORE UPDATE ON alert_policies
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_alert_deliveries_updated_at BEFORE UPDATE ON alert_deliveries
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_model_registry_updated_at BEFORE UPDATE ON model_registry
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_export_jobs_updated_at BEFORE UPDATE ON export_jobs
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================================
-- 9. Indexing baseline (05-data-layer.md §7)
-- =============================================================================

CREATE INDEX ix_users_phone ON users (phone_e164);
CREATE INDEX ix_users_email ON users (email);
CREATE INDEX ix_user_roles_user ON user_roles (user_id);
CREATE INDEX ix_user_roles_role ON user_roles (role_code);
CREATE INDEX ix_user_roles_granted_by ON user_roles (granted_by);
CREATE INDEX ix_devices_user ON devices (user_id);
CREATE INDEX ix_consents_user_type_created ON consents (user_id, type, created_at DESC);
CREATE INDEX ix_user_area_user ON user_area_assignments (user_id, geo_code);
CREATE INDEX ix_sessions_user ON sessions (user_id);
CREATE INDEX ix_sessions_family ON sessions (family_id);

CREATE INDEX ix_geographies_code ON geographies (code);
CREATE INDEX ix_geographies_parent ON geographies (parent_code);
CREATE INDEX ix_geographies_geom ON geographies USING GIST (geom);
CREATE INDEX ix_targets_crop ON targets (crop_code);
CREATE INDEX ix_crop_calendars_crop_geo ON crop_calendars (crop_code, geo_code);
CREATE INDEX ix_growing_areas_owner ON growing_areas (owner_user_id);
CREATE INDEX ix_growing_areas_geo ON growing_areas (geo_code);
CREATE INDEX ix_growing_areas_geom ON growing_areas USING GIST (geom) WHERE geom IS NOT NULL;
CREATE INDEX ix_crop_cycles_area ON crop_cycles (growing_area_id);
CREATE INDEX ix_crop_cycles_crop ON crop_cycles (crop_code);

CREATE INDEX ix_observations_user_created ON observations (user_id, created_at DESC);
CREATE INDEX ix_observations_queue ON observations (geo_code, status, urgency_score DESC, created_at);
CREATE INDEX ix_observations_growing_area ON observations (growing_area_id);
CREATE INDEX ix_observations_crop ON observations (crop_code);
CREATE INDEX ix_observations_subject ON observations (subject_user_id);

CREATE INDEX ix_image_assets_observation ON image_assets (observation_id);
CREATE INDEX ix_image_assets_content_hash ON image_assets (content_hash);
CREATE INDEX ix_image_assets_created ON image_assets (created_at DESC);

CREATE INDEX ix_image_quality_image ON image_quality_results (image_id, created_at DESC);
CREATE INDEX ix_image_predictions_image ON image_predictions (image_id, generated_at DESC);
CREATE INDEX ix_image_predictions_model ON image_predictions (model_version);

CREATE INDEX ix_review_requests_observation ON review_requests (observation_id);
CREATE INDEX ix_review_requests_status ON review_requests (status);
CREATE INDEX ix_review_requests_requested_by ON review_requests (requested_by);

CREATE INDEX ix_reviews_observation ON reviews (observation_id, created_at DESC);
CREATE INDEX ix_reviews_reviewer ON reviews (reviewer_id);
CREATE INDEX ix_review_evidence_review ON review_evidence (review_id);
CREATE INDEX ix_labels_observation ON labels (observation_id, reviewed_at DESC);
CREATE INDEX ix_labels_image ON labels (image_id) WHERE image_id IS NOT NULL;
CREATE INDEX ix_labels_review ON labels (review_id);
CREATE INDEX ix_labels_target ON labels (target_code);
CREATE INDEX ix_labels_reviewer ON labels (reviewer_id);
CREATE INDEX ix_labels_supersedes ON labels (supersedes_label_id) WHERE supersedes_label_id IS NOT NULL;
CREATE UNIQUE INDEX uq_labels_active_image
  ON labels (image_id)
  WHERE label_status = 'active' AND image_id IS NOT NULL;
CREATE UNIQUE INDEX uq_labels_active_observation
  ON labels (observation_id)
  WHERE label_status = 'active' AND image_id IS NULL;
CREATE INDEX ix_review_events_observation ON review_events (observation_id, created_at DESC);
CREATE INDEX ix_review_events_actor ON review_events (actor_id);
CREATE INDEX ix_observation_verification_status ON observation_verification (status, verified_at DESC);
CREATE INDEX ix_observation_verification_review ON observation_verification (review_id);
CREATE INDEX ix_observation_verification_verified_by ON observation_verification (verified_by);
CREATE INDEX ix_review_assignments_user ON review_assignments (user_id);
CREATE INDEX ix_review_assignments_expiry ON review_assignments (expires_at);

CREATE INDEX ix_sentinel_sites_crop_geo ON sentinel_sites (crop_code, geo_code, panel_version);
CREATE INDEX ix_sentinel_sites_approved_by ON sentinel_sites (approved_by);
CREATE INDEX ix_sentinel_sites_geom ON sentinel_sites USING GIST (geom);
CREATE INDEX ix_sentinel_visits_site_date ON sentinel_visits (site_id, visit_date DESC);
CREATE INDEX ix_sentinel_visits_observer ON sentinel_visits (observer_id);
CREATE INDEX ix_sentinel_visits_target ON sentinel_visits (target_code);

CREATE INDEX ix_historical_occurrences_crop_target_geo ON historical_occurrences (
  crop_code, target_code, geo_code, event_date DESC
);
CREATE INDEX ix_historical_occurrences_dedupe ON historical_occurrences (dedupe_key);
CREATE INDEX ix_historical_occurrences_tier ON historical_occurrences (verification_tier);
CREATE INDEX ix_historical_occurrences_dates ON historical_occurrences (event_date, report_date);

CREATE INDEX ix_weather_geo_time ON weather_snapshots (geo_code, source_timestamp DESC);
CREATE INDEX ix_weather_spatial ON weather_snapshots (geo_code, boundary_version, spatial_matching_method);
CREATE INDEX ix_weather_fetched ON weather_snapshots (fetched_at DESC);
CREATE INDEX ix_feature_snapshots_lookup ON feature_snapshots (
  crop_code, target_code, geo_code, horizon_days, issue_time DESC
);
CREATE INDEX ix_forecasts_lookup ON forecasts (
  crop_code, target_code, geo_code, issue_time DESC
);
CREATE INDEX ix_forecasts_feature_snapshot ON forecasts (feature_snapshot_id);
CREATE INDEX ix_forecasts_model ON forecasts (model_version);
CREATE INDEX ix_forecast_runs_status ON forecast_runs (status, started_at DESC);

CREATE INDEX ix_advisories_crop_target ON advisories (crop_code, target_code, status);
CREATE INDEX ix_advisories_current_version ON advisories (current_version_id);
CREATE INDEX ix_advisory_versions_advisory ON advisory_versions (advisory_id, version DESC);
CREATE INDEX ix_advisory_versions_author ON advisory_versions (author_id);
CREATE INDEX ix_advisory_approvals_version ON advisory_approvals (version_id);
CREATE INDEX ix_advisory_approvals_approver ON advisory_approvals (approver_id);
CREATE INDEX ix_alert_policies_geo_target ON alert_policies (geo_code, target_code, active);
CREATE INDEX ix_alert_policies_approved_by ON alert_policies (approved_by);
CREATE INDEX ix_alerts_forecast ON alerts (forecast_id);
CREATE INDEX ix_alerts_geo_target_time ON alerts (geo_code, target_code, created_at DESC);
CREATE INDEX ix_alert_deliveries_alert ON alert_deliveries (alert_id, status);
CREATE INDEX ix_alert_deliveries_user ON alert_deliveries (user_id, created_at DESC);

CREATE INDEX ix_model_registry_kind_status ON model_registry (kind, status);
CREATE INDEX ix_model_registry_approved_by ON model_registry (approved_by);
CREATE INDEX ix_audit_events_entity ON audit_events (entity_type, entity_id, created_at DESC);
CREATE INDEX ix_audit_events_actor ON audit_events (actor_id, created_at DESC);
CREATE INDEX ix_export_jobs_requester ON export_jobs (requested_by, created_at DESC);

-- =============================================================================
-- 10. Forecast label eligibility (D7)
-- =============================================================================

-- Returns cases eligible as positive evidence at a given cutoff. The caller must
-- also enforce the spatial unit, supported target and event definition (D1/D5).
-- A probable case keeps its evidence tier as a lower-confidence flag.
CREATE OR REPLACE FUNCTION forecast_eligible_cases(p_cutoff timestamptz)
RETURNS TABLE (
  observation_id uuid,
  crop_code      text,
  target_code    text,
  geo_code       text,
  event_date     date,
  evidence_tier  text,
  verified_at    timestamptz
)
LANGUAGE sql
STABLE
AS $$
  SELECT
    o.id,
    o.crop_code,
    COALESCE(l.target_code, r.corrected_label) AS target_code,
    o.geo_code,
    o.event_date,
    ov.evidence_tier,
    ov.verified_at
  FROM observation_verification ov
  JOIN observations o ON o.id = ov.observation_id
  JOIN reviews r ON r.id = ov.review_id
  LEFT JOIN LATERAL (
    SELECT l.target_code
    FROM labels l
    WHERE l.review_id = r.id
      AND l.label_status IN ('active', 'adjudicated')
    ORDER BY l.reviewed_at DESC, l.created_at DESC
    LIMIT 1
  ) l ON true
  WHERE ov.status IN ('confirmed', 'probable')
    AND ov.verified_at IS NOT NULL
    AND ov.verified_at <= p_cutoff
    AND o.event_date IS NOT NULL
    AND o.event_date <= (p_cutoff AT TIME ZONE 'UTC')::date
    AND o.deleted_at IS NULL
    AND COALESCE(l.target_code, r.corrected_label) IS NOT NULL;
$$;

COMMENT ON FUNCTION forecast_eligible_cases(timestamptz) IS
  'D7 positive-evidence query. Unverified, needs_visit, duplicate, unresolved and rejected are excluded. Probable retains its tier. Event date is required; report/submitted date is never substituted. The active/adjudicated label record is preferred over the review snapshot when both exist.';

-- Candidate forecast negatives. The caller must still enforce the label window
-- and the D9 coverage gate per area/window; coverage_pass = true is required.
CREATE OR REPLACE VIEW v_sentinel_negative_candidates AS
SELECT
  sv.id            AS visit_id,
  sv.site_id,
  ss.crop_code,
  ss.geo_code,
  sv.target_code,
  sv.visit_date,
  sv.observer_id
FROM sentinel_visits sv
JOIN sentinel_sites ss ON ss.id = sv.site_id
JOIN targets t ON t.crop_code = ss.crop_code AND t.code = sv.target_code
WHERE sv.scheduled = true
  AND sv.observed = 'absent'
  AND sv.coverage_pass = true
  AND t.supported = true
  AND sv.visit_date >= ss.active_from
  AND (ss.active_to IS NULL OR sv.visit_date <= ss.active_to);

COMMENT ON VIEW v_sentinel_negative_candidates IS
  'D7 negative candidates only: scheduled, absent, coverage-passing, supported target, active panel. The caller must also enforce the label window. A missing visit is never a negative.';

-- Evaluates weather sufficiency for an administrative unit and boundary version.
-- Makes missing, stale or incomplete data explicit by returning is_sufficient = false and a typed reason.
-- Never silently imputes.
CREATE OR REPLACE FUNCTION check_weather_sufficiency(
  p_geo_code text,
  p_boundary_version text,
  p_cutoff_time timestamptz,
  p_max_staleness_hours integer DEFAULT 24,
  p_min_completeness numeric DEFAULT 0.80
) RETURNS TABLE (
  is_sufficient boolean,
  reason_code text,
  latest_snapshot_id uuid,
  source_timestamp timestamptz,
  age_hours numeric,
  completeness numeric,
  variables jsonb
) AS $$
DECLARE
  v_rec record;
  v_age_hrs numeric;
  v_has_temp boolean;
  v_has_rh boolean;
  v_has_rain boolean;
  v_has_wind boolean;
  v_has_wet_days boolean;
BEGIN
  SELECT ws.id, ws.source_timestamp, ws.fetched_at, ws.variables, ws.completeness, ws.is_stale, ws.boundary_version
  INTO v_rec
  FROM weather_snapshots ws
  WHERE ws.geo_code = p_geo_code
    AND ws.source_timestamp <= p_cutoff_time
  ORDER BY ws.source_timestamp DESC
  LIMIT 1;

  IF NOT FOUND THEN
    RETURN QUERY SELECT false, 'weather_missing'::text, NULL::uuid, NULL::timestamptz, NULL::numeric, 0.0::numeric, NULL::jsonb;
    RETURN;
  END IF;

  v_age_hrs := ROUND((EXTRACT(EPOCH FROM (p_cutoff_time - v_rec.source_timestamp)) / 3600.0)::numeric, 2);

  IF v_rec.boundary_version <> p_boundary_version THEN
    RETURN QUERY SELECT false, 'boundary_mismatch'::text, v_rec.id, v_rec.source_timestamp, v_age_hrs, COALESCE(v_rec.completeness, 0.0), v_rec.variables;
    RETURN;
  END IF;

  IF v_rec.is_stale OR v_age_hrs > p_max_staleness_hours THEN
    RETURN QUERY SELECT false, 'weather_stale'::text, v_rec.id, v_rec.source_timestamp, v_age_hrs, COALESCE(v_rec.completeness, 0.0), v_rec.variables;
    RETURN;
  END IF;

  IF v_rec.completeness IS NOT NULL AND v_rec.completeness < p_min_completeness THEN
    RETURN QUERY SELECT false, 'weather_incomplete'::text, v_rec.id, v_rec.source_timestamp, v_age_hrs, v_rec.completeness, v_rec.variables;
    RETURN;
  END IF;

  -- Verify core required variables exist in jsonb payload:
  -- temperature, relative humidity, rainfall, wet_day_runs, wind
  v_has_temp := (v_rec.variables ? 'temperature_min_c' OR v_rec.variables ? 'temperature_mean_c' OR v_rec.variables ? 'temperature_c');
  v_has_rh := (v_rec.variables ? 'relative_humidity_max_pct' OR v_rec.variables ? 'relative_humidity_mean_pct' OR v_rec.variables ? 'relative_humidity_pct');
  v_has_rain := (v_rec.variables ? 'rainfall_mm');
  v_has_wind := (v_rec.variables ? 'wind_speed_ms' OR v_rec.variables ? 'wind_speed_kmh');
  v_has_wet_days := (v_rec.variables ? 'wet_day_runs' OR v_rec.variables ? 'wet_hours');

  IF NOT (v_has_temp AND v_has_rh AND v_has_rain AND v_has_wind AND v_has_wet_days) THEN
    RETURN QUERY SELECT false, 'weather_incomplete'::text, v_rec.id, v_rec.source_timestamp, v_age_hrs, COALESCE(v_rec.completeness, 0.0), v_rec.variables;
    RETURN;
  END IF;

  RETURN QUERY SELECT true, 'sufficient'::text, v_rec.id, v_rec.source_timestamp, v_age_hrs, COALESCE(v_rec.completeness, 1.0), v_rec.variables;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION check_weather_sufficiency IS
  'Evaluates whether recent weather data is sufficient to score a forecast. Rejects missing, stale, boundary-mismatched or incomplete data with typed reasons; never silently imputes.';

-- =============================================================================
-- 11. Demo visibility
-- =============================================================================

-- Production queries must exclude is_demo = true. This view is a convenience for
-- admin/demo tooling only; it is not used by farmer-facing endpoints.
CREATE OR REPLACE VIEW v_demo_rows AS
SELECT 'users'::text AS entity_type, id::text AS entity_id FROM users WHERE is_demo
UNION ALL SELECT 'consents', id::text FROM consents WHERE is_demo
UNION ALL SELECT 'geographies', id::text FROM geographies WHERE is_demo
UNION ALL SELECT 'crops', code::text FROM crops WHERE is_demo
UNION ALL SELECT 'targets', id::text FROM targets WHERE is_demo
UNION ALL SELECT 'crop_calendars', id::text FROM crop_calendars WHERE is_demo
UNION ALL SELECT 'growing_areas', id::text FROM growing_areas WHERE is_demo
UNION ALL SELECT 'crop_cycles', id::text FROM crop_cycles WHERE is_demo
UNION ALL SELECT 'observations', id::text FROM observations WHERE is_demo
UNION ALL SELECT 'image_assets', id::text FROM image_assets WHERE is_demo
UNION ALL SELECT 'image_quality_results', id::text FROM image_quality_results WHERE is_demo
UNION ALL SELECT 'image_predictions', id::text FROM image_predictions WHERE is_demo
UNION ALL SELECT 'reviews', id::text FROM reviews WHERE is_demo
UNION ALL SELECT 'review_evidence', id::text FROM review_evidence WHERE is_demo
UNION ALL SELECT 'labels', id::text FROM labels WHERE is_demo
UNION ALL SELECT 'review_events', id::text FROM review_events WHERE is_demo
UNION ALL SELECT 'sentinel_sites', id::text FROM sentinel_sites WHERE is_demo
UNION ALL SELECT 'sentinel_visits', id::text FROM sentinel_visits WHERE is_demo
UNION ALL SELECT 'historical_occurrences', id::text FROM historical_occurrences WHERE is_demo
UNION ALL SELECT 'weather_snapshots', id::text FROM weather_snapshots WHERE is_demo
UNION ALL SELECT 'feature_snapshots', id::text FROM feature_snapshots WHERE is_demo
UNION ALL SELECT 'forecasts', id::text FROM forecasts WHERE is_demo
UNION ALL SELECT 'forecast_runs', id::text FROM forecast_runs WHERE is_demo
UNION ALL SELECT 'advisories', id::text FROM advisories WHERE is_demo
UNION ALL SELECT 'advisory_versions', id::text FROM advisory_versions WHERE is_demo
UNION ALL SELECT 'advisory_approvals', id::text FROM advisory_approvals WHERE is_demo
UNION ALL SELECT 'alert_policies', id::text FROM alert_policies WHERE is_demo
UNION ALL SELECT 'alerts', id::text FROM alerts WHERE is_demo
UNION ALL SELECT 'alert_deliveries', id::text FROM alert_deliveries WHERE is_demo
UNION ALL SELECT 'model_registry', id::text FROM model_registry WHERE is_demo
UNION ALL SELECT 'audit_events', id::text FROM audit_events WHERE is_demo
UNION ALL SELECT 'export_jobs', id::text FROM export_jobs WHERE is_demo;

COMMENT ON VIEW v_demo_rows IS
  'Inventory of demo rows for reset/audit tooling. Production endpoints must filter is_demo = false by default.';

-- =============================================================================
-- 12. Reference data (no crop/target rows until D1)
-- =============================================================================

INSERT INTO roles (code, description) VALUES
  ('farmer', 'Field user who submits reports and reads advisories'),
  ('extension_worker', 'Verifies reports, captures on behalf, records sentinel visits'),
  ('pathologist', 'Escalation reviewer, taxonomy owner, sole role that can confirm'),
  ('agronomist', 'Advisory and risk-band approval; cannot verify or correct labels'),
  ('admin', 'Configuration, users, queue rules; cannot verify')
ON CONFLICT (code) DO NOTHING;

-- crops and targets are intentionally empty: D1 is unresolved. Seeding a crop
-- or target here would fabricate the project's core scientific decision.
