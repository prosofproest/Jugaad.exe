-- =============================================================================
-- CropSentinel AI — Master Database Architecture Schema
-- Authority: CropSentinel AI Master Database Specification
-- Engine: PostgreSQL 16+ with PostGIS 3.x and pgvector
-- Covers: 11 Domains, 76 Normalized Relational Tables
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
DO $$
BEGIN
  CREATE EXTENSION IF NOT EXISTS vector;
EXCEPTION
  WHEN OTHERS THEN
    RAISE NOTICE 'pgvector extension not installed in environment; skipping vector extension creation';
END $$;

-- -----------------------------------------------------------------------------
-- Helper Functions & Triggers
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
  RAISE EXCEPTION 'Table % is strictly append-only; % is not permitted', TG_TABLE_NAME, TG_OP
    USING ERRCODE = 'restrict_violation';
END;
$$;

-- =============================================================================
-- 1. USER DATABASE
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username      VARCHAR(64) UNIQUE,
  email         VARCHAR(320) UNIQUE,
  phone_e164    VARCHAR(20) UNIQUE,
  password_hash VARCHAR(255),
  status        VARCHAR(20) NOT NULL DEFAULT 'active',
  is_demo       BOOLEAN NOT NULL DEFAULT false,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at    TIMESTAMPTZ,
  CONSTRAINT chk_users_status CHECK (status IN ('active', 'inactive', 'suspended', 'pending_verification')),
  CONSTRAINT chk_users_contact_present CHECK (email IS NOT NULL OR phone_e164 IS NOT NULL)
);

CREATE TRIGGER trg_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS user_roles (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role          VARCHAR(50) NOT NULL,
  is_active     BOOLEAN NOT NULL DEFAULT true,
  granted_by    UUID REFERENCES users(id) ON DELETE SET NULL,
  granted_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_user_roles_user_role UNIQUE (user_id, role),
  CONSTRAINT chk_user_roles_valid CHECK (role IN ('farmer', 'expert', 'agent', 'admin', 'pathologist', 'agronomist', 'extension_worker', 'researcher'))
);

CREATE TABLE IF NOT EXISTS user_profiles (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                  UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  first_name               VARCHAR(100),
  last_name                VARCHAR(100),
  avatar_url               VARCHAR(500),
  bio                      TEXT,
  address                  TEXT,
  preferred_contact_method VARCHAR(20) NOT NULL DEFAULT 'phone',
  created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_user_profiles_contact_method CHECK (preferred_contact_method IN ('phone', 'sms', 'email', 'in_app'))
);

CREATE TRIGGER trg_user_profiles_updated_at
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS user_permissions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  permission_code VARCHAR(100) NOT NULL,
  scope           VARCHAR(100) NOT NULL DEFAULT 'global',
  granted_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at      TIMESTAMPTZ,
  CONSTRAINT uq_user_permission_scope UNIQUE (user_id, permission_code, scope)
);

CREATE TABLE IF NOT EXISTS user_sessions (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_token_hash VARCHAR(255) NOT NULL UNIQUE,
  ip_address         VARCHAR(45),
  user_agent         TEXT,
  device_id          VARCHAR(100),
  expires_at         TIMESTAMPTZ NOT NULL,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  revoked_at         TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS user_preferences (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  preferred_language     VARCHAR(10) NOT NULL DEFAULT 'en',
  timezone               VARCHAR(50) NOT NULL DEFAULT 'Asia/Kolkata',
  theme                  VARCHAR(20) NOT NULL DEFAULT 'system',
  notification_frequency VARCHAR(20) NOT NULL DEFAULT 'instant',
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_user_preferences_notif_freq CHECK (notification_frequency IN ('instant', 'daily_digest', 'weekly', 'muted'))
);

CREATE TRIGGER trg_user_preferences_updated_at
  BEFORE UPDATE ON user_preferences
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================================
-- 2. FARM DATABASE
-- =============================================================================

CREATE TABLE IF NOT EXISTS farms (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name                VARCHAR(200) NOT NULL,
  registration_number VARCHAR(100) UNIQUE,
  total_area_sqm      DOUBLE PRECISION,
  owner_id            UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  status              VARCHAR(20) NOT NULL DEFAULT 'active',
  is_demo             BOOLEAN NOT NULL DEFAULT false,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at          TIMESTAMPTZ,
  CONSTRAINT chk_farms_status CHECK (status IN ('active', 'inactive', 'archived')),
  CONSTRAINT chk_farms_positive_area CHECK (total_area_sqm IS NULL OR total_area_sqm > 0)
);

CREATE TRIGGER trg_farms_updated_at
  BEFORE UPDATE ON farms
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS farm_boundaries (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farm_id          UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
  boundary_polygon geometry(MultiPolygon, 4326) NOT NULL,
  perimeter_meters DOUBLE PRECISION,
  area_sqm         DOUBLE PRECISION,
  elevation_meters DOUBLE PRECISION,
  is_active        BOOLEAN NOT NULL DEFAULT true,
  recorded_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS farm_sections (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farm_id         UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
  section_code    VARCHAR(50) NOT NULL,
  name            VARCHAR(100) NOT NULL,
  description     TEXT,
  section_polygon geometry(Polygon, 4326),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_farm_section_code UNIQUE (farm_id, section_code)
);

CREATE TRIGGER trg_farm_sections_updated_at
  BEFORE UPDATE ON farm_sections
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS farm_plots (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farm_id           UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
  section_id        UUID REFERENCES farm_sections(id) ON DELETE SET NULL,
  plot_code         VARCHAR(50) NOT NULL,
  soil_type         VARCHAR(50),
  irrigation_source VARCHAR(50),
  area_sqm          DOUBLE PRECISION,
  plot_polygon      geometry(Polygon, 4326),
  is_active         BOOLEAN NOT NULL DEFAULT true,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_farm_plot_code UNIQUE (farm_id, plot_code),
  CONSTRAINT chk_farm_plots_positive_area CHECK (area_sqm IS NULL OR area_sqm > 0)
);

CREATE TRIGGER trg_farm_plots_updated_at
  BEFORE UPDATE ON farm_plots
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS farm_locations (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farm_id              UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
  address_line         VARCHAR(255),
  village_or_town      VARCHAR(100),
  taluk_or_subdistrict VARCHAR(100),
  district             VARCHAR(100) NOT NULL,
  state                VARCHAR(100) NOT NULL,
  country              VARCHAR(100) NOT NULL DEFAULT 'India',
  postal_code          VARCHAR(20),
  centroid             geometry(Point, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS farm_members (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farm_id      UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
  user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  access_level VARCHAR(30) NOT NULL DEFAULT 'viewer',
  is_active    BOOLEAN NOT NULL DEFAULT true,
  joined_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_farm_members_farm_user UNIQUE (farm_id, user_id),
  CONSTRAINT chk_farm_members_access_level CHECK (access_level IN ('owner', 'manager', 'agronomist', 'worker', 'viewer'))
);

-- =============================================================================
-- 3. CROP AND PLANT DATABASE
-- =============================================================================

CREATE TABLE IF NOT EXISTS crop_groups (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code        VARCHAR(50) NOT NULL UNIQUE,
  name        VARCHAR(100) NOT NULL,
  description TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_crop_groups_updated_at
  BEFORE UPDATE ON crop_groups
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS crop_types (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  group_id            UUID REFERENCES crop_groups(id) ON DELETE SET NULL,
  code                VARCHAR(50) NOT NULL UNIQUE,
  common_name         VARCHAR(100) NOT NULL,
  botanical_name      VARCHAR(150) NOT NULL,
  description         TEXT,
  optimal_temp_min_c  DOUBLE PRECISION,
  optimal_temp_max_c  DOUBLE PRECISION,
  optimal_rainfall_mm DOUBLE PRECISION,
  is_active           BOOLEAN NOT NULL DEFAULT true,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_crop_types_updated_at
  BEFORE UPDATE ON crop_types
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS crop_growth_stages (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_type_id            UUID NOT NULL REFERENCES crop_types(id) ON DELETE CASCADE,
  stage_name              VARCHAR(50) NOT NULL,
  stage_order             INTEGER NOT NULL,
  typical_duration_days   INTEGER NOT NULL,
  water_requirement_level VARCHAR(20) NOT NULL DEFAULT 'medium',
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_crop_stage_order UNIQUE (crop_type_id, stage_order),
  CONSTRAINT uq_crop_stage_name UNIQUE (crop_type_id, stage_name),
  CONSTRAINT chk_crop_stage_duration CHECK (typical_duration_days > 0),
  CONSTRAINT chk_crop_stage_water_req CHECK (water_requirement_level IN ('low', 'medium', 'high', 'critical'))
);

CREATE TABLE IF NOT EXISTS crop_instances (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plot_id               UUID NOT NULL REFERENCES farm_plots(id) ON DELETE CASCADE,
  crop_type_id          UUID NOT NULL REFERENCES crop_types(id) ON DELETE RESTRICT,
  variety               VARCHAR(100) NOT NULL,
  season                VARCHAR(30) NOT NULL,
  planting_date         DATE NOT NULL,
  expected_harvest_date DATE,
  actual_harvest_date   DATE,
  status                VARCHAR(30) NOT NULL DEFAULT 'active',
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_crop_instance_status CHECK (status IN ('planned', 'active', 'harvested', 'failed', 'rotated')),
  CONSTRAINT chk_crop_instance_season CHECK (season IN ('kharif', 'rabi', 'zaid', 'summer', 'perennial'))
);

CREATE TRIGGER trg_crop_instances_updated_at
  BEFORE UPDATE ON crop_instances
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS plants (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_instance_id UUID NOT NULL REFERENCES crop_instances(id) ON DELETE CASCADE,
  tag_or_id        VARCHAR(50) NOT NULL,
  row_number       INTEGER,
  column_number    INTEGER,
  plant_location   geometry(Point, 4326),
  health_status    VARCHAR(30) NOT NULL DEFAULT 'healthy',
  planted_at       DATE,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_plant_crop_instance_tag UNIQUE (crop_instance_id, tag_or_id),
  CONSTRAINT chk_plants_health_status CHECK (health_status IN ('healthy', 'stressed', 'infested', 'diseased', 'deceased', 'recovered'))
);

CREATE TRIGGER trg_plants_updated_at
  BEFORE UPDATE ON plants
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS plant_observations (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plant_id           UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
  observer_id        UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  observation_date   TIMESTAMPTZ NOT NULL DEFAULT now(),
  visual_symptoms    TEXT,
  vigor_score        INTEGER,
  foliage_damage_pct DOUBLE PRECISION,
  observation_notes  TEXT,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_plant_obs_vigor CHECK (vigor_score IS NULL OR (vigor_score >= 1 AND vigor_score <= 10)),
  CONSTRAINT chk_plant_obs_damage_pct CHECK (foliage_damage_pct IS NULL OR (foliage_damage_pct >= 0 AND foliage_damage_pct <= 100))
);

CREATE TABLE IF NOT EXISTS planting_records (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_instance_id         UUID NOT NULL REFERENCES crop_instances(id) ON DELETE CASCADE,
  seed_lot_number          VARCHAR(100),
  seed_source              VARCHAR(200),
  sowing_method            VARCHAR(50) NOT NULL DEFAULT 'direct_seeding',
  planting_density_per_sqm DOUBLE PRECISION,
  fertilization_notes      TEXT,
  recorded_by              UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  recorded_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_planting_record_sowing_method CHECK (sowing_method IN ('direct_seeding', 'transplanting', 'broadcasting', 'dibbling', 'drilling'))
);

-- =============================================================================
-- 4. MEDIA DATABASE (Strictly Metadata and Storage References - NO BLOBs)
-- =============================================================================

CREATE TABLE IF NOT EXISTS media_files (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  uploader_id       UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  storage_provider  VARCHAR(50) NOT NULL DEFAULT 's3',
  bucket_name       VARCHAR(100) NOT NULL,
  object_key        VARCHAR(500) NOT NULL UNIQUE,
  file_name         VARCHAR(255) NOT NULL,
  file_size_bytes   INTEGER NOT NULL,
  mime_type         VARCHAR(100) NOT NULL,
  file_hash_sha256  VARCHAR(64) NOT NULL,
  media_type        VARCHAR(20) NOT NULL,
  duration_seconds  DOUBLE PRECISION,
  width_px          INTEGER,
  height_px         INTEGER,
  capture_timestamp TIMESTAMPTZ NOT NULL,
  upload_timestamp  TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_quarantined    BOOLEAN NOT NULL DEFAULT false,
  quarantine_reason VARCHAR(255),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_media_files_media_type CHECK (media_type IN ('image', 'video')),
  CONSTRAINT chk_media_files_positive_size CHECK (file_size_bytes > 0),
  CONSTRAINT chk_media_files_mime_type CHECK (mime_type IN ('image/jpeg', 'image/png', 'image/webp', 'video/mp4', 'video/quicktime'))
);

CREATE TRIGGER trg_media_files_updated_at
  BEFORE UPDATE ON media_files
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS media_frames (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  media_file_id       UUID NOT NULL REFERENCES media_files(id) ON DELETE CASCADE,
  frame_number        INTEGER NOT NULL,
  timestamp_offset_ms INTEGER NOT NULL,
  frame_object_key    VARCHAR(500) NOT NULL UNIQUE,
  width_px            INTEGER,
  height_px           INTEGER,
  quality_score       DOUBLE PRECISION,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_media_frames_file_num UNIQUE (media_file_id, frame_number),
  CONSTRAINT chk_media_frames_num_nonneg CHECK (frame_number >= 0),
  CONSTRAINT chk_media_frames_quality CHECK (quality_score IS NULL OR (quality_score >= 0.0 AND quality_score <= 1.0))
);

CREATE TABLE IF NOT EXISTS media_observations (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  media_file_id  UUID NOT NULL REFERENCES media_files(id) ON DELETE CASCADE,
  observation_id UUID NOT NULL REFERENCES plant_observations(id) ON DELETE CASCADE,
  media_role     VARCHAR(50) NOT NULL DEFAULT 'symptom_closeup',
  attached_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_media_obs_pair UNIQUE (media_file_id, observation_id),
  CONSTRAINT chk_media_obs_role CHECK (media_role IN ('primary', 'symptom_closeup', 'whole_plant', 'field_overview', 'underside_leaf', 'stem_cross_section'))
);

CREATE TABLE IF NOT EXISTS media_locations (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  media_file_id        UUID NOT NULL UNIQUE REFERENCES media_files(id) ON DELETE CASCADE,
  location             geometry(Point, 4326) NOT NULL,
  altitude_meters      DOUBLE PRECISION,
  gps_accuracy_meters  DOUBLE PRECISION,
  heading_degrees      DOUBLE PRECISION,
  captured_at          TIMESTAMPTZ NOT NULL
);

-- ai_analysis will be referenced by media_analysis_links (declared below Domain 6)

-- =============================================================================
-- 5. PEST AND DISEASE DATABASE
-- =============================================================================

CREATE TABLE IF NOT EXISTS pest_categories (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code        VARCHAR(50) NOT NULL UNIQUE,
  name        VARCHAR(100) NOT NULL,
  description TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_pest_categories_updated_at
  BEFORE UPDATE ON pest_categories
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS pests (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pest_category_id    UUID NOT NULL REFERENCES pest_categories(id) ON DELETE RESTRICT,
  common_name         VARCHAR(150) NOT NULL,
  scientific_name     VARCHAR(200) NOT NULL UNIQUE,
  description         TEXT,
  identification_guide TEXT,
  economic_threshold  TEXT,
  quarantine_status   VARCHAR(30) NOT NULL DEFAULT 'non_quarantine',
  is_active           BOOLEAN NOT NULL DEFAULT true,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_pests_quarantine_status CHECK (quarantine_status IN ('non_quarantine', 'regulated_non_quarantine', 'quarantine_pest', 'priority_pest'))
);

CREATE TRIGGER trg_pests_updated_at
  BEFORE UPDATE ON pests
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS pest_life_cycles (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pest_id                  UUID NOT NULL REFERENCES pests(id) ON DELETE CASCADE,
  stage_name               VARCHAR(50) NOT NULL,
  stage_duration_days_min  INTEGER NOT NULL,
  stage_duration_days_max  INTEGER NOT NULL,
  damaging_stage           BOOLEAN NOT NULL DEFAULT true,
  favorable_temperature_min DOUBLE PRECISION,
  favorable_temperature_max DOUBLE PRECISION,
  favorable_humidity_min   DOUBLE PRECISION,
  created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_pest_lifecycle_stage UNIQUE (pest_id, stage_name),
  CONSTRAINT chk_pest_stage_dur_min CHECK (stage_duration_days_min >= 0),
  CONSTRAINT chk_pest_stage_dur_max CHECK (stage_duration_days_max >= stage_duration_days_min)
);

CREATE TABLE IF NOT EXISTS pest_host_crops (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pest_id                UUID NOT NULL REFERENCES pests(id) ON DELETE CASCADE,
  crop_type_id           UUID NOT NULL REFERENCES crop_types(id) ON DELETE CASCADE,
  susceptibility_level   VARCHAR(30) NOT NULL DEFAULT 'primary',
  damage_severity_rating INTEGER,
  notes                  TEXT,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_pest_host_crops_pair UNIQUE (pest_id, crop_type_id),
  CONSTRAINT chk_pest_host_susceptibility CHECK (susceptibility_level IN ('primary', 'secondary', 'accidental', 'resistant')),
  CONSTRAINT chk_pest_host_severity_rating CHECK (damage_severity_rating IS NULL OR (damage_severity_rating >= 1 AND damage_severity_rating <= 5))
);

CREATE TABLE IF NOT EXISTS diseases (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  common_name          VARCHAR(150) NOT NULL,
  scientific_name      VARCHAR(200) NOT NULL UNIQUE,
  pathogen_type        VARCHAR(50) NOT NULL,
  vector_pest_id       UUID REFERENCES pests(id) ON DELETE SET NULL,
  description          TEXT,
  favorable_conditions TEXT,
  economic_impact      TEXT,
  is_active            BOOLEAN NOT NULL DEFAULT true,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_diseases_pathogen_type CHECK (pathogen_type IN ('fungal', 'bacterial', 'viral', 'viroid', 'phytoplasma', 'oomycete', 'nematode', 'abiotic'))
);

CREATE TRIGGER trg_diseases_updated_at
  BEFORE UPDATE ON diseases
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS disease_symptoms (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  disease_id          UUID NOT NULL REFERENCES diseases(id) ON DELETE CASCADE,
  affected_plant_part VARCHAR(50) NOT NULL,
  symptom_description TEXT NOT NULL,
  severity_scale      VARCHAR(20) NOT NULL DEFAULT 'moderate',
  is_primary_symptom  BOOLEAN NOT NULL DEFAULT true,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_disease_symptoms_plant_part CHECK (affected_plant_part IN ('leaf', 'stem', 'root', 'fruit', 'flower', 'crown', 'whole_plant', 'vascular_system'))
);

CREATE TABLE IF NOT EXISTS crop_symptoms (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  crop_type_id              UUID NOT NULL REFERENCES crop_types(id) ON DELETE CASCADE,
  disease_id                UUID REFERENCES diseases(id) ON DELETE CASCADE,
  pest_id                   UUID REFERENCES pests(id) ON DELETE CASCADE,
  symptom_name              VARCHAR(150) NOT NULL,
  characteristic_appearance TEXT NOT NULL,
  typical_growth_stage      VARCHAR(50),
  visual_diagnostic_rules   TEXT,
  created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_crop_symptoms_agent_present CHECK (disease_id IS NOT NULL OR pest_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS pest_damage_records (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pest_id                  UUID NOT NULL REFERENCES pests(id) ON DELETE CASCADE,
  plant_observation_id     UUID REFERENCES plant_observations(id) ON DELETE SET NULL,
  damage_type              VARCHAR(50) NOT NULL,
  affected_area_percentage DOUBLE PRECISION,
  severity_index           INTEGER NOT NULL,
  recorded_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_pest_damage_type CHECK (damage_type IN ('defoliation', 'stem_boring', 'leaf_curling', 'fruit_piercing', 'root_galling', 'sap_depletion', 'gall_formation')),
  CONSTRAINT chk_pest_damage_severity_idx CHECK (severity_index >= 1 AND severity_index <= 5),
  CONSTRAINT chk_pest_damage_pct_bounds CHECK (affected_area_percentage IS NULL OR (affected_area_percentage >= 0 AND affected_area_percentage <= 100))
);

-- =============================================================================
-- 6. AI ANALYSIS DATABASE (Traceable, Append-Only Predictions)
-- =============================================================================

CREATE TABLE IF NOT EXISTS ai_model_versions (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  model_name               VARCHAR(100) NOT NULL,
  version_tag              VARCHAR(50) NOT NULL,
  model_family             VARCHAR(50) NOT NULL,
  weights_digest_sha256    VARCHAR(64) NOT NULL,
  training_dataset_version VARCHAR(50),
  f1_score                 DOUBLE PRECISION,
  accuracy                 DOUBLE PRECISION,
  inference_runtime        VARCHAR(50) NOT NULL DEFAULT 'onnxruntime',
  is_active                BOOLEAN NOT NULL DEFAULT true,
  deployed_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  retired_at               TIMESTAMPTZ,
  created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_ai_model_name_version UNIQUE (model_name, version_tag),
  CONSTRAINT chk_ai_model_family CHECK (model_family IN ('yolo', 'resnet', 'efficientnet', 'vit', 'ensemble', 'custom'))
);

CREATE TRIGGER trg_ai_model_versions_updated_at
  BEFORE UPDATE ON ai_model_versions
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS ai_analysis (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  media_file_id      UUID NOT NULL REFERENCES media_files(id) ON DELETE CASCADE,
  requested_by       UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  status             VARCHAR(30) NOT NULL DEFAULT 'pending',
  analysis_type      VARCHAR(50) NOT NULL DEFAULT 'detection',
  processing_time_ms INTEGER,
  raw_response       JSONB,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_ai_analysis_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'quarantined')),
  CONSTRAINT chk_ai_analysis_type CHECK (analysis_type IN ('detection', 'classification', 'segmentation', 'severity_estimation', 'multitask'))
);

CREATE TRIGGER trg_ai_analysis_updated_at
  BEFORE UPDATE ON ai_analysis
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS media_analysis_links (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  media_file_id UUID NOT NULL REFERENCES media_files(id) ON DELETE CASCADE,
  analysis_id   UUID NOT NULL REFERENCES ai_analysis(id) ON DELETE CASCADE,
  frame_id      UUID REFERENCES media_frames(id) ON DELETE SET NULL,
  linked_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_predictions (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id         UUID NOT NULL REFERENCES ai_analysis(id) ON DELETE CASCADE,
  model_version_id    UUID NOT NULL REFERENCES ai_model_versions(id) ON DELETE RESTRICT,
  pest_id             UUID REFERENCES pests(id) ON DELETE SET NULL,
  disease_id          UUID REFERENCES diseases(id) ON DELETE SET NULL,
  primary_diagnosis   VARCHAR(150) NOT NULL,
  confidence_score    NUMERIC(5, 4) NOT NULL,
  severity_level      VARCHAR(20) NOT NULL DEFAULT 'medium',
  inference_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_superseded       BOOLEAN NOT NULL DEFAULT false,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_ai_pred_confidence_range CHECK (confidence_score >= 0.0000 AND confidence_score <= 1.0000),
  CONSTRAINT chk_ai_pred_severity_level CHECK (severity_level IN ('none', 'low', 'medium', 'high', 'severe'))
);

CREATE TABLE IF NOT EXISTS ai_detections (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prediction_id        UUID NOT NULL REFERENCES ai_predictions(id) ON DELETE CASCADE,
  label                VARCHAR(100) NOT NULL,
  bbox_x_min           NUMERIC(6, 4) NOT NULL,
  bbox_y_min           NUMERIC(6, 4) NOT NULL,
  bbox_x_max           NUMERIC(6, 4) NOT NULL,
  bbox_y_max           NUMERIC(6, 4) NOT NULL,
  detection_confidence NUMERIC(5, 4) NOT NULL,
  mask_rle             TEXT,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_ai_detection_confidence_range CHECK (detection_confidence >= 0.0000 AND detection_confidence <= 1.0000),
  CONSTRAINT chk_ai_det_box_x CHECK (bbox_x_min >= 0 AND bbox_x_min <= bbox_x_max),
  CONSTRAINT chk_ai_det_box_y CHECK (bbox_y_min >= 0 AND bbox_y_min <= bbox_y_max)
);

CREATE TABLE IF NOT EXISTS ai_confidence (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prediction_id      UUID NOT NULL REFERENCES ai_predictions(id) ON DELETE CASCADE,
  class_label        VARCHAR(100) NOT NULL,
  probability        NUMERIC(5, 4) NOT NULL,
  calibration_method VARCHAR(50) NOT NULL DEFAULT 'platt',
  entropy_score      DOUBLE PRECISION,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_ai_conf_probability_range CHECK (probability >= 0.0000 AND probability <= 1.0000)
);

CREATE TABLE IF NOT EXISTS diagnosis_records (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id         UUID NOT NULL REFERENCES ai_analysis(id) ON DELETE CASCADE,
  prediction_id       UUID REFERENCES ai_predictions(id) ON DELETE SET NULL,
  verified_by         UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  confirmed_pest_id   UUID REFERENCES pests(id) ON DELETE SET NULL,
  confirmed_disease_id UUID REFERENCES diseases(id) ON DELETE SET NULL,
  confirmation_status VARCHAR(50) NOT NULL,
  expert_notes        TEXT,
  diagnosed_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_diag_confirmation_status CHECK (confirmation_status IN ('expert_confirmed', 'expert_rejected', 'pending_review', 'auto_accepted'))
);

CREATE TRIGGER trg_diagnosis_records_updated_at
  BEFORE UPDATE ON diagnosis_records
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS ai_feedback (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  diagnosis_record_id UUID NOT NULL REFERENCES diagnosis_records(id) ON DELETE CASCADE,
  prediction_id       UUID NOT NULL REFERENCES ai_predictions(id) ON DELETE CASCADE,
  user_id             UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  feedback_type       VARCHAR(50) NOT NULL,
  corrected_pest_id   UUID REFERENCES pests(id) ON DELETE SET NULL,
  corrected_disease_id UUID REFERENCES diseases(id) ON DELETE SET NULL,
  comments            TEXT,
  submitted_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_ai_feedback_type CHECK (feedback_type IN ('agree', 'disagree', 'false_positive', 'missed_detection', 'unclear_image'))
);

-- =============================================================================
-- 7. PEST MANAGEMENT DATABASE
-- =============================================================================

CREATE TABLE IF NOT EXISTS ipm_methods (
  id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code                        VARCHAR(50) NOT NULL UNIQUE,
  title                       VARCHAR(150) NOT NULL,
  category                    VARCHAR(50) NOT NULL,
  description                 TEXT,
  environmental_impact_rating VARCHAR(20) NOT NULL DEFAULT 'low',
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_ipm_methods_category CHECK (category IN ('preventive', 'cultural', 'mechanical', 'physical', 'biological', 'behavioral', 'chemical')),
  CONSTRAINT chk_ipm_methods_env_impact CHECK (environmental_impact_rating IN ('none', 'low', 'moderate', 'high', 'severe'))
);

CREATE TRIGGER trg_ipm_methods_updated_at
  BEFORE UPDATE ON ipm_methods
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS pest_control_options (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pest_id              UUID REFERENCES pests(id) ON DELETE CASCADE,
  disease_id           UUID REFERENCES diseases(id) ON DELETE CASCADE,
  crop_type_id         UUID REFERENCES crop_types(id) ON DELETE CASCADE,
  ipm_method_id        UUID NOT NULL REFERENCES ipm_methods(id) ON DELETE RESTRICT,
  strategy_summary     TEXT NOT NULL,
  applicability_window VARCHAR(100),
  effectiveness_rating VARCHAR(20) NOT NULL DEFAULT 'moderate',
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_control_options_target_present CHECK (pest_id IS NOT NULL OR disease_id IS NOT NULL),
  CONSTRAINT chk_control_options_eff_rating CHECK (effectiveness_rating IN ('low', 'moderate', 'high', 'very_high'))
);

CREATE TRIGGER trg_pest_control_options_updated_at
  BEFORE UPDATE ON pest_control_options
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS biological_controls (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ipm_method_id          UUID NOT NULL REFERENCES ipm_methods(id) ON DELETE CASCADE,
  agent_name             VARCHAR(150) NOT NULL,
  agent_type             VARCHAR(50) NOT NULL,
  target_pest_id         UUID NOT NULL REFERENCES pests(id) ON DELETE CASCADE,
  release_rate           VARCHAR(100),
  optimal_timing         VARCHAR(100),
  conservation_practices TEXT,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_biocontrol_agent_type CHECK (agent_type IN ('predator', 'parasitoid', 'pathogen', 'entomopathogen', 'microbial', 'antagonist'))
);

CREATE TRIGGER trg_biological_controls_updated_at
  BEFORE UPDATE ON biological_controls
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS mechanical_controls (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ipm_method_id    UUID NOT NULL REFERENCES ipm_methods(id) ON DELETE CASCADE,
  method_name      VARCHAR(150) NOT NULL,
  equipment_needed VARCHAR(200),
  labor_intensity  VARCHAR(20) NOT NULL DEFAULT 'medium',
  execution_steps  TEXT NOT NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_mech_control_labor CHECK (labor_intensity IN ('low', 'medium', 'high', 'intensive'))
);

CREATE TRIGGER trg_mechanical_controls_updated_at
  BEFORE UPDATE ON mechanical_controls
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS cultural_controls (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ipm_method_id           UUID NOT NULL REFERENCES ipm_methods(id) ON DELETE CASCADE,
  practice_type           VARCHAR(50) NOT NULL,
  implementation_protocol TEXT NOT NULL,
  recommended_timing      VARCHAR(100),
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_cult_control_practice CHECK (practice_type IN ('crop_rotation', 'intercropping', 'trap_cropping', 'field_sanitation', 'adjusted_sowing', 'resistant_varieties'))
);

CREATE TRIGGER trg_cultural_controls_updated_at
  BEFORE UPDATE ON cultural_controls
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS physical_controls (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ipm_method_id        UUID NOT NULL REFERENCES ipm_methods(id) ON DELETE CASCADE,
  control_mechanism    VARCHAR(50) NOT NULL,
  technical_parameters TEXT,
  installation_guide   TEXT,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_phys_control_mechanism CHECK (control_mechanism IN ('solarization', 'soil_steaming', 'mesh_exclusion', 'row_covers', 'reflective_mulch', 'flame_weeding'))
);

CREATE TRIGGER trg_physical_controls_updated_at
  BEFORE UPDATE ON physical_controls
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS behavioral_controls (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ipm_method_id             UUID NOT NULL REFERENCES ipm_methods(id) ON DELETE CASCADE,
  attractant_type           VARCHAR(50) NOT NULL,
  trap_density_per_hectare  INTEGER,
  replacement_interval_days INTEGER,
  monitoring_threshold      VARCHAR(100),
  created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_behav_control_attractant CHECK (attractant_type IN ('sex_pheromone', 'aggregation_pheromone', 'yellow_sticky_trap', 'blue_sticky_trap', 'light_trap', 'food_bait'))
);

CREATE TRIGGER trg_behavioral_controls_updated_at
  BEFORE UPDATE ON behavioral_controls
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS chemical_controls (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ipm_method_id         UUID NOT NULL REFERENCES ipm_methods(id) ON DELETE CASCADE,
  active_ingredient     VARCHAR(150) NOT NULL,
  chemical_class        VARCHAR(100) NOT NULL,
  mode_of_action        VARCHAR(200),
  resistance_risk_group VARCHAR(50),
  toxicity_class        VARCHAR(20) NOT NULL,
  phi_days              INTEGER,
  rei_hours             INTEGER,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_chem_control_toxicity CHECK (toxicity_class IN ('WHO_Ia', 'WHO_Ib', 'WHO_II', 'WHO_III', 'WHO_U', 'Green_Triangle', 'Blue_Triangle', 'Yellow_Triangle', 'Red_Triangle')),
  CONSTRAINT chk_chem_phi_nonneg CHECK (phi_days IS NULL OR phi_days >= 0),
  CONSTRAINT chk_chem_rei_nonneg CHECK (rei_hours IS NULL OR rei_hours >= 0)
);

CREATE TRIGGER trg_chemical_controls_updated_at
  BEFORE UPDATE ON chemical_controls
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS pesticide_registrations (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chemical_control_id    UUID NOT NULL REFERENCES chemical_controls(id) ON DELETE CASCADE,
  registration_number    VARCHAR(100) NOT NULL UNIQUE,
  registering_authority  VARCHAR(100) NOT NULL DEFAULT 'CIBRC',
  registered_trade_name  VARCHAR(150) NOT NULL,
  approved_crop_id       UUID NOT NULL REFERENCES crop_types(id) ON DELETE RESTRICT,
  approved_pest_id       UUID REFERENCES pests(id) ON DELETE RESTRICT,
  approved_dosage_per_ha VARCHAR(100) NOT NULL,
  approval_date          DATE NOT NULL,
  expiry_date            DATE,
  status                 VARCHAR(30) NOT NULL DEFAULT 'active',
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_pesticide_reg_status CHECK (status IN ('active', 'provisional', 'expired', 'restricted', 'banned', 'cancelled'))
);

CREATE TRIGGER trg_pesticide_registrations_updated_at
  BEFORE UPDATE ON pesticide_registrations
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS treatment_records (
  id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farm_plot_id                UUID NOT NULL REFERENCES farm_plots(id) ON DELETE CASCADE,
  crop_instance_id            UUID NOT NULL REFERENCES crop_instances(id) ON DELETE CASCADE,
  applied_by                  UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  ipm_method_id               UUID NOT NULL REFERENCES ipm_methods(id) ON DELETE RESTRICT,
  chemical_control_id         UUID REFERENCES chemical_controls(id) ON DELETE SET NULL,
  registration_id             UUID REFERENCES pesticide_registrations(id) ON DELETE SET NULL,
  application_date            TIMESTAMPTZ NOT NULL,
  dosage_applied              VARCHAR(100) NOT NULL,
  weather_conditions_at_spray VARCHAR(150),
  safety_equipment_used       VARCHAR(200),
  notes                       TEXT,
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_treatment_records_updated_at
  BEFORE UPDATE ON treatment_records
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS treatment_effectiveness (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  treatment_record_id       UUID NOT NULL REFERENCES treatment_records(id) ON DELETE CASCADE,
  evaluation_date           TIMESTAMPTZ NOT NULL DEFAULT now(),
  days_post_treatment       INTEGER NOT NULL,
  pest_mortality_percentage DOUBLE PRECISION,
  crop_recovery_score       INTEGER NOT NULL,
  phytotoxicity_observed    BOOLEAN NOT NULL DEFAULT false,
  evaluator_id              UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  evaluation_notes          TEXT,
  created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_treat_eff_days_nonneg CHECK (days_post_treatment >= 0),
  CONSTRAINT chk_treat_eff_mortality_range CHECK (pest_mortality_percentage IS NULL OR (pest_mortality_percentage >= 0 AND pest_mortality_percentage <= 100)),
  CONSTRAINT chk_treat_eff_recovery_score CHECK (crop_recovery_score >= 1 AND crop_recovery_score <= 5)
);

-- =============================================================================
-- 8. HOTSPOT AND OUTBREAK DATABASE (Spatial, Temporal, Risk Tracking)
-- =============================================================================

CREATE TABLE IF NOT EXISTS pest_reports (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reporter_id         UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  farm_plot_id        UUID REFERENCES farm_plots(id) ON DELETE SET NULL,
  reported_pest_id    UUID REFERENCES pests(id) ON DELETE SET NULL,
  reported_disease_id UUID REFERENCES diseases(id) ON DELETE SET NULL,
  report_location     geometry(Point, 4326) NOT NULL,
  severity            VARCHAR(20) NOT NULL DEFAULT 'moderate',
  observation_date    TIMESTAMPTZ NOT NULL,
  status              VARCHAR(30) NOT NULL DEFAULT 'unverified',
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_pest_reports_severity CHECK (severity IN ('low', 'moderate', 'high', 'severe')),
  CONSTRAINT chk_pest_reports_status CHECK (status IN ('unverified', 'under_investigation', 'verified', 'rejected')),
  CONSTRAINT chk_pest_report_target_present CHECK (reported_pest_id IS NOT NULL OR reported_disease_id IS NOT NULL)
);

CREATE TRIGGER trg_pest_reports_updated_at
  BEFORE UPDATE ON pest_reports
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS verified_cases (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pest_report_id     UUID NOT NULL UNIQUE REFERENCES pest_reports(id) ON DELETE CASCADE,
  verifier_id        UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  confirmed_location geometry(Point, 4326) NOT NULL,
  confirmed_pest_id  UUID REFERENCES pests(id) ON DELETE SET NULL,
  confirmed_disease_id UUID REFERENCES diseases(id) ON DELETE SET NULL,
  confidence_level   VARCHAR(20) NOT NULL DEFAULT 'high',
  verified_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  notes              TEXT,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_verified_cases_conf CHECK (confidence_level IN ('tentative', 'moderate', 'high', 'laboratory_confirmed'))
);

CREATE TRIGGER trg_verified_cases_updated_at
  BEFORE UPDATE ON verified_cases
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS hotspot_regions (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  region_name       VARCHAR(150) NOT NULL,
  boundary_geom     geometry(MultiPolygon, 4326) NOT NULL,
  pest_id           UUID REFERENCES pests(id) ON DELETE SET NULL,
  disease_id        UUID REFERENCES diseases(id) ON DELETE SET NULL,
  risk_level        VARCHAR(20) NOT NULL DEFAULT 'moderate',
  active_case_count INTEGER NOT NULL DEFAULT 1,
  start_date        DATE NOT NULL,
  end_date          DATE,
  is_active         BOOLEAN NOT NULL DEFAULT true,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_hotspot_risk_level CHECK (risk_level IN ('low', 'moderate', 'high', 'extreme')),
  CONSTRAINT chk_hotspot_cases_nonneg CHECK (active_case_count >= 0)
);

CREATE TRIGGER trg_hotspot_regions_updated_at
  BEFORE UPDATE ON hotspot_regions
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS regional_pest_statistics (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  region_code      VARCHAR(50) NOT NULL,
  date_bucket      DATE NOT NULL,
  pest_id          UUID REFERENCES pests(id) ON DELETE SET NULL,
  disease_id       UUID REFERENCES diseases(id) ON DELETE SET NULL,
  total_reports    INTEGER NOT NULL DEFAULT 0,
  verified_count   INTEGER NOT NULL DEFAULT 0,
  incidence_rate   DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  average_severity DOUBLE PRECISION,
  calculated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_reg_pest_stat_bucket UNIQUE (region_code, date_bucket, pest_id, disease_id)
);

CREATE TABLE IF NOT EXISTS outbreak_predictions (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  region_geom              geometry(Polygon, 4326) NOT NULL,
  pest_id                  UUID REFERENCES pests(id) ON DELETE SET NULL,
  disease_id               UUID REFERENCES diseases(id) ON DELETE SET NULL,
  predicted_risk_score     NUMERIC(5, 4) NOT NULL,
  forecast_horizon_days    INTEGER NOT NULL,
  prediction_model_version UUID REFERENCES ai_model_versions(id) ON DELETE SET NULL,
  prediction_timestamp     TIMESTAMPTZ NOT NULL DEFAULT now(),
  valid_from               TIMESTAMPTZ NOT NULL,
  valid_until              TIMESTAMPTZ NOT NULL,
  created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_outbreak_risk_range CHECK (predicted_risk_score >= 0.0000 AND predicted_risk_score <= 1.0000),
  CONSTRAINT chk_outbreak_horizon_pos CHECK (forecast_horizon_days > 0)
);

CREATE TABLE IF NOT EXISTS spread_observations (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hotspot_id              UUID NOT NULL REFERENCES hotspot_regions(id) ON DELETE CASCADE,
  observation_location    geometry(Point, 4326) NOT NULL,
  spread_direction_degrees DOUBLE PRECISION,
  spread_rate_km_per_day  DOUBLE PRECISION,
  observed_at             TIMESTAMPTZ NOT NULL,
  recorder_id             UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_spread_direction_degrees CHECK (spread_direction_degrees IS NULL OR (spread_direction_degrees >= 0 AND spread_direction_degrees <= 360))
);

CREATE TABLE IF NOT EXISTS risk_history (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  region_code          VARCHAR(50) NOT NULL,
  timestamp            TIMESTAMPTZ NOT NULL,
  pest_id              UUID REFERENCES pests(id) ON DELETE SET NULL,
  historical_risk_score NUMERIC(5, 4) NOT NULL,
  weather_conditions   TEXT,
  source_run_id        VARCHAR(100),
  recorded_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_risk_hist_score_range CHECK (historical_risk_score >= 0.0000 AND historical_risk_score <= 1.0000)
);

CREATE TABLE IF NOT EXISTS monitoring_coverage (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  area_name               VARCHAR(150) NOT NULL,
  boundary                geometry(Polygon, 4326) NOT NULL,
  assigned_scouts_count   INTEGER NOT NULL DEFAULT 0,
  scouting_frequency_days INTEGER NOT NULL DEFAULT 7,
  last_monitored_date     DATE,
  coverage_percentage     DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_monitoring_coverage_pct CHECK (coverage_percentage >= 0.0 AND coverage_percentage <= 100.0)
);

CREATE TRIGGER trg_monitoring_coverage_updated_at
  BEFORE UPDATE ON monitoring_coverage
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================================
-- 9. RECOVERY AND INSPECTION DATABASE
-- =============================================================================

CREATE TABLE IF NOT EXISTS inspections (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farm_id               UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
  plot_id               UUID REFERENCES farm_plots(id) ON DELETE SET NULL,
  inspector_id          UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  scheduled_date        DATE NOT NULL,
  conducted_at          TIMESTAMPTZ,
  status                VARCHAR(30) NOT NULL DEFAULT 'scheduled',
  overall_health_rating INTEGER,
  findings_summary      TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_inspections_status CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled', 'rescheduled')),
  CONSTRAINT chk_inspections_health_rating CHECK (overall_health_rating IS NULL OR (overall_health_rating >= 1 AND overall_health_rating <= 5))
);

CREATE TRIGGER trg_inspections_updated_at
  BEFORE UPDATE ON inspections
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS inspection_assignments (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  inspection_id      UUID NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
  agent_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  assigned_by        UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  assigned_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  role_in_inspection VARCHAR(50) NOT NULL DEFAULT 'lead_scout',
  status             VARCHAR(30) NOT NULL DEFAULT 'assigned',
  CONSTRAINT uq_inspection_agent UNIQUE (inspection_id, agent_id),
  CONSTRAINT chk_insp_assign_status CHECK (status IN ('assigned', 'accepted', 'declined', 'completed'))
);

CREATE TABLE IF NOT EXISTS scouting_records (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  inspection_id         UUID NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
  waypoint_location     geometry(Point, 4326) NOT NULL,
  plant_count_inspected INTEGER NOT NULL,
  infested_plant_count  INTEGER NOT NULL,
  pest_id               UUID REFERENCES pests(id) ON DELETE SET NULL,
  notes                 TEXT,
  recorded_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_scouting_inspected_nonneg CHECK (plant_count_inspected >= 0),
  CONSTRAINT chk_scouting_infested_bounds CHECK (infested_plant_count >= 0 AND infested_plant_count <= plant_count_inspected)
);

CREATE TABLE IF NOT EXISTS recovery_records (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farm_plot_id        UUID NOT NULL REFERENCES farm_plots(id) ON DELETE CASCADE,
  crop_instance_id    UUID NOT NULL REFERENCES crop_instances(id) ON DELETE CASCADE,
  treatment_record_id UUID REFERENCES treatment_records(id) ON DELETE SET NULL,
  inspection_id       UUID REFERENCES inspections(id) ON DELETE SET NULL,
  recovery_status     VARCHAR(30) NOT NULL,
  recovery_percentage DOUBLE PRECISION NOT NULL,
  assessed_at         TIMESTAMPTZ NOT NULL,
  assessor_id         UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_recovery_status_valid CHECK (recovery_status IN ('worsening', 'stable', 'partial_recovery', 'full_recovery')),
  CONSTRAINT chk_recovery_pct_range CHECK (recovery_percentage >= 0.0 AND recovery_percentage <= 100.0)
);

CREATE TRIGGER trg_recovery_records_updated_at
  BEFORE UPDATE ON recovery_records
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS recovery_comparisons (
  id                           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recovery_record_id           UUID NOT NULL REFERENCES recovery_records(id) ON DELETE CASCADE,
  baseline_media_id            UUID NOT NULL REFERENCES media_files(id) ON DELETE RESTRICT,
  current_media_id             UUID NOT NULL REFERENCES media_files(id) ON DELETE RESTRICT,
  symptom_reduction_percentage DOUBLE PRECISION,
  foliage_regrowth_score       INTEGER,
  comparison_notes             TEXT,
  created_at                   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                   TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_rec_comp_reduction_pct CHECK (symptom_reduction_percentage IS NULL OR (symptom_reduction_percentage >= 0.0 AND symptom_reduction_percentage <= 100.0)),
  CONSTRAINT chk_rec_comp_regrowth_score CHECK (foliage_regrowth_score IS NULL OR (foliage_regrowth_score >= 1 AND foliage_regrowth_score <= 5))
);

CREATE TRIGGER trg_recovery_comparisons_updated_at
  BEFORE UPDATE ON recovery_comparisons
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS seasonal_history (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farm_plot_id         UUID NOT NULL REFERENCES farm_plots(id) ON DELETE CASCADE,
  season_year          INTEGER NOT NULL,
  season_name          VARCHAR(30) NOT NULL,
  crop_type_id         UUID NOT NULL REFERENCES crop_types(id) ON DELETE RESTRICT,
  total_yield_kg       DOUBLE PRECISION,
  pest_pressure_rating VARCHAR(20) NOT NULL DEFAULT 'low',
  weather_summary      TEXT,
  recorded_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_seasonal_hist_plot_season UNIQUE (farm_plot_id, season_year, season_name),
  CONSTRAINT chk_seasonal_hist_season CHECK (season_name IN ('kharif', 'rabi', 'zaid', 'annual')),
  CONSTRAINT chk_seasonal_hist_pest_pressure CHECK (pest_pressure_rating IN ('none', 'low', 'moderate', 'high', 'severe'))
);

CREATE TABLE IF NOT EXISTS infestation_history (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  farm_plot_id         UUID NOT NULL REFERENCES farm_plots(id) ON DELETE CASCADE,
  crop_instance_id     UUID REFERENCES crop_instances(id) ON DELETE SET NULL,
  pest_id              UUID REFERENCES pests(id) ON DELETE SET NULL,
  disease_id           UUID REFERENCES diseases(id) ON DELETE SET NULL,
  outbreak_start_date  DATE NOT NULL,
  peak_severity        VARCHAR(20) NOT NULL,
  containment_date     DATE,
  crop_loss_percentage DOUBLE PRECISION,
  recorded_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_infest_hist_loss_range CHECK (crop_loss_percentage IS NULL OR (crop_loss_percentage >= 0.0 AND crop_loss_percentage <= 100.0))
);

-- =============================================================================
-- 10. CHATBOT AND KNOWLEDGE DATABASE
-- =============================================================================

CREATE TABLE IF NOT EXISTS chat_sessions (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title      VARCHAR(150) NOT NULL DEFAULT 'New Conversation',
  language   VARCHAR(10) NOT NULL DEFAULT 'en',
  channel    VARCHAR(20) NOT NULL DEFAULT 'mobile',
  is_active  BOOLEAN NOT NULL DEFAULT true,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ended_at   TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_chat_sessions_channel CHECK (channel IN ('web', 'mobile', 'whatsapp', 'sms', 'ivr'))
);

CREATE TRIGGER trg_chat_sessions_updated_at
  BEFORE UPDATE ON chat_sessions
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS chat_messages (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id      UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  sender_type     VARCHAR(20) NOT NULL,
  message_text    TEXT NOT NULL,
  sequence_number INTEGER NOT NULL,
  cited_sources   JSONB,
  sent_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_chat_session_seq UNIQUE (session_id, sequence_number),
  CONSTRAINT chk_chat_messages_sender_type CHECK (sender_type IN ('user', 'bot', 'expert_agent', 'system'))
);

CREATE TABLE IF NOT EXISTS knowledge_articles (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title        VARCHAR(255) NOT NULL,
  slug         VARCHAR(255) NOT NULL UNIQUE,
  version      INTEGER NOT NULL DEFAULT 1,
  author_id    UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  category     VARCHAR(100) NOT NULL,
  summary      TEXT,
  content      TEXT NOT NULL,
  status       VARCHAR(20) NOT NULL DEFAULT 'published',
  is_current   BOOLEAN NOT NULL DEFAULT true,
  published_at TIMESTAMPTZ,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_knowledge_art_status CHECK (status IN ('draft', 'under_review', 'published', 'archived')),
  CONSTRAINT chk_knowledge_art_version_pos CHECK (version >= 1)
);

CREATE TRIGGER trg_knowledge_articles_updated_at
  BEFORE UPDATE ON knowledge_articles
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS knowledge_chunks (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  article_id    UUID NOT NULL REFERENCES knowledge_articles(id) ON DELETE CASCADE,
  chunk_index   INTEGER NOT NULL,
  content_chunk TEXT NOT NULL,
  token_count   INTEGER NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_art_chunk_index UNIQUE (article_id, chunk_index),
  CONSTRAINT chk_chunk_idx_nonneg CHECK (chunk_index >= 0),
  CONSTRAINT chk_chunk_token_pos CHECK (token_count > 0)
);

CREATE TABLE IF NOT EXISTS knowledge_embeddings (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chunk_id         UUID NOT NULL REFERENCES knowledge_chunks(id) ON DELETE CASCADE,
  embedding_model  VARCHAR(100) NOT NULL,
  embedding_vector TEXT NOT NULL,
  dimension        INTEGER NOT NULL DEFAULT 1536,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_embed_dim_positive CHECK (dimension > 0)
);

CREATE TABLE IF NOT EXISTS chatbot_feedback (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id    UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  rating        INTEGER NOT NULL,
  is_helpful    BOOLEAN NOT NULL DEFAULT true,
  feedback_text TEXT,
  submitted_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_chatbot_rating_range CHECK (rating >= 1 AND rating <= 5)
);

-- =============================================================================
-- 11. NOTIFICATION DATABASE
-- =============================================================================

CREATE TABLE IF NOT EXISTS notifications (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title             VARCHAR(200) NOT NULL,
  body              TEXT NOT NULL,
  notification_type VARCHAR(50) NOT NULL,
  priority          VARCHAR(20) NOT NULL DEFAULT 'medium',
  status            VARCHAR(20) NOT NULL DEFAULT 'pending',
  channel           VARCHAR(20) NOT NULL DEFAULT 'push',
  retry_count       INTEGER NOT NULL DEFAULT 0,
  sent_at           TIMESTAMPTZ,
  read_at           TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_notif_type CHECK (notification_type IN ('pest_alert', 'weather_warning', 'advisory_update', 'inspection_reminder', 'system', 'treatment_due')),
  CONSTRAINT chk_notif_priority CHECK (priority IN ('low', 'medium', 'high', 'critical')),
  CONSTRAINT chk_notif_status CHECK (status IN ('pending', 'sent', 'delivered', 'read', 'failed')),
  CONSTRAINT chk_notif_channel CHECK (channel IN ('push', 'sms', 'in_app', 'email', 'voice_call')),
  CONSTRAINT chk_notif_retry_nonneg CHECK (retry_count >= 0)
);

CREATE TABLE IF NOT EXISTS alert_rules (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rule_name            VARCHAR(100) NOT NULL UNIQUE,
  event_type           VARCHAR(50) NOT NULL,
  condition_expression TEXT NOT NULL,
  threshold_value      NUMERIC(8, 4),
  target_role          VARCHAR(50) NOT NULL DEFAULT 'farmer',
  is_active            BOOLEAN NOT NULL DEFAULT true,
  created_by           UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_alert_rules_updated_at
  BEFORE UPDATE ON alert_rules
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS user_alert_preferences (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  push_enabled           BOOLEAN NOT NULL DEFAULT true,
  sms_enabled            BOOLEAN NOT NULL DEFAULT true,
  email_enabled          BOOLEAN NOT NULL DEFAULT false,
  quiet_hours_start      VARCHAR(5),
  quiet_hours_end        VARCHAR(5),
  min_priority_threshold VARCHAR(20) NOT NULL DEFAULT 'medium',
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_user_alert_min_priority CHECK (min_priority_threshold IN ('low', 'medium', 'high', 'critical'))
);

CREATE TRIGGER trg_user_alert_preferences_updated_at
  BEFORE UPDATE ON user_alert_preferences
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS scheduled_tasks (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_name          VARCHAR(100) NOT NULL,
  task_type          VARCHAR(50) NOT NULL,
  target_user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
  scheduled_time     TIMESTAMPTZ NOT NULL,
  recurrence_pattern VARCHAR(50),
  status             VARCHAR(20) NOT NULL DEFAULT 'pending',
  last_run_at        TIMESTAMPTZ,
  next_run_at        TIMESTAMPTZ,
  retry_count        INTEGER NOT NULL DEFAULT 0,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_task_type_valid CHECK (task_type IN ('scouting_reminder', 'treatment_followup', 'sensor_sync', 'weekly_digest', 'weather_alert')),
  CONSTRAINT chk_task_status_valid CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
  CONSTRAINT chk_task_retry_nonneg CHECK (retry_count >= 0)
);

CREATE TABLE IF NOT EXISTS sync_logs (
  id                           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  device_id                    VARCHAR(100),
  sync_entity_type             VARCHAR(50) NOT NULL,
  client_timestamp             TIMESTAMPTZ NOT NULL,
  server_timestamp             TIMESTAMPTZ NOT NULL DEFAULT now(),
  records_synced               INTEGER NOT NULL DEFAULT 0,
  sync_status                  VARCHAR(30) NOT NULL DEFAULT 'success',
  conflict_resolution_strategy VARCHAR(50) NOT NULL DEFAULT 'server_wins',
  error_details                TEXT,
  created_at                   TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT chk_sync_status_valid CHECK (sync_status IN ('success', 'partial_failure', 'conflict', 'failed')),
  CONSTRAINT chk_sync_records_nonneg CHECK (records_synced >= 0)
);

-- =============================================================================
-- INDEXES & SPATIAL GIST INDEXES
-- =============================================================================

-- Spatial GiST Indexes
CREATE INDEX IF NOT EXISTS idx_farm_boundaries_geom ON farm_boundaries USING GIST (boundary_polygon);
CREATE INDEX IF NOT EXISTS idx_farm_sections_geom ON farm_sections USING GIST (section_polygon) WHERE section_polygon IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_farm_plots_geom ON farm_plots USING GIST (plot_polygon) WHERE plot_polygon IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_farm_locations_centroid ON farm_locations USING GIST (centroid);
CREATE INDEX IF NOT EXISTS idx_plants_geom ON plants USING GIST (plant_location) WHERE plant_location IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_media_locations_geom ON media_locations USING GIST (location);
CREATE INDEX IF NOT EXISTS idx_pest_reports_geom ON pest_reports USING GIST (report_location);
CREATE INDEX IF NOT EXISTS idx_verified_cases_geom ON verified_cases USING GIST (confirmed_location);
CREATE INDEX IF NOT EXISTS idx_hotspot_regions_geom ON hotspot_regions USING GIST (boundary_geom);
CREATE INDEX IF NOT EXISTS idx_outbreak_predictions_geom ON outbreak_predictions USING GIST (region_geom);
CREATE INDEX IF NOT EXISTS idx_spread_obs_geom ON spread_observations USING GIST (observation_location);
CREATE INDEX IF NOT EXISTS idx_scouting_records_geom ON scouting_records USING GIST (waypoint_location);
CREATE INDEX IF NOT EXISTS idx_monitoring_coverage_geom ON monitoring_coverage USING GIST (boundary);

-- Core Foreign Key and Search Indexes
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_farms_owner_id ON farms(owner_id);
CREATE INDEX IF NOT EXISTS idx_farm_members_farm_id ON farm_members(farm_id);
CREATE INDEX IF NOT EXISTS idx_farm_members_user_id ON farm_members(user_id);
CREATE INDEX IF NOT EXISTS idx_crop_instances_plot_id ON crop_instances(plot_id);
CREATE INDEX IF NOT EXISTS idx_crop_instances_crop_type_id ON crop_instances(crop_type_id);
CREATE INDEX IF NOT EXISTS idx_plants_crop_instance_id ON plants(crop_instance_id);
CREATE INDEX IF NOT EXISTS idx_plant_obs_plant_id ON plant_observations(plant_id);
CREATE INDEX IF NOT EXISTS idx_media_files_uploader_id ON media_files(uploader_id);
CREATE INDEX IF NOT EXISTS idx_media_files_hash ON media_files(file_hash_sha256);
CREATE INDEX IF NOT EXISTS idx_media_frames_file_id ON media_frames(media_file_id);
CREATE INDEX IF NOT EXISTS idx_pests_category_id ON pests(pest_category_id);
CREATE INDEX IF NOT EXISTS idx_pest_host_pest_id ON pest_host_crops(pest_id);
CREATE INDEX IF NOT EXISTS idx_pest_host_crop_id ON pest_host_crops(crop_type_id);
CREATE INDEX IF NOT EXISTS idx_diseases_vector_id ON diseases(vector_pest_id);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_media_id ON ai_analysis(media_file_id);
CREATE INDEX IF NOT EXISTS idx_ai_predictions_analysis_id ON ai_predictions(analysis_id);
CREATE INDEX IF NOT EXISTS idx_ai_predictions_model_id ON ai_predictions(model_version_id);
CREATE INDEX IF NOT EXISTS idx_ai_detections_pred_id ON ai_detections(prediction_id);
CREATE INDEX IF NOT EXISTS idx_diagnosis_analysis_id ON diagnosis_records(analysis_id);
CREATE INDEX IF NOT EXISTS idx_diagnosis_verifier_id ON diagnosis_records(verified_by);
CREATE INDEX IF NOT EXISTS idx_ai_feedback_diag_id ON ai_feedback(diagnosis_record_id);
CREATE INDEX IF NOT EXISTS idx_pest_reports_reporter_id ON pest_reports(reporter_id);
CREATE INDEX IF NOT EXISTS idx_pest_reports_plot_id ON pest_reports(farm_plot_id);
CREATE INDEX IF NOT EXISTS idx_hotspot_pest_id ON hotspot_regions(pest_id);
CREATE INDEX IF NOT EXISTS idx_hotspot_disease_id ON hotspot_regions(disease_id);
CREATE INDEX IF NOT EXISTS idx_outbreak_pest_id ON outbreak_predictions(pest_id);
CREATE INDEX IF NOT EXISTS idx_outbreak_disease_id ON outbreak_predictions(disease_id);
CREATE INDEX IF NOT EXISTS idx_inspections_farm_id ON inspections(farm_id);
CREATE INDEX IF NOT EXISTS idx_inspections_inspector_id ON inspections(inspector_id);
CREATE INDEX IF NOT EXISTS idx_recovery_plot_id ON recovery_records(farm_plot_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_art_id ON knowledge_chunks(article_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_embed_chunk_id ON knowledge_embeddings(chunk_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_user_id ON scheduled_tasks(target_user_id);
CREATE INDEX IF NOT EXISTS idx_sync_logs_user_id ON sync_logs(user_id);

-- =============================================================================
-- APPEND-ONLY GUARDS ON PREDICTIONS & AUDIT LOGS
-- =============================================================================

CREATE TRIGGER trg_ai_predictions_append_only
  BEFORE UPDATE OR DELETE ON ai_predictions
  FOR EACH ROW
  WHEN (OLD.is_superseded = NEW.is_superseded AND TG_OP = 'UPDATE')
  EXECUTE FUNCTION reject_mutation();

CREATE TRIGGER trg_outbreak_predictions_append_only
  BEFORE UPDATE OR DELETE ON outbreak_predictions
  FOR EACH ROW EXECUTE FUNCTION reject_mutation();

CREATE TRIGGER trg_risk_history_append_only
  BEFORE UPDATE OR DELETE ON risk_history
  FOR EACH ROW EXECUTE FUNCTION reject_mutation();

