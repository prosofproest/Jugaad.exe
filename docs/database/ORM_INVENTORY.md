# ORM Inventory (authoritative ORM metadata)

Generated from live `Base.metadata` by `backend/scripts/emit_orm_inventory.py`.
Source of truth for every table below is the Python model; schema SQL
is derived from it (see POSTGRESQL_MAPPING_MATRIX.md).

- ORM models/tables discovered: **67**
- Foreign keys (column-level): **54**
- Unique constraints: **14**
- B-tree indexes (declared): **122**
- CHECK constraints in ORM metadata: **46**
- Native ENUM types: **0** (closed sets are `VARCHAR` + service checks)
- Geometry/geography columns: **0** (see §3)
- ORM `relationship()` declarations: **0** (all associations are FK columns)

## 1. Per-table detail

### `advisories` — backend/app/db/models.py :: Advisory

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_advisories_crop_code` (crop_code)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `crop_code` | VARCHAR(60) | NOT NULL | indexed |
| `target_code` | VARCHAR(80) | NOT NULL |  |
| `geo_scope` | JSON | NOT NULL | python default |
| `language` | VARCHAR(10) | NOT NULL |  |
| `title` | VARCHAR(300) | NOT NULL |  |
| `current_version_id` | VARCHAR(64) | NULL |  |
| `status` | VARCHAR(30) | NOT NULL | python default |
| `is_demo` | Boolean | NOT NULL | python default |
| `withdrawal_reason` | Text | NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `advisory_approvals` — backend/app/db/models.py :: AdvisoryApproval

- Primary key: `id`
- Foreign keys:
  - `approver_id` → `users.id`
  - `version_id` → `advisory_versions.id`
- Indexes:
  - `ix_advisory_approvals_version_id` (version_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `version_id` | VARCHAR(64) | NOT NULL | indexed |
| `approver_id` | VARCHAR(64) | NOT NULL |  |
| `role` | VARCHAR(40) | NOT NULL |  |
| `approved_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `notes` | Text | NULL |  |

### `advisory_versions` — backend/app/db/models.py :: AdvisoryVersion

- Primary key: `id`
- Foreign keys:
  - `advisory_id` → `advisories.id`
  - `author_id` → `users.id`
- Unique constraints:
  - `uq_advisory_version` (advisory_id, version)
- Indexes:
  - `ix_advisory_versions_advisory_id` (advisory_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `advisory_id` | VARCHAR(64) | NOT NULL | indexed |
| `version` | Integer | NOT NULL |  |
| `body_md` | Text | NOT NULL |  |
| `action_types` | JSON | NOT NULL | python default |
| `author_id` | VARCHAR(64) | NOT NULL |  |
| `source` | VARCHAR(400) | NOT NULL | python default |
| `season` | VARCHAR(40) | NULL |  |
| `status` | VARCHAR(30) | NOT NULL | python default |
| `valid_from` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL |  |
| `valid_to` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL |  |
| `content_hash` | VARCHAR(128) | NOT NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `alert_deliveries` — backend/app/db/models.py :: AlertDelivery

- Primary key: `id`
- Foreign keys:
  - `alert_id` → `alerts.id`
  - `user_id` → `users.id`
- Indexes:
  - `ix_alert_deliveries_alert_id` (alert_id)
  - `ix_alert_deliveries_user_id` (user_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `alert_id` | VARCHAR(64) | NOT NULL | indexed |
| `user_id` | VARCHAR(64) | NOT NULL | indexed |
| `channel` | VARCHAR(20) | NOT NULL |  |
| `status` | VARCHAR(30) | NOT NULL | python default |
| `provider_ref` | VARCHAR(200) | NULL |  |
| `sent_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `delivered_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `error` | Text | NULL |  |
| `suppressed_reason` | VARCHAR(80) | NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `alert_feedback` — backend/app/db/models.py :: AlertFeedback

- Primary key: `id`
- Foreign keys:
  - `delivery_id` → `alert_deliveries.id`
- Indexes:
  - `ix_alert_feedback_delivery_id` (delivery_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `delivery_id` | VARCHAR(64) | NOT NULL | indexed |
| `rating` | VARCHAR(30) | NOT NULL |  |
| `reason` | VARCHAR(300) | NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `alert_policies` — backend/app/db/models.py :: AlertPolicy

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_alert_policies_scope` (geo_code, target_code)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `geo_code` | VARCHAR(64) | NOT NULL |  |
| `target_code` | VARCHAR(80) | NOT NULL |  |
| `min_band` | VARCHAR(30) | NOT NULL | python default |
| `min_coverage` | VARCHAR(20) | NOT NULL | python default |
| `cooldown_hours` | Integer | NOT NULL | python default |
| `channels` | JSON | NOT NULL | python default |
| `approved_by` | VARCHAR(64) | NULL |  |
| `active` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `alerts` — backend/app/db/models.py :: Alert

- Primary key: `id`
- Foreign keys:
  - `forecast_id` → `forecasts.id`
- Unique constraints:
  - `uq_alerts_dedupe_key` (dedupe_key)
- Indexes:
  - `ix_alerts_forecast_id` (forecast_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `forecast_id` | VARCHAR(64) | NOT NULL | indexed |
| `geo_code` | VARCHAR(64) | NOT NULL |  |
| `target_code` | VARCHAR(80) | NOT NULL |  |
| `band` | VARCHAR(30) | NOT NULL |  |
| `window_from` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL |  |
| `window_to` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL |  |
| `message_version` | VARCHAR(80) | NOT NULL |  |
| `coverage` | VARCHAR(20) | NOT NULL |  |
| `reason_summary` | VARCHAR(300) | NULL |  |
| `dedupe_key` | VARCHAR(128) | NOT NULL | UNIQUE |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `audit_events` — backend/app/db/models.py :: AuditEvent

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_audit_entity` (entity_type, entity_id, created_at)
  - `ix_audit_events_action` (action)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `actor_id` | VARCHAR(64) | NULL |  |
| `actor_role` | VARCHAR(40) | NULL |  |
| `action` | VARCHAR(80) | NOT NULL | indexed |
| `entity_type` | VARCHAR(60) | NULL |  |
| `entity_id` | VARCHAR(64) | NULL |  |
| `reason` | Text | NULL |  |
| `request_id` | VARCHAR(128) | NULL |  |
| `ip_hash` | VARCHAR(128) | NULL |  |
| `detail` | JSON | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `chat_review_requests` — backend/app/modules/conversations/orm.py :: ReviewRequestRow (chat)

- Primary key: `id`
- Foreign keys:
  - `conversation_id` → `conversations.id` ON DELETE CASCADE
  - `message_id` → `messages.id` ON DELETE CASCADE
- Unique constraints:
  - `uq_chat_review_requests_message_id` (message_id)
- Indexes:
  - `ix_chat_review_requests_conversation_id` (conversation_id)
  - `ix_chat_review_requests_message_id` (message_id)
  - `ix_chat_review_requests_owner_id` (owner_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK |
| `conversation_id` | VARCHAR(64) | NOT NULL | indexed |
| `message_id` | VARCHAR(64) | NOT NULL | indexed |
| `owner_id` | VARCHAR(64) | NOT NULL | indexed |
| `status` | VARCHAR(32) | NOT NULL | python default |
| `reason` | Text | NULL |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | server_default=now() |

### `consents` — backend/app/db/models.py :: Consent

- Primary key: `id`
- Foreign keys:
  - `user_id` → `users.id`
- Indexes:
  - `ix_consents_user_type` (user_id, type, created_at)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `user_id` | VARCHAR(64) | NOT NULL |  |
| `type` | VARCHAR(60) | NOT NULL |  |
| `version` | VARCHAR(60) | NOT NULL |  |
| `granted` | Boolean | NOT NULL |  |
| `text_hash` | VARCHAR(128) | NOT NULL |  |
| `channel` | VARCHAR(30) | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `conversations` — backend/app/modules/conversations/orm.py :: ConversationRow

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_conversations_owner_id` (owner_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK |
| `owner_id` | VARCHAR(64) | NOT NULL | indexed |
| `title` | VARCHAR(120) | NOT NULL |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | server_default=now() |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | server_default=now() |
| `last_message_at` | TIMESTAMP WITH TIME ZONE | NOT NULL |  |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | NULL |  |

### `crop_calendars` — backend/app/db/models.py :: CropCalendar

- Primary key: `id`
- Foreign keys:
  - `crop_code` → `crops.code`
- Indexes:
  - `ix_crop_calendars_lookup` (crop_code, geo_code, season)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `crop_code` | VARCHAR(60) | NOT NULL |  |
| `geo_code` | VARCHAR(64) | NOT NULL |  |
| `season` | VARCHAR(40) | NOT NULL |  |
| `planting_window` | JSON | NOT NULL | python default |
| `stage_windows` | JSON | NOT NULL | python default |

### `crop_cycles` — backend/app/db/models.py :: CropCycle

- Primary key: `id`
- Foreign keys:
  - `crop_code` → `crops.code`
  - `growing_area_id` → `growing_areas.id`
- Indexes:
  - `ix_crop_cycles_growing_area_id` (growing_area_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `growing_area_id` | VARCHAR(64) | NOT NULL | indexed |
| `crop_code` | VARCHAR(60) | NOT NULL |  |
| `variety` | VARCHAR(120) | NULL |  |
| `planting_date` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `stage` | VARCHAR(40) | NULL |  |
| `stage_updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |

### `crops` — backend/app/db/models.py :: Crop

- Primary key: `code`
- Foreign keys: none

| Column | Type | Null | Notes |
|---|---|---|---|
| `code` | VARCHAR(60) | NOT NULL | PK |
| `name` | VARCHAR(200) | NOT NULL |  |
| `supported` | Boolean | NOT NULL | python default |
| `supported_from` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `devices` — backend/app/db/models.py :: Device

- Primary key: `id`
- Foreign keys:
  - `user_id` → `users.id`
- Indexes:
  - `ix_devices_user_id` (user_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `user_id` | VARCHAR(64) | NOT NULL | indexed |
| `platform` | VARCHAR(30) | NOT NULL |  |
| `app_version` | VARCHAR(40) | NULL |  |
| `push_token` | VARCHAR(255) | NULL |  |
| `last_seen_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `disease_reports` — backend/app/geo/models.py :: DiseaseReport

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_disease_reports_crop_code` (crop_code)
  - `ix_disease_reports_event_date` (event_date)
  - `ix_disease_reports_h3_cell_id` (h3_cell_id)
  - `ix_disease_reports_target_code` (target_code)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `h3_cell_id` | VARCHAR(32) | NOT NULL | indexed |
| `resolution` | Integer | NOT NULL |  |
| `crop_code` | VARCHAR(60) | NOT NULL | indexed |
| `target_code` | VARCHAR(80) | NOT NULL | indexed |
| `event_date` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | indexed |
| `report_date` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `report_source` | VARCHAR(50) | NOT NULL |  |
| `case_count` | Integer | NOT NULL | python default |
| `unique_farms` | Integer | NOT NULL | python default |
| `verified_farms` | Integer | NOT NULL | python default |
| `severity_distribution` | JSON | NOT NULL | python default |
| `avg_ai_confidence` | Numeric | NULL |  |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `expert_verifications` — backend/app/geo/models.py :: ExpertVerification

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_expert_verifications_inspection_result_id` (inspection_result_id)
  - `ix_expert_verifications_observation_id` (observation_id)
  - `ix_expert_verifications_verification_status` (verification_status)
  - `ix_expert_verifications_verified_by` (verified_by)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `observation_id` | VARCHAR(64) | NULL | indexed |
| `inspection_result_id` | VARCHAR(64) | NULL | indexed |
| `verified_by` | VARCHAR(64) | NOT NULL | indexed |
| `verification_status` | VARCHAR(30) | NOT NULL | indexed |
| `corrected_target_code` | VARCHAR(80) | NULL |  |
| `corrected_severity` | VARCHAR(30) | NULL |  |
| `notes` | Text | NULL |  |
| `verified_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `export_jobs` — backend/app/db/models.py :: ExportJob

- Primary key: `id`
- Foreign keys:
  - `requested_by` → `users.id`

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `requested_by` | VARCHAR(64) | NOT NULL |  |
| `purpose` | VARCHAR(400) | NOT NULL |  |
| `filters` | JSON | NOT NULL | python default |
| `status` | VARCHAR(20) | NOT NULL | python default |
| `row_count` | Integer | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `farm_hexagon_assignments` — backend/app/geo/models.py :: FarmHexagonAssignment

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_farm_hexagon_assignments_farm_id` (farm_id)
  - `ix_farm_hexagon_assignments_geo_code` (geo_code)
  - `ix_farm_hexagon_assignments_h3_cell_id` (h3_cell_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `farm_id` | VARCHAR(64) | NOT NULL | indexed |
| `geo_code` | VARCHAR(64) | NOT NULL | indexed |
| `h3_cell_id` | VARCHAR(32) | NOT NULL | indexed |
| `resolution` | Integer | NOT NULL |  |
| `overlap_area_m2` | Numeric | NULL |  |
| `overlap_percentage` | Numeric | NULL |  |
| `is_primary` | Boolean | NOT NULL | python default |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `feature_snapshots` — backend/app/db/models.py :: FeatureSnapshot

- Primary key: `id`
- Foreign keys: none

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `crop_code` | VARCHAR(60) | NOT NULL |  |
| `target_code` | VARCHAR(80) | NOT NULL |  |
| `geo_code` | VARCHAR(64) | NOT NULL |  |
| `horizon_days` | Integer | NOT NULL |  |
| `issue_time` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL |  |
| `features` | JSON | NOT NULL | python default |
| `source_refs` | JSON | NOT NULL | python default |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `field_agent_profiles` — backend/app/geo/models.py :: FieldAgentProfile

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_field_agent_profiles_primary_geo_code` (primary_geo_code)
  - `ix_field_agent_profiles_user_id` (user_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `user_id` | VARCHAR(64) | NOT NULL | UNIQUE; indexed |
| `primary_geo_code` | VARCHAR(64) | NULL | indexed |
| `expertise_areas` | JSON | NOT NULL | python default |
| `crop_experience` | JSON | NOT NULL | python default |
| `max_distance_km` | Numeric | NOT NULL | python default |
| `is_available` | Boolean | NOT NULL | python default |
| `current_lat` | Numeric | NULL |  |
| `current_lng` | Numeric | NULL |  |
| `location_updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `current_workload` | Integer | NOT NULL | python default |
| `max_concurrent_tasks` | Integer | NOT NULL | python default |
| `completion_rate` | Numeric | NULL |  |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `forecast_runs` — backend/app/db/models.py :: ForecastRun

- Primary key: `id`
- Foreign keys: none

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `started_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `finished_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `status` | VARCHAR(30) | NOT NULL | python default |
| `model_version` | VARCHAR(80) | NULL |  |
| `areas_total` | Integer | NOT NULL | python default |
| `areas_scored` | Integer | NOT NULL | python default |
| `areas_insufficient` | Integer | NOT NULL | python default |
| `error` | Text | NULL |  |

### `forecasts` — backend/app/db/models.py :: Forecast

- Primary key: `id`
- Foreign keys:
  - `feature_snapshot_id` → `feature_snapshots.id`
- Indexes:
  - `ix_forecasts_lookup` (crop_code, target_code, geo_code, issue_time)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `crop_code` | VARCHAR(60) | NOT NULL |  |
| `target_code` | VARCHAR(80) | NOT NULL |  |
| `geo_code` | VARCHAR(64) | NOT NULL |  |
| `horizon_days` | Integer | NOT NULL |  |
| `issue_time` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL |  |
| `valid_from` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL |  |
| `valid_to` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL |  |
| `risk_band` | VARCHAR(30) | NOT NULL |  |
| `probability` | Numeric | NULL |  |
| `confidence_band` | VARCHAR(20) | NOT NULL | python default |
| `coverage` | VARCHAR(20) | NOT NULL | python default |
| `coverage_detail` | JSON | NOT NULL | python default |
| `drivers` | JSON | NOT NULL | python default |
| `reason_code` | VARCHAR(60) | NULL |  |
| `model_version` | VARCHAR(80) | NOT NULL |  |
| `feature_snapshot_id` | VARCHAR(64) | NULL |  |
| `boundary_version` | VARCHAR(60) | NULL |  |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `geo_observations` — backend/app/geo/models.py :: GeoObservation

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_geo_observations_crop_code` (crop_code)
  - `ix_geo_observations_event_date` (event_date)
  - `ix_geo_observations_geo_code` (geo_code)
  - `ix_geo_observations_h3_cell_id` (h3_cell_id)
  - `ix_geo_observations_observation_id` (observation_id)
  - `ix_geo_observations_target_code` (target_code)
  - `ix_geo_observations_verification_status` (verification_status)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `observation_id` | VARCHAR(64) | NULL | indexed |
| `h3_cell_id` | VARCHAR(32) | NOT NULL | indexed |
| `resolution` | Integer | NOT NULL |  |
| `geo_code` | VARCHAR(64) | NOT NULL | indexed |
| `crop_code` | VARCHAR(60) | NOT NULL | indexed |
| `target_code` | VARCHAR(80) | NOT NULL | indexed |
| `event_date` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | indexed |
| `reported_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `reporter_type` | VARCHAR(30) | NOT NULL |  |
| `verification_status` | VARCHAR(30) | NOT NULL | indexed; python default |
| `severity` | VARCHAR(30) | NULL |  |
| `ai_confidence` | Numeric | NULL |  |
| `ai_model_version` | VARCHAR(80) | NULL |  |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `geographies` — backend/app/db/models.py :: Geography

- Primary key: `id`
- Foreign keys: none
- Unique constraints:
  - `uq_geographies_code` (code)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `code` | VARCHAR(64) | NOT NULL | UNIQUE |
| `level` | VARCHAR(30) | NOT NULL |  |
| `name` | VARCHAR(200) | NOT NULL |  |
| `parent_code` | VARCHAR(64) | NULL |  |
| `boundary_version` | VARCHAR(60) | NOT NULL | python default |
| `valid_from` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `valid_to` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |

### `growing_areas` — backend/app/db/models.py :: GrowingArea

- Primary key: `id`
- Foreign keys:
  - `owner_user_id` → `users.id`
- Indexes:
  - `ix_growing_areas_geo_code` (geo_code)
  - `ix_growing_areas_owner_user_id` (owner_user_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `owner_user_id` | VARCHAR(64) | NOT NULL | indexed |
| `geo_code` | VARCHAR(64) | NOT NULL | indexed |
| `precision` | VARCHAR(20) | NOT NULL | python default |
| `label` | VARCHAR(200) | NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `h3_cells` — backend/app/geo/models.py :: H3Cell

- Primary key: `id`
- Foreign keys: none
- Unique constraints:
  - `uq_h3_cells_cell_id` (cell_id)
- Indexes:
  - `ix_h3_cells_cell_id` (cell_id)
  - `ix_h3_cells_parent_cell_id` (parent_cell_id)
  - `ix_h3_cells_resolution` (resolution)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `cell_id` | VARCHAR(32) | NOT NULL | UNIQUE; indexed |
| `resolution` | Integer | NOT NULL | indexed |
| `center_lat` | Numeric | NOT NULL |  |
| `center_lng` | Numeric | NOT NULL |  |
| `area_m2` | Numeric | NOT NULL |  |
| `boundary_geojson` | JSON | NOT NULL |  |
| `parent_cell_id` | VARCHAR(32) | NULL | indexed |
| `is_active` | Boolean | NOT NULL | python default |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `hotspot_clusters` — backend/app/geo/models.py :: HotspotCluster

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_hotspot_clusters_classification` (classification)
  - `ix_hotspot_clusters_crop_code` (crop_code)
  - `ix_hotspot_clusters_h3_cell_id` (h3_cell_id)
  - `ix_hotspot_clusters_target_code` (target_code)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `h3_cell_id` | VARCHAR(32) | NOT NULL | indexed |
| `resolution` | Integer | NOT NULL |  |
| `target_type` | VARCHAR(30) | NOT NULL |  |
| `target_code` | VARCHAR(80) | NOT NULL | indexed |
| `crop_code` | VARCHAR(60) | NULL | indexed |
| `classification` | VARCHAR(20) | NOT NULL | indexed; python default |
| `score` | Numeric | NOT NULL | python default |
| `total_reports` | Integer | NOT NULL | python default |
| `unique_affected_farms` | Integer | NOT NULL | python default |
| `verified_farms` | Integer | NOT NULL | python default |
| `unverified_reports` | Integer | NOT NULL | python default |
| `pending_reviews` | Integer | NOT NULL | python default |
| `severity_distribution` | JSON | NOT NULL | python default |
| `first_reported` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `most_recent_report` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `historical_frequency` | Numeric | NOT NULL | python default |
| `weather_risk_factor` | Numeric | NULL |  |
| `neighbor_cells` | JSON | NOT NULL | python default |
| `calculated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `hotspot_history` — backend/app/geo/models.py :: HotspotHistory

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_hotspot_hist_cell` (h3_cell_id)
  - `ix_hotspot_hist_date` (snapshot_date)
  - `ix_hotspot_hist_target` (target_code)
  - `ix_hotspot_history_h3_cell_id` (h3_cell_id)
  - `ix_hotspot_history_snapshot_date` (snapshot_date)
  - `ix_hotspot_history_target_code` (target_code)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `h3_cell_id` | VARCHAR(32) | NOT NULL | indexed |
| `target_type` | VARCHAR(30) | NOT NULL |  |
| `target_code` | VARCHAR(80) | NOT NULL | indexed |
| `snapshot_date` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | indexed |
| `classification` | VARCHAR(20) | NOT NULL |  |
| `score` | Numeric | NOT NULL | python default |
| `unique_affected_farms` | Integer | NOT NULL | python default |
| `weather_risk_factor` | Numeric | NULL |  |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `idempotency_records` — backend/app/db/models.py :: IdempotencyRecord

- Primary key: `id`
- Foreign keys:
  - `user_id` → `users.id`
- Unique constraints:
  - `uq_idempotency_user_scope_key` (user_id, scope, key)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `user_id` | VARCHAR(64) | NOT NULL |  |
| `scope` | VARCHAR(80) | NOT NULL |  |
| `key` | VARCHAR(200) | NOT NULL |  |
| `request_hash` | VARCHAR(128) | NULL |  |
| `entity_id` | VARCHAR(64) | NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `image_assets` — backend/app/db/models.py :: ImageAsset

- Primary key: `id`
- Foreign keys:
  - `observation_id` → `observations.id`
- Indexes:
  - `ix_image_assets_hash` (content_hash)
  - `ix_image_assets_observation_id` (observation_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `observation_id` | VARCHAR(64) | NOT NULL | indexed |
| `storage_key` | VARCHAR(400) | NOT NULL |  |
| `original_width` | Integer | NULL |  |
| `original_height` | Integer | NULL |  |
| `bytes` | Integer | NULL |  |
| `content_hash` | VARCHAR(128) | NULL |  |
| `mime` | VARCHAR(80) | NOT NULL |  |
| `source` | VARCHAR(20) | NOT NULL | python default |
| `compression` | JSON | NOT NULL | python default |
| `upload_status` | VARCHAR(20) | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `image_predictions` — backend/app/db/models.py :: ImagePrediction

- Primary key: `id`
- Foreign keys:
  - `image_id` → `image_assets.id`
- Indexes:
  - `ix_image_predictions_image_id` (image_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `image_id` | VARCHAR(64) | NOT NULL | indexed |
| `model_version` | VARCHAR(80) | NOT NULL |  |
| `candidates` | JSON | NOT NULL | python default |
| `confidence_band` | VARCHAR(20) | NULL |  |
| `calibrated` | Boolean | NOT NULL | python default |
| `abstained` | Boolean | NOT NULL | python default |
| `abstain_reason` | VARCHAR(60) | NULL |  |
| `quality_flags` | JSON | NOT NULL | python default |
| `is_demo` | Boolean | NOT NULL | python default |
| `generated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `image_quality_results` — backend/app/db/models.py :: ImageQualityResult

- Primary key: `id`
- Foreign keys:
  - `image_id` → `image_assets.id`
- Indexes:
  - `ix_image_quality_results_image_id` (image_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `image_id` | VARCHAR(64) | NOT NULL | indexed |
| `gate_version` | VARCHAR(80) | NOT NULL |  |
| `result` | VARCHAR(20) | NOT NULL |  |
| `flags` | JSON | NOT NULL | python default |
| `thresholds` | JSON | NOT NULL | python default |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `image_uploads` — backend/app/modules/conversations/orm.py :: ImageUploadRow

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_image_uploads_owner_id` (owner_id)
  - `ix_image_uploads_sha256` (sha256)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK |
| `owner_id` | VARCHAR(64) | NOT NULL | indexed |
| `filename` | VARCHAR(255) | NOT NULL |  |
| `content_type` | VARCHAR(100) | NOT NULL |  |
| `size_bytes` | Integer | NOT NULL |  |
| `sha256` | VARCHAR(64) | NOT NULL | indexed |
| `storage_path` | VARCHAR(512) | NOT NULL |  |
| `width` | Integer | NOT NULL |  |
| `height` | Integer | NOT NULL |  |
| `laplacian_variance` | Float | NOT NULL |  |
| `mean_luma` | Float | NOT NULL |  |
| `clipped_fraction` | Float | NOT NULL |  |
| `plant_presence` | Float | NOT NULL |  |
| `quality_result` | VARCHAR(32) | NOT NULL |  |
| `quality_flags` | JSON | NULL |  |
| `quality_gate_version` | VARCHAR(80) | NOT NULL |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | server_default=now() |

### `inspection_results` — backend/app/geo/models.py :: InspectionResult

- Primary key: `id`
- Foreign keys:
  - `task_id` → `inspection_tasks.id` ON DELETE CASCADE
- Indexes:
  - `ix_inspection_cell` (h3_cell_id)
  - `ix_inspection_results_h3_cell_id` (h3_cell_id)
  - `ix_inspection_results_task_id` (task_id)
  - `ix_inspection_task` (task_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `task_id` | VARCHAR(64) | NOT NULL | indexed |
| `h3_cell_id` | VARCHAR(32) | NOT NULL | indexed |
| `inspected_by` | VARCHAR(64) | NOT NULL |  |
| `inspection_date` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `crop_code` | VARCHAR(60) | NOT NULL |  |
| `target_code` | VARCHAR(80) | NOT NULL |  |
| `found_issue` | Boolean | NOT NULL | python default |
| `severity` | VARCHAR(30) | NULL |  |
| `ai_confidence` | Numeric | NULL |  |
| `symptoms_observed` | Text | NULL |  |
| `photos_taken` | Integer | NOT NULL | python default |
| `videos_taken` | Integer | NOT NULL | python default |
| `farmer_notified` | Boolean | NOT NULL | python default |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `inspection_tasks` — backend/app/geo/models.py :: InspectionTask

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_inspection_tasks_assigned_to` (assigned_to)
  - `ix_inspection_tasks_crop_code` (crop_code)
  - `ix_inspection_tasks_deadline` (deadline)
  - `ix_inspection_tasks_expires_at` (expires_at)
  - `ix_inspection_tasks_h3_cell_id` (h3_cell_id)
  - `ix_inspection_tasks_priority` (priority)
  - `ix_inspection_tasks_status` (status)
  - `ix_inspection_tasks_target_code` (target_code)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `h3_cell_id` | VARCHAR(32) | NOT NULL | indexed |
| `resolution` | Integer | NOT NULL |  |
| `crop_code` | VARCHAR(60) | NOT NULL | indexed |
| `target_code` | VARCHAR(80) | NOT NULL | indexed |
| `task_type` | VARCHAR(30) | NOT NULL |  |
| `priority` | VARCHAR(20) | NOT NULL | indexed; python default |
| `status` | VARCHAR(30) | NOT NULL | indexed; python default |
| `assigned_to` | VARCHAR(64) | NULL | indexed |
| `assigned_by` | VARCHAR(64) | NULL |  |
| `assignment_type` | VARCHAR(20) | NOT NULL | python default |
| `deadline` | TIMESTAMP (naive UTC via UTCDateTime) | NULL | indexed |
| `expires_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL | indexed |
| `suspected_issue` | Text | NULL |  |
| `crop_growth_stage` | VARCHAR(50) | NULL |  |
| `inspection_instructions` | Text | NULL |  |
| `max_distance_km` | Numeric | NULL |  |
| `required_expertise` | JSON | NOT NULL | python default |
| `created_by` | VARCHAR(64) | NOT NULL |  |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `message_attachments` — backend/app/db/models.py :: MessageAttachment

- Primary key: `id`
- Foreign keys:
  - `image_id` → `image_assets.id`
  - `message_id` → `messages.id`
- Indexes:
  - `ix_message_attachments_message_id` (message_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `message_id` | VARCHAR(64) | NOT NULL | indexed |
| `image_id` | VARCHAR(64) | NOT NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `message_events` — backend/app/modules/conversations/orm.py :: MessageEventRow

- Primary key: `id`
- Foreign keys:
  - `conversation_id` → `conversations.id` ON DELETE CASCADE
  - `message_id` → `messages.id` ON DELETE CASCADE
- Indexes:
  - `ix_message_events_conversation_id` (conversation_id)
  - `ix_message_events_message_id` (message_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK |
| `conversation_id` | VARCHAR(64) | NOT NULL | indexed |
| `message_id` | VARCHAR(64) | NOT NULL | indexed |
| `event_type` | VARCHAR(48) | NOT NULL |  |
| `detail` | JSON | NULL |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | server_default=now() |

### `messages` — backend/app/modules/conversations/orm.py :: MessageRow

- Primary key: `id`
- Foreign keys:
  - `conversation_id` → `conversations.id` ON DELETE CASCADE
- Unique constraints:
  - `uq_messages_conversation_client` (conversation_id, client_message_id)
- Indexes:
  - `ix_messages_conversation_id` (conversation_id)
  - `ix_messages_turn_id` (turn_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK |
| `conversation_id` | VARCHAR(64) | NOT NULL | indexed |
| `role` | VARCHAR(16) | NOT NULL |  |
| `kind` | VARCHAR(32) | NOT NULL |  |
| `text` | Text | NULL |  |
| `client_message_id` | VARCHAR(128) | NULL |  |
| `turn_id` | VARCHAR(128) | NULL | indexed |
| `observation_id` | VARCHAR(64) | NULL |  |
| `assessment` | JSON | NULL |  |
| `image` | JSON | NULL |  |
| `next_steps` | JSON | NULL |  |
| `is_demo` | Boolean | NOT NULL | python default |
| `sequence` | Integer | NOT NULL | python default |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | server_default=now() |

### `model_registry` — backend/app/db/models.py :: ModelRegistry

- Primary key: `id`
- Foreign keys: none
- Unique constraints:
  - `uq_model_kind_version` (kind, version)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `kind` | VARCHAR(40) | NOT NULL |  |
| `version` | VARCHAR(80) | NOT NULL |  |
| `artefact_key` | VARCHAR(400) | NULL |  |
| `checksum` | VARCHAR(128) | NULL |  |
| `metrics` | JSON | NOT NULL | python default |
| `status` | VARCHAR(20) | NOT NULL | python default |
| `approved_by` | VARCHAR(64) | NULL |  |
| `approved_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `notification_preferences` — backend/app/db/models.py :: NotificationPreference

- Primary key: `id`
- Foreign keys:
  - `user_id` → `users.id`
- Unique constraints:
  - `uq_notification_pref` (user_id, channel, target_code)
- Indexes:
  - `ix_notification_preferences_user_id` (user_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `user_id` | VARCHAR(64) | NOT NULL | indexed |
| `channel` | VARCHAR(20) | NOT NULL |  |
| `target_code` | VARCHAR(80) | NULL |  |
| `enabled` | Boolean | NOT NULL | python default |
| `quiet_start` | VARCHAR(5) | NULL |  |
| `quiet_end` | VARCHAR(5) | NULL |  |
| `language` | VARCHAR(10) | NOT NULL | python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `observation_verification` — backend/app/db/models.py :: ObservationVerification

- Primary key: `observation_id`
- Foreign keys:
  - `observation_id` → `observations.id`
  - `review_id` → `reviews.id`
  - `verified_by` → `users.id`

| Column | Type | Null | Notes |
|---|---|---|---|
| `observation_id` | VARCHAR(64) | NOT NULL | PK |
| `status` | VARCHAR(30) | NOT NULL | python default |
| `evidence_tier` | VARCHAR(30) | NOT NULL | python default |
| `verified_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `verified_by` | VARCHAR(64) | NULL |  |
| `review_id` | VARCHAR(64) | NULL |  |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `observations` — backend/app/db/models.py :: Observation

- Primary key: `id`
- Foreign keys:
  - `crop_code` → `crops.code`
  - `growing_area_id` → `growing_areas.id`
  - `subject_user_id` → `users.id`
  - `user_id` → `users.id`
- Unique constraints:
  - `uq_observation_client` (user_id, client_report_id)
- Indexes:
  - `ix_observations_area_status` (area_code, status, created_at)
  - `ix_observations_user_created` (user_id, created_at)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `client_report_id` | VARCHAR(128) | NOT NULL |  |
| `user_id` | VARCHAR(64) | NOT NULL |  |
| `subject_user_id` | VARCHAR(64) | NULL |  |
| `growing_area_id` | VARCHAR(64) | NULL |  |
| `area_code` | VARCHAR(64) | NOT NULL |  |
| `crop_code` | VARCHAR(60) | NOT NULL |  |
| `variety` | VARCHAR(120) | NULL |  |
| `growth_stage` | VARCHAR(40) | NULL |  |
| `notes` | Text | NULL |  |
| `captured_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `submitted_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `status` | VARCHAR(30) | NOT NULL | python default |
| `is_demo` | Boolean | NOT NULL | python default |
| `deleted_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `otp_codes` — backend/app/db/models.py :: OtpCode

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_otp_phone_created` (phone_e164, created_at)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `phone_e164` | VARCHAR(20) | NOT NULL |  |
| `code_hash` | VARCHAR(128) | NOT NULL |  |
| `attempts` | Integer | NOT NULL | python default |
| `expires_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL |  |
| `consumed_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `pest_reports` — backend/app/geo/models.py :: PestReport

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_pest_reports_crop_code` (crop_code)
  - `ix_pest_reports_event_date` (event_date)
  - `ix_pest_reports_h3_cell_id` (h3_cell_id)
  - `ix_pest_reports_target_code` (target_code)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `h3_cell_id` | VARCHAR(32) | NOT NULL | indexed |
| `resolution` | Integer | NOT NULL |  |
| `crop_code` | VARCHAR(60) | NOT NULL | indexed |
| `target_code` | VARCHAR(80) | NOT NULL | indexed |
| `event_date` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | indexed |
| `report_date` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `report_source` | VARCHAR(50) | NOT NULL |  |
| `case_count` | Integer | NOT NULL | python default |
| `unique_farms` | Integer | NOT NULL | python default |
| `verified_farms` | Integer | NOT NULL | python default |
| `severity_distribution` | JSON | NOT NULL | python default |
| `avg_ai_confidence` | Numeric | NULL |  |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `recovery_monitoring_records` — backend/app/geo/models.py :: RecoveryMonitoringRecord

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_recovery_monitoring_records_farm_id` (farm_id)
  - `ix_recovery_monitoring_records_follow_up_date` (follow_up_date)
  - `ix_recovery_monitoring_records_h3_cell_id` (h3_cell_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `farm_id` | VARCHAR(64) | NOT NULL | indexed |
| `h3_cell_id` | VARCHAR(32) | NOT NULL | indexed |
| `crop_code` | VARCHAR(60) | NOT NULL |  |
| `target_code` | VARCHAR(80) | NOT NULL |  |
| `previous_severity` | VARCHAR(30) | NOT NULL |  |
| `current_severity` | VARCHAR(30) | NOT NULL |  |
| `recovery_percentage` | Numeric | NOT NULL | python default |
| `recovery_status` | VARCHAR(30) | NOT NULL | python default |
| `follow_up_date` | TIMESTAMP (naive UTC via UTCDateTime) | NULL | indexed |
| `notes` | Text | NULL |  |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `regional_risk_scores` — backend/app/geo/models.py :: RegionalRiskScore

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_regional_risk_scores_crop_code` (crop_code)
  - `ix_regional_risk_scores_h3_cell_id` (h3_cell_id)
  - `ix_regional_risk_scores_target_code` (target_code)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `h3_cell_id` | VARCHAR(32) | NOT NULL | indexed |
| `resolution` | Integer | NOT NULL |  |
| `crop_code` | VARCHAR(60) | NOT NULL | indexed |
| `target_code` | VARCHAR(80) | NOT NULL | indexed |
| `valid_from` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL |  |
| `valid_to` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL |  |
| `risk_score` | Numeric | NOT NULL | python default |
| `weather_risk` | Numeric | NOT NULL | python default |
| `biological_risk` | Numeric | NOT NULL | python default |
| `historical_risk` | Numeric | NOT NULL | python default |
| `risk_label` | VARCHAR(20) | NOT NULL | python default |
| `contributing_factors` | JSON | NOT NULL | python default |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `review_assignments` — backend/app/db/models.py :: ReviewAssignment

- Primary key: `id`
- Foreign keys:
  - `observation_id` → `observations.id`
  - `user_id` → `users.id`
- Indexes:
  - `ix_review_assignments_observation_id` (observation_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `observation_id` | VARCHAR(64) | NOT NULL | indexed |
| `user_id` | VARCHAR(64) | NOT NULL |  |
| `area_code` | VARCHAR(64) | NOT NULL |  |
| `assigned_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `expires_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL |  |

### `review_events` — backend/app/db/models.py :: ReviewEvent

- Primary key: `id`
- Foreign keys:
  - `actor_id` → `users.id`
  - `observation_id` → `observations.id`
- Indexes:
  - `ix_review_events_observation` (observation_id, created_at)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `observation_id` | VARCHAR(64) | NOT NULL |  |
| `from_status` | VARCHAR(30) | NULL |  |
| `to_status` | VARCHAR(30) | NOT NULL |  |
| `actor_id` | VARCHAR(64) | NULL |  |
| `reason` | Text | NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `review_evidence` — backend/app/db/models.py :: ReviewEvidence

- Primary key: `id`
- Foreign keys:
  - `review_id` → `reviews.id`
- Indexes:
  - `ix_review_evidence_review_id` (review_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `review_id` | VARCHAR(64) | NOT NULL | indexed |
| `type` | VARCHAR(40) | NOT NULL |  |
| `value` | Text | NOT NULL |  |
| `source` | VARCHAR(120) | NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `review_requests` — backend/app/db/models.py :: ReviewRequest (observation queue)

- Primary key: `id`
- Foreign keys:
  - `observation_id` → `observations.id`
  - `requested_by` → `users.id`
- Indexes:
  - `ix_review_requests_observation_id` (observation_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `observation_id` | VARCHAR(64) | NOT NULL | indexed |
| `requested_by` | VARCHAR(64) | NOT NULL |  |
| `reason` | VARCHAR(300) | NULL |  |
| `status` | VARCHAR(30) | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `reviews` — backend/app/db/models.py :: Review

- Primary key: `id`
- Foreign keys:
  - `observation_id` → `observations.id`
  - `reviewer_id` → `users.id`
- Indexes:
  - `ix_reviews_observation_created` (observation_id, created_at)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `observation_id` | VARCHAR(64) | NOT NULL |  |
| `reviewer_id` | VARCHAR(64) | NOT NULL |  |
| `decision` | VARCHAR(30) | NOT NULL |  |
| `reason_code` | VARCHAR(60) | NULL |  |
| `corrected_label` | VARCHAR(80) | NULL |  |
| `severity` | VARCHAR(30) | NULL |  |
| `note` | Text | NULL |  |
| `duplicate_of` | VARCHAR(64) | NULL |  |
| `client_request_id` | VARCHAR(128) | NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `roles` — backend/app/db/models.py :: Role

- Primary key: `code`
- Foreign keys: none

| Column | Type | Null | Notes |
|---|---|---|---|
| `code` | VARCHAR(40) | NOT NULL | PK |
| `description` | VARCHAR(255) | NOT NULL |  |

### `sessions` — backend/app/db/models.py :: Session

- Primary key: `id`
- Foreign keys:
  - `user_id` → `users.id`
- Unique constraints:
  - `uq_sessions_refresh_hash` (refresh_hash)
- Indexes:
  - `ix_sessions_family_id` (family_id)
  - `ix_sessions_user_family` (user_id, family_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `user_id` | VARCHAR(64) | NOT NULL |  |
| `refresh_hash` | VARCHAR(128) | NOT NULL | UNIQUE |
| `family_id` | VARCHAR(64) | NOT NULL | indexed |
| `token_version` | Integer | NOT NULL | python default |
| `expires_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL |  |
| `revoked_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `ip_hash` | VARCHAR(128) | NULL |  |
| `user_agent` | VARCHAR(400) | NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `system_configs` — backend/app/db/models.py :: SystemConfig

- Primary key: `key`
- Foreign keys: none

| Column | Type | Null | Notes |
|---|---|---|---|
| `key` | VARCHAR(120) | NOT NULL | PK |
| `value` | JSON | NOT NULL | python default |
| `updated_by` | VARCHAR(64) | NULL |  |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |

### `targets` — backend/app/db/models.py :: Target

- Primary key: `id`
- Foreign keys:
  - `crop_code` → `crops.code`
- Unique constraints:
  - `uq_target_crop_code` (crop_code, code)
- Indexes:
  - `ix_targets_crop_code` (crop_code)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `crop_code` | VARCHAR(60) | NOT NULL | indexed |
| `code` | VARCHAR(80) | NOT NULL |  |
| `name` | VARCHAR(200) | NOT NULL |  |
| `kind` | VARCHAR(30) | NOT NULL |  |
| `supported` | Boolean | NOT NULL | python default |
| `forecast_eligible` | Boolean | NOT NULL | python default |
| `taxonomy_note` | Text | NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `task_assignments` — backend/app/geo/models.py :: TaskAssignment

- Primary key: `id`
- Foreign keys:
  - `task_id` → `inspection_tasks.id` ON DELETE CASCADE
- Indexes:
  - `ix_task_assign_at` (assigned_at)
  - `ix_task_assign_task` (task_id)
  - `ix_task_assign_user` (user_id)
  - `ix_task_assignments_task_id` (task_id)
  - `ix_task_assignments_user_id` (user_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `task_id` | VARCHAR(64) | NOT NULL | indexed |
| `user_id` | VARCHAR(64) | NOT NULL | indexed |
| `assigned_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `assigned_by` | VARCHAR(64) | NOT NULL |  |
| `assignment_type` | VARCHAR(20) | NOT NULL |  |
| `accepted_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `declined_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `completed_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `distance_km` | Numeric | NULL |  |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `task_status_history` — backend/app/geo/models.py :: TaskStatusHistory

- Primary key: `id`
- Foreign keys:
  - `task_id` → `inspection_tasks.id` ON DELETE CASCADE
- Indexes:
  - `ix_task_hist_at` (created_at)
  - `ix_task_hist_task` (task_id)
  - `ix_task_status_history_task_id` (task_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `task_id` | VARCHAR(64) | NOT NULL | indexed |
| `from_status` | VARCHAR(30) | NULL |  |
| `to_status` | VARCHAR(30) | NOT NULL |  |
| `changed_by` | VARCHAR(64) | NOT NULL |  |
| `reason` | Text | NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `is_demo` | Boolean | NOT NULL | python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `user_area_assignments` — backend/app/db/models.py :: UserAreaAssignment

- Primary key: `id`
- Foreign keys:
  - `user_id` → `users.id`
- Indexes:
  - `ix_area_assignments_user_active` (user_id, active_to)
  - `ix_user_area_assignments_geo_code` (geo_code)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `user_id` | VARCHAR(64) | NOT NULL |  |
| `geo_code` | VARCHAR(64) | NOT NULL | indexed |
| `level` | VARCHAR(30) | NOT NULL | python default |
| `active_from` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `active_to` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |

### `user_permissions` — backend/app/db/models.py :: UserPermission

- Primary key: `id`
- Foreign keys:
  - `user_id` → `users.id`
- Indexes:
  - `ix_user_permissions_user_active` (user_id, revoked_at)
  - `ix_user_permissions_user_id` (user_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `user_id` | VARCHAR(64) | NOT NULL | indexed |
| `permission` | VARCHAR(60) | NOT NULL |  |
| `granted_by` | VARCHAR(64) | NULL |  |
| `granted_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `revoked_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |

### `user_roles` — backend/app/db/models.py :: UserRole

- Primary key: `id`
- Foreign keys:
  - `role_code` → `roles.code`
  - `user_id` → `users.id`
- Indexes:
  - `ix_user_roles_user_active` (user_id, revoked_at)
  - `ix_user_roles_user_id` (user_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `user_id` | VARCHAR(64) | NOT NULL | indexed |
| `role_code` | VARCHAR(40) | NOT NULL |  |
| `granted_by` | VARCHAR(64) | NULL |  |
| `granted_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `revoked_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |

### `user_task_availability` — backend/app/geo/models.py :: UserTaskAvailability

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_user_task_availability_user_id` (user_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `user_id` | VARCHAR(64) | NOT NULL | indexed |
| `available_from` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL |  |
| `available_to` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL |  |
| `max_distance_km` | Numeric | NULL |  |
| `preferred_crop_codes` | JSON | NOT NULL | python default |
| `preferred_target_codes` | JSON | NOT NULL | python default |
| `is_active` | Boolean | NOT NULL | python default |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `users` — backend/app/db/models.py :: User

- Primary key: `id`
- Foreign keys: none
- Unique constraints:
  - `uq_users_phone_e164` (phone_e164)
  - `uq_users_email` (email)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `phone_e164` | VARCHAR(20) | NULL | UNIQUE |
| `email` | VARCHAR(320) | NULL | UNIQUE |
| `display_name` | VARCHAR(200) | NULL |  |
| `password_hash` | VARCHAR(255) | NULL |  |
| `status` | VARCHAR(20) | NOT NULL | python default |
| `locale` | VARCHAR(10) | NOT NULL | python default |
| `active_role` | VARCHAR(40) | NOT NULL | python default |
| `token_version` | Integer | NOT NULL | python default |
| `mfa_secret` | VARCHAR(64) | NULL |  |
| `failed_login_count` | Integer | NOT NULL | python default |
| `failed_login_first_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `locked_until` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `deleted_at` | TIMESTAMP (naive UTC via UTCDateTime) | NULL |  |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `video_readings` — backend/app/modules/video/orm.py :: VideoReadingRow

- Primary key: `id`
- Foreign keys:
  - `video_id` → `video_uploads.id` ON DELETE CASCADE
- Indexes:
  - `ix_video_readings_owner_id` (owner_id)
  - `ix_video_readings_video_id` (video_id)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK |
| `video_id` | VARCHAR(64) | NOT NULL | indexed |
| `owner_id` | VARCHAR(64) | NOT NULL | indexed |
| `state` | VARCHAR(32) | NOT NULL |  |
| `reason_code` | VARCHAR(64) | NULL |  |
| `error_code` | VARCHAR(64) | NULL |  |
| `summary_text` | Text | NOT NULL |  |
| `summary` | JSON | NULL |  |
| `frames` | JSON | NULL |  |
| `engine_version` | VARCHAR(120) | NOT NULL |  |
| `detector_version` | VARCHAR(80) | NOT NULL |  |
| `tracker_version` | VARCHAR(80) | NOT NULL |  |
| `is_demo` | Boolean | NOT NULL | python default |
| `calibrated` | Boolean | NOT NULL | python default |
| `generated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | server_default=now() |

### `video_uploads` — backend/app/modules/video/orm.py :: VideoUploadRow

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_video_uploads_owner_id` (owner_id)
  - `ix_video_uploads_sha256` (sha256)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK |
| `owner_id` | VARCHAR(64) | NOT NULL | indexed |
| `filename` | VARCHAR(255) | NOT NULL |  |
| `content_type` | VARCHAR(100) | NOT NULL |  |
| `size_bytes` | Integer | NOT NULL |  |
| `sha256` | VARCHAR(64) | NOT NULL | indexed |
| `storage_path` | VARCHAR(512) | NOT NULL |  |
| `duration_ms` | Integer | NOT NULL |  |
| `width` | Integer | NOT NULL |  |
| `height` | Integer | NOT NULL |  |
| `fps` | Float | NOT NULL |  |
| `frame_count` | Integer | NOT NULL |  |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | server_default=now() |
| `deleted_at` | TIMESTAMP WITH TIME ZONE | NULL |  |

### `weather_cell_records` — backend/app/geo/models.py :: WeatherCellRecord

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_weather_cell_records_expires_at` (expires_at)
  - `ix_weather_cell_records_h3_cell_id` (h3_cell_id)
  - `ix_weather_cell_records_source_timestamp` (source_timestamp)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `h3_cell_id` | VARCHAR(32) | NOT NULL | indexed |
| `resolution` | Integer | NOT NULL |  |
| `source` | VARCHAR(80) | NOT NULL |  |
| `source_timestamp` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | indexed |
| `fetched_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `expires_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | indexed |
| `variables` | JSON | NOT NULL | python default |
| `completeness` | Numeric | NOT NULL | python default |
| `is_stale` | Boolean | NOT NULL | python default |
| `is_demo` | Boolean | NOT NULL | python default |
| `created_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |
| `updated_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | server_default=now(); python default |

### `weather_snapshots` — backend/app/db/models.py :: WeatherSnapshot

- Primary key: `id`
- Foreign keys: none
- Indexes:
  - `ix_weather_geo_source` (geo_code, source_timestamp)

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | VARCHAR(64) | NOT NULL | PK; python default |
| `geo_code` | VARCHAR(64) | NOT NULL |  |
| `source` | VARCHAR(80) | NOT NULL |  |
| `source_timestamp` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL |  |
| `fetched_at` | TIMESTAMP (naive UTC via UTCDateTime) | NOT NULL | python default |
| `variables` | JSON | NOT NULL | python default |
| `completeness` | Numeric | NOT NULL | python default |
| `is_stale` | Boolean | NOT NULL | python default |
| `is_demo` | Boolean | NOT NULL | python default |

## 2. Type mapping decisions (ORM → PostgreSQL)

- `String(n)` → `VARCHAR(n)`. No `TEXT` upgrade except ORM `Text` columns.
- IDs are `String(64)` app-generated (`usr_…`, `conv_…`); they stay
  `VARCHAR(64)`, **not** `UUID`. Regenerating as UUID would orphan every FK.
- `UTCDateTime` (TypeDecorator over `DateTime`) → `TIMESTAMP WITHOUT TIME ZONE`
  on PostgreSQL, storing naive UTC; Python returns aware UTC. Chat/video
  tables use `DateTime(timezone=True)` → `TIMESTAMPTZ`. This mixed
  semantics are preserved as-is; unifying to TIMESTAMPTZ needs a data
  migration and is an open decision (not done here).
- `JSON` → `JSON` on PostgreSQL (SQLAlchemy portable type). 26 columns
  are JSON. Upgrading to `JSONB` (indexing, containment) needs an ORM
  variant change first — not done here; see Phase 3 rationale.
- `Numeric(4,3)` / `Numeric(6,5)` → `NUMERIC`. Python `default=` values
  are client-side and have **no** server defaults in migrations.
- Only 16 columns have `server_default=now()` (TimestampMixin + chat/video
  `created_at`/`updated_at`/`generated_at`). Everything else is a
  Python-side default — migrations intentionally emit no server default.
- `Float` → `DOUBLE PRECISION` (quality metrics). `Boolean` → `BOOLEAN`.
- `ON DELETE CASCADE` only on chat/video FKs (5+1). All other FKs are
  `NO ACTION` (ORM default). Deletion semantics are service-enforced.

## 3. PostGIS (zero spatial columns — deliberate)

The backend ORM has **zero** geometry/geography columns. `models.py`
states this explicitly: the pilot API only serves block/mandal
aggregates and geometry arrives when boundary data is approved. Migration
`0004` therefore enables the `postgis` extension but adds no spatial
columns or GiST indexes. The `database/schema/01-schema.sql` reference
schema **does** declare `geographies.geom MultiPolygon(4326)`,
`growing_areas.geom`, `observations.geom Point(4326)` — that geometry is
a documented drift (§4), not recreated here. Adding ORM geometry now
would invent SRIDs/dimensionality the app never approved.

## 4. Reconciliation: backend vs `database/` reference

| Area | Backend ORM (authority) | `database/schema/01-schema.sql` (reference) |
|---|---|---|
| Tables | 50 (`app.db.models` + chat/video ORMs) | 40 (subset; `historical_occurrences` etc. exist only there) |
| PKs | `VARCHAR(64)` app ids | `UUID DEFAULT gen_random_uuid()` |
| Timestamps | mixed naive/aware (see §2) | `timestamptz` |
| JSON | `JSON` | `jsonb` |
| Closed sets | `VARCHAR` + service checks | `text + CHECK` |
| Geometry | none | `geometry(...,4326)` ×3 |
| Append-only | service code only | `reject_mutation()` triggers ×13 |
| Migrations | Alembic 0001→0004 (backend) | `database/alembic/0001,0002` (reference) |

**Authority:** backend Alembic (`backend/app/db/migrations`, `env.py` loads
`app.db.models`) is the single operational migration system (ADR-002).
`database/` SQL/history are **reference only** (its own header says so:
“must never be applied to production by hand”). Never run both histories
against the same database. The backend schema is a portable subset that
runs on SQLite for dev/tests and PostgreSQL for deployment; reference
features (triggers, geometry, historical_occurrences) need explicit ORM
parcels + migrations before they exist in the deployment.

## 5. Models without database tables

None. Every ORM model maps to one table. All association columns
(`user_roles`, `user_permissions`, etc.) are full tables, not.
