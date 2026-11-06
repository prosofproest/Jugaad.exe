# CropSentinel AI — Master Database Schema Reference

**Authority:** CropSentinel AI Master Specification
**Database Engine:** PostgreSQL 16+ with PostGIS 3.x and pgvector
**ORM:** SQLAlchemy 2.0
**Migration Manager:** Alembic

---

## Summary Metrics
- **Total Database Domains:** 11
- **Total Implemented Tables:** 76
- **Spatial Geometries Enabled:** 13 tables (Point, Polygon, MultiPolygon)
- **Spatial Indexes:** 13 GiST Indexes
- **Append-Only Immutable Tables:** 3 (`ai_predictions`, `outbreak_predictions`, `risk_history`)
- **Primary Key Convention:** UUID (v4) with `gen_random_uuid()`
- **Timestamp Convention:** UTC `timestamptz` with `created_at` and `updated_at` triggers
- **Storage Policy:** Binary files strictly stored in Object Storage (S3/GCS); metadata & keys in PostgreSQL

---

## User Database

### Table: `users`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `username` | `VARCHAR(64)` | NULL | Field `username` |
| `email` | `VARCHAR(320)` | NULL | Field `email` |
| `phone_e164` | `VARCHAR(20)` | NULL | Field `phone_e164` |
| `password_hash` | `VARCHAR(255)` | NULL | Field `password_hash` |
| `status` | `VARCHAR(20)` | NOT NULL | Field `status` |
| `is_demo` | `BOOLEAN` | NOT NULL | Field `is_demo` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |
| `deleted_at` | `DATETIME` | NULL | Field `deleted_at` |

**Indexes:**
- `ix_users_username` on (username)
- `ix_users_phone_e164` on (phone_e164)
- `ix_users_email` on (email)

**Check Constraints:**
- `chk_users_contact_present`
- `chk_users_status`

---

### Table: `user_roles`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `user_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `user_id` |
| `role` | `VARCHAR(50)` | NOT NULL | Field `role` |
| `is_active` | `BOOLEAN` | NOT NULL | Field `is_active` |
| `granted_by` | `CHAR(36)` | NULL (FK -> `users.id`) | Field `granted_by` |
| `granted_at` | `DATETIME` | NOT NULL | Field `granted_at` |

**Indexes:**
- `ix_user_roles_user_id` on (user_id)

**Check Constraints:**
- `chk_user_roles_valid`

---

### Table: `user_profiles`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `user_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `user_id` |
| `first_name` | `VARCHAR(100)` | NULL | Field `first_name` |
| `last_name` | `VARCHAR(100)` | NULL | Field `last_name` |
| `avatar_url` | `VARCHAR(500)` | NULL | Field `avatar_url` |
| `bio` | `TEXT` | NULL | Field `bio` |
| `address` | `TEXT` | NULL | Field `address` |
| `preferred_contact_method` | `VARCHAR(20)` | NOT NULL | Field `preferred_contact_method` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Check Constraints:**
- `chk_user_profiles_contact_method`

---

### Table: `user_permissions`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `user_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `user_id` |
| `permission_code` | `VARCHAR(100)` | NOT NULL | Field `permission_code` |
| `scope` | `VARCHAR(100)` | NOT NULL | Field `scope` |
| `granted_at` | `DATETIME` | NOT NULL | Field `granted_at` |
| `expires_at` | `DATETIME` | NULL | Field `expires_at` |

**Indexes:**
- `ix_user_permissions_user_id` on (user_id)

---

### Table: `user_sessions`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `user_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `user_id` |
| `session_token_hash` | `VARCHAR(255)` | NOT NULL | Field `session_token_hash` |
| `ip_address` | `VARCHAR(45)` | NULL | Field `ip_address` |
| `user_agent` | `TEXT` | NULL | Field `user_agent` |
| `device_id` | `VARCHAR(100)` | NULL | Field `device_id` |
| `expires_at` | `DATETIME` | NOT NULL | Field `expires_at` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `revoked_at` | `DATETIME` | NULL | Field `revoked_at` |

**Indexes:**
- `ix_user_sessions_session_token_hash` on (session_token_hash)
- `ix_user_sessions_user_id` on (user_id)

---

### Table: `user_preferences`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `user_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `user_id` |
| `preferred_language` | `VARCHAR(10)` | NOT NULL | Field `preferred_language` |
| `timezone` | `VARCHAR(50)` | NOT NULL | Field `timezone` |
| `theme` | `VARCHAR(20)` | NOT NULL | Field `theme` |
| `notification_frequency` | `VARCHAR(20)` | NOT NULL | Field `notification_frequency` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Check Constraints:**
- `chk_user_preferences_notif_freq`

---

## Farm Database

### Table: `farms`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `name` | `VARCHAR(200)` | NOT NULL | Field `name` |
| `registration_number` | `VARCHAR(100)` | NULL | Field `registration_number` |
| `total_area_sqm` | `FLOAT` | NULL | Field `total_area_sqm` |
| `owner_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `owner_id` |
| `status` | `VARCHAR(20)` | NOT NULL | Field `status` |
| `is_demo` | `BOOLEAN` | NOT NULL | Field `is_demo` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |
| `deleted_at` | `DATETIME` | NULL | Field `deleted_at` |

**Indexes:**
- `ix_farms_owner_id` on (owner_id)

**Check Constraints:**
- `chk_farms_positive_area`
- `chk_farms_status`

---

### Table: `farm_boundaries`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `farm_id` | `CHAR(36)` | NOT NULL (FK -> `farms.id`) | Field `farm_id` |
| `boundary_polygon` | `TEXT` | NOT NULL | Field `boundary_polygon` |
| `perimeter_meters` | `FLOAT` | NULL | Field `perimeter_meters` |
| `area_sqm` | `FLOAT` | NULL | Field `area_sqm` |
| `elevation_meters` | `FLOAT` | NULL | Field `elevation_meters` |
| `is_active` | `BOOLEAN` | NOT NULL | Field `is_active` |
| `recorded_at` | `DATETIME` | NOT NULL | Field `recorded_at` |

**Indexes:**
- `idx_farm_boundaries_geom` on (boundary_polygon)
- `ix_farm_boundaries_farm_id` on (farm_id)

---

### Table: `farm_sections`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `farm_id` | `CHAR(36)` | NOT NULL (FK -> `farms.id`) | Field `farm_id` |
| `section_code` | `VARCHAR(50)` | NOT NULL | Field `section_code` |
| `name` | `VARCHAR(100)` | NOT NULL | Field `name` |
| `description` | `TEXT` | NULL | Field `description` |
| `section_polygon` | `TEXT` | NULL | Field `section_polygon` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_farm_sections_farm_id` on (farm_id)
- `idx_farm_sections_geom` on (section_polygon)

---

### Table: `farm_plots`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `farm_id` | `CHAR(36)` | NOT NULL (FK -> `farms.id`) | Field `farm_id` |
| `section_id` | `CHAR(36)` | NULL (FK -> `farm_sections.id`) | Field `section_id` |
| `plot_code` | `VARCHAR(50)` | NOT NULL | Field `plot_code` |
| `soil_type` | `VARCHAR(50)` | NULL | Field `soil_type` |
| `irrigation_source` | `VARCHAR(50)` | NULL | Field `irrigation_source` |
| `area_sqm` | `FLOAT` | NULL | Field `area_sqm` |
| `plot_polygon` | `TEXT` | NULL | Field `plot_polygon` |
| `is_active` | `BOOLEAN` | NOT NULL | Field `is_active` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_farm_plots_section_id` on (section_id)
- `ix_farm_plots_farm_id` on (farm_id)
- `idx_farm_plots_geom` on (plot_polygon)

**Check Constraints:**
- `chk_farm_plots_positive_area`

---

### Table: `farm_locations`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `farm_id` | `CHAR(36)` | NOT NULL (FK -> `farms.id`) | Field `farm_id` |
| `address_line` | `VARCHAR(255)` | NULL | Field `address_line` |
| `village_or_town` | `VARCHAR(100)` | NULL | Field `village_or_town` |
| `taluk_or_subdistrict` | `VARCHAR(100)` | NULL | Field `taluk_or_subdistrict` |
| `district` | `VARCHAR(100)` | NOT NULL | Field `district` |
| `state` | `VARCHAR(100)` | NOT NULL | Field `state` |
| `country` | `VARCHAR(100)` | NOT NULL | Field `country` |
| `postal_code` | `VARCHAR(20)` | NULL | Field `postal_code` |
| `centroid` | `TEXT` | NOT NULL | Field `centroid` |

**Indexes:**
- `idx_farm_locations_centroid` on (centroid)
- `ix_farm_locations_farm_id` on (farm_id)

---

### Table: `farm_members`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `farm_id` | `CHAR(36)` | NOT NULL (FK -> `farms.id`) | Field `farm_id` |
| `user_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `user_id` |
| `access_level` | `VARCHAR(30)` | NOT NULL | Field `access_level` |
| `is_active` | `BOOLEAN` | NOT NULL | Field `is_active` |
| `joined_at` | `DATETIME` | NOT NULL | Field `joined_at` |

**Indexes:**
- `ix_farm_members_user_id` on (user_id)
- `ix_farm_members_farm_id` on (farm_id)

**Check Constraints:**
- `chk_farm_members_access_level`

---

## Crop and Plant Database

### Table: `crop_types`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `group_id` | `CHAR(36)` | NULL (FK -> `crop_groups.id`) | Field `group_id` |
| `code` | `VARCHAR(50)` | NOT NULL | Field `code` |
| `common_name` | `VARCHAR(100)` | NOT NULL | Field `common_name` |
| `botanical_name` | `VARCHAR(150)` | NOT NULL | Field `botanical_name` |
| `description` | `TEXT` | NULL | Field `description` |
| `optimal_temp_min_c` | `FLOAT` | NULL | Field `optimal_temp_min_c` |
| `optimal_temp_max_c` | `FLOAT` | NULL | Field `optimal_temp_max_c` |
| `optimal_rainfall_mm` | `FLOAT` | NULL | Field `optimal_rainfall_mm` |
| `is_active` | `BOOLEAN` | NOT NULL | Field `is_active` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_crop_types_group_id` on (group_id)

---

### Table: `crop_groups`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `code` | `VARCHAR(50)` | NOT NULL | Field `code` |
| `name` | `VARCHAR(100)` | NOT NULL | Field `name` |
| `description` | `TEXT` | NULL | Field `description` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

---

### Table: `crop_instances`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `plot_id` | `CHAR(36)` | NOT NULL (FK -> `farm_plots.id`) | Field `plot_id` |
| `crop_type_id` | `CHAR(36)` | NOT NULL (FK -> `crop_types.id`) | Field `crop_type_id` |
| `variety` | `VARCHAR(100)` | NOT NULL | Field `variety` |
| `season` | `VARCHAR(30)` | NOT NULL | Field `season` |
| `planting_date` | `DATE` | NOT NULL | Field `planting_date` |
| `expected_harvest_date` | `DATE` | NULL | Field `expected_harvest_date` |
| `actual_harvest_date` | `DATE` | NULL | Field `actual_harvest_date` |
| `status` | `VARCHAR(30)` | NOT NULL | Field `status` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_crop_instances_crop_type_id` on (crop_type_id)
- `ix_crop_instances_plot_id` on (plot_id)

**Check Constraints:**
- `chk_crop_instance_status`
- `chk_crop_instance_season`

---

### Table: `plants`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `crop_instance_id` | `CHAR(36)` | NOT NULL (FK -> `crop_instances.id`) | Field `crop_instance_id` |
| `tag_or_id` | `VARCHAR(50)` | NOT NULL | Field `tag_or_id` |
| `row_number` | `INTEGER` | NULL | Field `row_number` |
| `column_number` | `INTEGER` | NULL | Field `column_number` |
| `plant_location` | `TEXT` | NULL | Field `plant_location` |
| `health_status` | `VARCHAR(30)` | NOT NULL | Field `health_status` |
| `planted_at` | `DATE` | NULL | Field `planted_at` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `idx_plants_geom` on (plant_location)
- `ix_plants_crop_instance_id` on (crop_instance_id)

**Check Constraints:**
- `chk_plants_health_status`

---

### Table: `plant_observations`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `plant_id` | `CHAR(36)` | NOT NULL (FK -> `plants.id`) | Field `plant_id` |
| `observer_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `observer_id` |
| `observation_date` | `DATETIME` | NOT NULL | Field `observation_date` |
| `visual_symptoms` | `TEXT` | NULL | Field `visual_symptoms` |
| `vigor_score` | `INTEGER` | NULL | Field `vigor_score` |
| `foliage_damage_pct` | `FLOAT` | NULL | Field `foliage_damage_pct` |
| `observation_notes` | `TEXT` | NULL | Field `observation_notes` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_plant_observations_observer_id` on (observer_id)
- `ix_plant_observations_plant_id` on (plant_id)

**Check Constraints:**
- `chk_plant_obs_vigor`
- `chk_plant_obs_damage_pct`

---

### Table: `crop_growth_stages`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `crop_type_id` | `CHAR(36)` | NOT NULL (FK -> `crop_types.id`) | Field `crop_type_id` |
| `stage_name` | `VARCHAR(50)` | NOT NULL | Field `stage_name` |
| `stage_order` | `INTEGER` | NOT NULL | Field `stage_order` |
| `typical_duration_days` | `INTEGER` | NOT NULL | Field `typical_duration_days` |
| `water_requirement_level` | `VARCHAR(20)` | NOT NULL | Field `water_requirement_level` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_crop_growth_stages_crop_type_id` on (crop_type_id)

**Check Constraints:**
- `chk_crop_stage_water_req`
- `chk_crop_stage_duration`

---

### Table: `planting_records`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `crop_instance_id` | `CHAR(36)` | NOT NULL (FK -> `crop_instances.id`) | Field `crop_instance_id` |
| `seed_lot_number` | `VARCHAR(100)` | NULL | Field `seed_lot_number` |
| `seed_source` | `VARCHAR(200)` | NULL | Field `seed_source` |
| `sowing_method` | `VARCHAR(50)` | NOT NULL | Field `sowing_method` |
| `planting_density_per_sqm` | `FLOAT` | NULL | Field `planting_density_per_sqm` |
| `fertilization_notes` | `TEXT` | NULL | Field `fertilization_notes` |
| `recorded_by` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `recorded_by` |
| `recorded_at` | `DATETIME` | NOT NULL | Field `recorded_at` |

**Indexes:**
- `ix_planting_records_crop_instance_id` on (crop_instance_id)

**Check Constraints:**
- `chk_planting_record_sowing_method`

---

## Media Database

### Table: `media_files`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `uploader_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `uploader_id` |
| `storage_provider` | `VARCHAR(50)` | NOT NULL | Field `storage_provider` |
| `bucket_name` | `VARCHAR(100)` | NOT NULL | Field `bucket_name` |
| `object_key` | `VARCHAR(500)` | NOT NULL | Field `object_key` |
| `file_name` | `VARCHAR(255)` | NOT NULL | Field `file_name` |
| `file_size_bytes` | `INTEGER` | NOT NULL | Field `file_size_bytes` |
| `mime_type` | `VARCHAR(100)` | NOT NULL | Field `mime_type` |
| `file_hash_sha256` | `VARCHAR(64)` | NOT NULL | Field `file_hash_sha256` |
| `media_type` | `VARCHAR(20)` | NOT NULL | Field `media_type` |
| `duration_seconds` | `FLOAT` | NULL | Field `duration_seconds` |
| `width_px` | `INTEGER` | NULL | Field `width_px` |
| `height_px` | `INTEGER` | NULL | Field `height_px` |
| `capture_timestamp` | `DATETIME` | NOT NULL | Field `capture_timestamp` |
| `upload_timestamp` | `DATETIME` | NOT NULL | Field `upload_timestamp` |
| `is_quarantined` | `BOOLEAN` | NOT NULL | Field `is_quarantined` |
| `quarantine_reason` | `VARCHAR(255)` | NULL | Field `quarantine_reason` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_media_files_uploader_id` on (uploader_id)
- `ix_media_files_object_key` on (object_key)
- `ix_media_files_file_hash_sha256` on (file_hash_sha256)

**Check Constraints:**
- `chk_media_files_positive_size`
- `chk_media_files_media_type`
- `chk_media_files_mime_type`

---

### Table: `media_frames`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `media_file_id` | `CHAR(36)` | NOT NULL (FK -> `media_files.id`) | Field `media_file_id` |
| `frame_number` | `INTEGER` | NOT NULL | Field `frame_number` |
| `timestamp_offset_ms` | `INTEGER` | NOT NULL | Field `timestamp_offset_ms` |
| `frame_object_key` | `VARCHAR(500)` | NOT NULL | Field `frame_object_key` |
| `width_px` | `INTEGER` | NULL | Field `width_px` |
| `height_px` | `INTEGER` | NULL | Field `height_px` |
| `quality_score` | `FLOAT` | NULL | Field `quality_score` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_media_frames_media_file_id` on (media_file_id)

**Check Constraints:**
- `chk_media_frames_quality`
- `chk_media_frames_num_nonneg`

---

### Table: `media_observations`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `media_file_id` | `CHAR(36)` | NOT NULL (FK -> `media_files.id`) | Field `media_file_id` |
| `observation_id` | `CHAR(36)` | NOT NULL (FK -> `plant_observations.id`) | Field `observation_id` |
| `media_role` | `VARCHAR(50)` | NOT NULL | Field `media_role` |
| `attached_at` | `DATETIME` | NOT NULL | Field `attached_at` |

**Indexes:**
- `ix_media_observations_observation_id` on (observation_id)
- `ix_media_observations_media_file_id` on (media_file_id)

**Check Constraints:**
- `chk_media_obs_role`

---

### Table: `media_locations`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `media_file_id` | `CHAR(36)` | NOT NULL (FK -> `media_files.id`) | Field `media_file_id` |
| `location` | `TEXT` | NOT NULL | Field `location` |
| `altitude_meters` | `FLOAT` | NULL | Field `altitude_meters` |
| `gps_accuracy_meters` | `FLOAT` | NULL | Field `gps_accuracy_meters` |
| `heading_degrees` | `FLOAT` | NULL | Field `heading_degrees` |
| `captured_at` | `DATETIME` | NOT NULL | Field `captured_at` |

**Indexes:**
- `idx_media_locations_geom` on (location)

---

### Table: `media_analysis_links`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `media_file_id` | `CHAR(36)` | NOT NULL (FK -> `media_files.id`) | Field `media_file_id` |
| `analysis_id` | `CHAR(36)` | NOT NULL (FK -> `ai_analysis.id`) | Field `analysis_id` |
| `frame_id` | `CHAR(36)` | NULL (FK -> `media_frames.id`) | Field `frame_id` |
| `linked_at` | `DATETIME` | NOT NULL | Field `linked_at` |

**Indexes:**
- `ix_media_analysis_links_analysis_id` on (analysis_id)
- `ix_media_analysis_links_media_file_id` on (media_file_id)

---

## Pest and Disease Database

### Table: `pests`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `pest_category_id` | `CHAR(36)` | NOT NULL (FK -> `pest_categories.id`) | Field `pest_category_id` |
| `common_name` | `VARCHAR(150)` | NOT NULL | Field `common_name` |
| `scientific_name` | `VARCHAR(200)` | NOT NULL | Field `scientific_name` |
| `description` | `TEXT` | NULL | Field `description` |
| `identification_guide` | `TEXT` | NULL | Field `identification_guide` |
| `economic_threshold` | `TEXT` | NULL | Field `economic_threshold` |
| `quarantine_status` | `VARCHAR(30)` | NOT NULL | Field `quarantine_status` |
| `is_active` | `BOOLEAN` | NOT NULL | Field `is_active` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_pests_common_name` on (common_name)
- `ix_pests_pest_category_id` on (pest_category_id)

**Check Constraints:**
- `chk_pests_quarantine_status`

---

### Table: `pest_categories`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `code` | `VARCHAR(50)` | NOT NULL | Field `code` |
| `name` | `VARCHAR(100)` | NOT NULL | Field `name` |
| `description` | `TEXT` | NULL | Field `description` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

---

### Table: `pest_life_cycles`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `pest_id` | `CHAR(36)` | NOT NULL (FK -> `pests.id`) | Field `pest_id` |
| `stage_name` | `VARCHAR(50)` | NOT NULL | Field `stage_name` |
| `stage_duration_days_min` | `INTEGER` | NOT NULL | Field `stage_duration_days_min` |
| `stage_duration_days_max` | `INTEGER` | NOT NULL | Field `stage_duration_days_max` |
| `damaging_stage` | `BOOLEAN` | NOT NULL | Field `damaging_stage` |
| `favorable_temperature_min` | `FLOAT` | NULL | Field `favorable_temperature_min` |
| `favorable_temperature_max` | `FLOAT` | NULL | Field `favorable_temperature_max` |
| `favorable_humidity_min` | `FLOAT` | NULL | Field `favorable_humidity_min` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_pest_life_cycles_pest_id` on (pest_id)

**Check Constraints:**
- `chk_pest_stage_dur_min`
- `chk_pest_stage_dur_max`

---

### Table: `pest_host_crops`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `pest_id` | `CHAR(36)` | NOT NULL (FK -> `pests.id`) | Field `pest_id` |
| `crop_type_id` | `CHAR(36)` | NOT NULL (FK -> `crop_types.id`) | Field `crop_type_id` |
| `susceptibility_level` | `VARCHAR(30)` | NOT NULL | Field `susceptibility_level` |
| `damage_severity_rating` | `INTEGER` | NULL | Field `damage_severity_rating` |
| `notes` | `TEXT` | NULL | Field `notes` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_pest_host_crops_crop_type_id` on (crop_type_id)
- `ix_pest_host_crops_pest_id` on (pest_id)

**Check Constraints:**
- `chk_pest_host_severity_rating`
- `chk_pest_host_susceptibility`

---

### Table: `diseases`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `common_name` | `VARCHAR(150)` | NOT NULL | Field `common_name` |
| `scientific_name` | `VARCHAR(200)` | NOT NULL | Field `scientific_name` |
| `pathogen_type` | `VARCHAR(50)` | NOT NULL | Field `pathogen_type` |
| `vector_pest_id` | `CHAR(36)` | NULL (FK -> `pests.id`) | Field `vector_pest_id` |
| `description` | `TEXT` | NULL | Field `description` |
| `favorable_conditions` | `TEXT` | NULL | Field `favorable_conditions` |
| `economic_impact` | `TEXT` | NULL | Field `economic_impact` |
| `is_active` | `BOOLEAN` | NOT NULL | Field `is_active` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_diseases_common_name` on (common_name)

**Check Constraints:**
- `chk_diseases_pathogen_type`

---

### Table: `disease_symptoms`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `disease_id` | `CHAR(36)` | NOT NULL (FK -> `diseases.id`) | Field `disease_id` |
| `affected_plant_part` | `VARCHAR(50)` | NOT NULL | Field `affected_plant_part` |
| `symptom_description` | `TEXT` | NOT NULL | Field `symptom_description` |
| `severity_scale` | `VARCHAR(20)` | NOT NULL | Field `severity_scale` |
| `is_primary_symptom` | `BOOLEAN` | NOT NULL | Field `is_primary_symptom` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_disease_symptoms_disease_id` on (disease_id)

**Check Constraints:**
- `chk_disease_symptoms_plant_part`

---

### Table: `crop_symptoms`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `crop_type_id` | `CHAR(36)` | NOT NULL (FK -> `crop_types.id`) | Field `crop_type_id` |
| `disease_id` | `CHAR(36)` | NULL (FK -> `diseases.id`) | Field `disease_id` |
| `pest_id` | `CHAR(36)` | NULL (FK -> `pests.id`) | Field `pest_id` |
| `symptom_name` | `VARCHAR(150)` | NOT NULL | Field `symptom_name` |
| `characteristic_appearance` | `TEXT` | NOT NULL | Field `characteristic_appearance` |
| `typical_growth_stage` | `VARCHAR(50)` | NULL | Field `typical_growth_stage` |
| `visual_diagnostic_rules` | `TEXT` | NULL | Field `visual_diagnostic_rules` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_crop_symptoms_crop_type_id` on (crop_type_id)
- `ix_crop_symptoms_pest_id` on (pest_id)
- `ix_crop_symptoms_disease_id` on (disease_id)

**Check Constraints:**
- `chk_crop_symptoms_agent_present`

---

### Table: `pest_damage_records`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `pest_id` | `CHAR(36)` | NOT NULL (FK -> `pests.id`) | Field `pest_id` |
| `plant_observation_id` | `CHAR(36)` | NULL (FK -> `plant_observations.id`) | Field `plant_observation_id` |
| `damage_type` | `VARCHAR(50)` | NOT NULL | Field `damage_type` |
| `affected_area_percentage` | `FLOAT` | NULL | Field `affected_area_percentage` |
| `severity_index` | `INTEGER` | NOT NULL | Field `severity_index` |
| `recorded_at` | `DATETIME` | NOT NULL | Field `recorded_at` |

**Indexes:**
- `ix_pest_damage_records_pest_id` on (pest_id)

**Check Constraints:**
- `chk_pest_damage_type`
- `chk_pest_damage_severity_idx`
- `chk_pest_damage_pct_bounds`

---

## AI Analysis Database

### Table: `ai_analysis`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `media_file_id` | `CHAR(36)` | NOT NULL (FK -> `media_files.id`) | Field `media_file_id` |
| `requested_by` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `requested_by` |
| `status` | `VARCHAR(30)` | NOT NULL | Field `status` |
| `analysis_type` | `VARCHAR(50)` | NOT NULL | Field `analysis_type` |
| `processing_time_ms` | `INTEGER` | NULL | Field `processing_time_ms` |
| `raw_response` | `JSON` | NULL | Field `raw_response` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_ai_analysis_media_file_id` on (media_file_id)
- `ix_ai_analysis_requested_by` on (requested_by)

**Check Constraints:**
- `chk_ai_analysis_status`
- `chk_ai_analysis_type`

---

### Table: `ai_predictions`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `analysis_id` | `CHAR(36)` | NOT NULL (FK -> `ai_analysis.id`) | Field `analysis_id` |
| `model_version_id` | `CHAR(36)` | NOT NULL (FK -> `ai_model_versions.id`) | Field `model_version_id` |
| `pest_id` | `CHAR(36)` | NULL (FK -> `pests.id`) | Field `pest_id` |
| `disease_id` | `CHAR(36)` | NULL (FK -> `diseases.id`) | Field `disease_id` |
| `primary_diagnosis` | `VARCHAR(150)` | NOT NULL | Field `primary_diagnosis` |
| `confidence_score` | `NUMERIC(5, 4)` | NOT NULL | Field `confidence_score` |
| `severity_level` | `VARCHAR(20)` | NOT NULL | Field `severity_level` |
| `inference_timestamp` | `DATETIME` | NOT NULL | Field `inference_timestamp` |
| `is_superseded` | `BOOLEAN` | NOT NULL | Field `is_superseded` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_ai_predictions_model_version_id` on (model_version_id)
- `ix_ai_predictions_disease_id` on (disease_id)
- `ix_ai_predictions_pest_id` on (pest_id)
- `ix_ai_predictions_analysis_id` on (analysis_id)

**Check Constraints:**
- `chk_ai_pred_confidence_range`
- `chk_ai_pred_severity_level`

---

### Table: `ai_detections`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `prediction_id` | `CHAR(36)` | NOT NULL (FK -> `ai_predictions.id`) | Field `prediction_id` |
| `label` | `VARCHAR(100)` | NOT NULL | Field `label` |
| `bbox_x_min` | `NUMERIC(6, 4)` | NOT NULL | Field `bbox_x_min` |
| `bbox_y_min` | `NUMERIC(6, 4)` | NOT NULL | Field `bbox_y_min` |
| `bbox_x_max` | `NUMERIC(6, 4)` | NOT NULL | Field `bbox_x_max` |
| `bbox_y_max` | `NUMERIC(6, 4)` | NOT NULL | Field `bbox_y_max` |
| `detection_confidence` | `NUMERIC(5, 4)` | NOT NULL | Field `detection_confidence` |
| `mask_rle` | `TEXT` | NULL | Field `mask_rle` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_ai_detections_prediction_id` on (prediction_id)

**Check Constraints:**
- `chk_ai_det_box_x`
- `chk_ai_detection_confidence_range`
- `chk_ai_det_box_y`

---

### Table: `ai_confidence`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `prediction_id` | `CHAR(36)` | NOT NULL (FK -> `ai_predictions.id`) | Field `prediction_id` |
| `class_label` | `VARCHAR(100)` | NOT NULL | Field `class_label` |
| `probability` | `NUMERIC(5, 4)` | NOT NULL | Field `probability` |
| `calibration_method` | `VARCHAR(50)` | NOT NULL | Field `calibration_method` |
| `entropy_score` | `FLOAT` | NULL | Field `entropy_score` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_ai_confidence_prediction_id` on (prediction_id)

**Check Constraints:**
- `chk_ai_conf_probability_range`

---

### Table: `ai_model_versions`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `model_name` | `VARCHAR(100)` | NOT NULL | Field `model_name` |
| `version_tag` | `VARCHAR(50)` | NOT NULL | Field `version_tag` |
| `model_family` | `VARCHAR(50)` | NOT NULL | Field `model_family` |
| `weights_digest_sha256` | `VARCHAR(64)` | NOT NULL | Field `weights_digest_sha256` |
| `training_dataset_version` | `VARCHAR(50)` | NULL | Field `training_dataset_version` |
| `f1_score` | `FLOAT` | NULL | Field `f1_score` |
| `accuracy` | `FLOAT` | NULL | Field `accuracy` |
| `inference_runtime` | `VARCHAR(50)` | NOT NULL | Field `inference_runtime` |
| `is_active` | `BOOLEAN` | NOT NULL | Field `is_active` |
| `deployed_at` | `DATETIME` | NOT NULL | Field `deployed_at` |
| `retired_at` | `DATETIME` | NULL | Field `retired_at` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Check Constraints:**
- `chk_ai_model_family`

---

### Table: `ai_feedback`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `diagnosis_record_id` | `CHAR(36)` | NOT NULL (FK -> `diagnosis_records.id`) | Field `diagnosis_record_id` |
| `prediction_id` | `CHAR(36)` | NOT NULL (FK -> `ai_predictions.id`) | Field `prediction_id` |
| `user_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `user_id` |
| `feedback_type` | `VARCHAR(50)` | NOT NULL | Field `feedback_type` |
| `corrected_pest_id` | `CHAR(36)` | NULL (FK -> `pests.id`) | Field `corrected_pest_id` |
| `corrected_disease_id` | `CHAR(36)` | NULL (FK -> `diseases.id`) | Field `corrected_disease_id` |
| `comments` | `TEXT` | NULL | Field `comments` |
| `submitted_at` | `DATETIME` | NOT NULL | Field `submitted_at` |

**Indexes:**
- `ix_ai_feedback_diagnosis_record_id` on (diagnosis_record_id)
- `ix_ai_feedback_prediction_id` on (prediction_id)
- `ix_ai_feedback_user_id` on (user_id)

**Check Constraints:**
- `chk_ai_feedback_type`

---

### Table: `diagnosis_records`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `analysis_id` | `CHAR(36)` | NOT NULL (FK -> `ai_analysis.id`) | Field `analysis_id` |
| `prediction_id` | `CHAR(36)` | NULL (FK -> `ai_predictions.id`) | Field `prediction_id` |
| `verified_by` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `verified_by` |
| `confirmed_pest_id` | `CHAR(36)` | NULL (FK -> `pests.id`) | Field `confirmed_pest_id` |
| `confirmed_disease_id` | `CHAR(36)` | NULL (FK -> `diseases.id`) | Field `confirmed_disease_id` |
| `confirmation_status` | `VARCHAR(50)` | NOT NULL | Field `confirmation_status` |
| `expert_notes` | `TEXT` | NULL | Field `expert_notes` |
| `diagnosed_at` | `DATETIME` | NOT NULL | Field `diagnosed_at` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_diagnosis_records_verified_by` on (verified_by)
- `ix_diagnosis_records_analysis_id` on (analysis_id)

**Check Constraints:**
- `chk_diag_confirmation_status`

---

## Pest Management Database

### Table: `ipm_methods`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `code` | `VARCHAR(50)` | NOT NULL | Field `code` |
| `title` | `VARCHAR(150)` | NOT NULL | Field `title` |
| `category` | `VARCHAR(50)` | NOT NULL | Field `category` |
| `description` | `TEXT` | NULL | Field `description` |
| `environmental_impact_rating` | `VARCHAR(20)` | NOT NULL | Field `environmental_impact_rating` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Check Constraints:**
- `chk_ipm_methods_category`
- `chk_ipm_methods_env_impact`

---

### Table: `pest_control_options`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `pest_id` | `CHAR(36)` | NULL (FK -> `pests.id`) | Field `pest_id` |
| `disease_id` | `CHAR(36)` | NULL (FK -> `diseases.id`) | Field `disease_id` |
| `crop_type_id` | `CHAR(36)` | NULL (FK -> `crop_types.id`) | Field `crop_type_id` |
| `ipm_method_id` | `CHAR(36)` | NOT NULL (FK -> `ipm_methods.id`) | Field `ipm_method_id` |
| `strategy_summary` | `TEXT` | NOT NULL | Field `strategy_summary` |
| `applicability_window` | `VARCHAR(100)` | NULL | Field `applicability_window` |
| `effectiveness_rating` | `VARCHAR(20)` | NOT NULL | Field `effectiveness_rating` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_pest_control_options_crop_type_id` on (crop_type_id)
- `ix_pest_control_options_ipm_method_id` on (ipm_method_id)
- `ix_pest_control_options_pest_id` on (pest_id)
- `ix_pest_control_options_disease_id` on (disease_id)

**Check Constraints:**
- `chk_control_options_eff_rating`
- `chk_control_options_target_present`

---

### Table: `biological_controls`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `ipm_method_id` | `CHAR(36)` | NOT NULL (FK -> `ipm_methods.id`) | Field `ipm_method_id` |
| `agent_name` | `VARCHAR(150)` | NOT NULL | Field `agent_name` |
| `agent_type` | `VARCHAR(50)` | NOT NULL | Field `agent_type` |
| `target_pest_id` | `CHAR(36)` | NOT NULL (FK -> `pests.id`) | Field `target_pest_id` |
| `release_rate` | `VARCHAR(100)` | NULL | Field `release_rate` |
| `optimal_timing` | `VARCHAR(100)` | NULL | Field `optimal_timing` |
| `conservation_practices` | `TEXT` | NULL | Field `conservation_practices` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_biological_controls_ipm_method_id` on (ipm_method_id)
- `ix_biological_controls_target_pest_id` on (target_pest_id)

**Check Constraints:**
- `chk_biocontrol_agent_type`

---

### Table: `mechanical_controls`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `ipm_method_id` | `CHAR(36)` | NOT NULL (FK -> `ipm_methods.id`) | Field `ipm_method_id` |
| `method_name` | `VARCHAR(150)` | NOT NULL | Field `method_name` |
| `equipment_needed` | `VARCHAR(200)` | NULL | Field `equipment_needed` |
| `labor_intensity` | `VARCHAR(20)` | NOT NULL | Field `labor_intensity` |
| `execution_steps` | `TEXT` | NOT NULL | Field `execution_steps` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_mechanical_controls_ipm_method_id` on (ipm_method_id)

**Check Constraints:**
- `chk_mech_control_labor`

---

### Table: `cultural_controls`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `ipm_method_id` | `CHAR(36)` | NOT NULL (FK -> `ipm_methods.id`) | Field `ipm_method_id` |
| `practice_type` | `VARCHAR(50)` | NOT NULL | Field `practice_type` |
| `implementation_protocol` | `TEXT` | NOT NULL | Field `implementation_protocol` |
| `recommended_timing` | `VARCHAR(100)` | NULL | Field `recommended_timing` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_cultural_controls_ipm_method_id` on (ipm_method_id)

**Check Constraints:**
- `chk_cult_control_practice`

---

### Table: `physical_controls`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `ipm_method_id` | `CHAR(36)` | NOT NULL (FK -> `ipm_methods.id`) | Field `ipm_method_id` |
| `control_mechanism` | `VARCHAR(50)` | NOT NULL | Field `control_mechanism` |
| `technical_parameters` | `TEXT` | NULL | Field `technical_parameters` |
| `installation_guide` | `TEXT` | NULL | Field `installation_guide` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_physical_controls_ipm_method_id` on (ipm_method_id)

**Check Constraints:**
- `chk_phys_control_mechanism`

---

### Table: `behavioral_controls`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `ipm_method_id` | `CHAR(36)` | NOT NULL (FK -> `ipm_methods.id`) | Field `ipm_method_id` |
| `attractant_type` | `VARCHAR(50)` | NOT NULL | Field `attractant_type` |
| `trap_density_per_hectare` | `INTEGER` | NULL | Field `trap_density_per_hectare` |
| `replacement_interval_days` | `INTEGER` | NULL | Field `replacement_interval_days` |
| `monitoring_threshold` | `VARCHAR(100)` | NULL | Field `monitoring_threshold` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_behavioral_controls_ipm_method_id` on (ipm_method_id)

**Check Constraints:**
- `chk_behav_control_attractant`

---

### Table: `chemical_controls`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `ipm_method_id` | `CHAR(36)` | NOT NULL (FK -> `ipm_methods.id`) | Field `ipm_method_id` |
| `active_ingredient` | `VARCHAR(150)` | NOT NULL | Field `active_ingredient` |
| `chemical_class` | `VARCHAR(100)` | NOT NULL | Field `chemical_class` |
| `mode_of_action` | `VARCHAR(200)` | NULL | Field `mode_of_action` |
| `resistance_risk_group` | `VARCHAR(50)` | NULL | Field `resistance_risk_group` |
| `toxicity_class` | `VARCHAR(20)` | NOT NULL | Field `toxicity_class` |
| `phi_days` | `INTEGER` | NULL | Field `phi_days` |
| `rei_hours` | `INTEGER` | NULL | Field `rei_hours` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_chemical_controls_active_ingredient` on (active_ingredient)
- `ix_chemical_controls_ipm_method_id` on (ipm_method_id)

**Check Constraints:**
- `chk_chem_control_toxicity`
- `chk_chem_phi_nonneg`
- `chk_chem_rei_nonneg`

---

### Table: `pesticide_registrations`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `chemical_control_id` | `CHAR(36)` | NOT NULL (FK -> `chemical_controls.id`) | Field `chemical_control_id` |
| `registration_number` | `VARCHAR(100)` | NOT NULL | Field `registration_number` |
| `registering_authority` | `VARCHAR(100)` | NOT NULL | Field `registering_authority` |
| `registered_trade_name` | `VARCHAR(150)` | NOT NULL | Field `registered_trade_name` |
| `approved_crop_id` | `CHAR(36)` | NOT NULL (FK -> `crop_types.id`) | Field `approved_crop_id` |
| `approved_pest_id` | `CHAR(36)` | NULL (FK -> `pests.id`) | Field `approved_pest_id` |
| `approved_dosage_per_ha` | `VARCHAR(100)` | NOT NULL | Field `approved_dosage_per_ha` |
| `approval_date` | `DATE` | NOT NULL | Field `approval_date` |
| `expiry_date` | `DATE` | NULL | Field `expiry_date` |
| `status` | `VARCHAR(30)` | NOT NULL | Field `status` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_pesticide_registrations_approved_pest_id` on (approved_pest_id)
- `ix_pesticide_registrations_chemical_control_id` on (chemical_control_id)
- `ix_pesticide_registrations_registration_number` on (registration_number)
- `ix_pesticide_registrations_approved_crop_id` on (approved_crop_id)

**Check Constraints:**
- `chk_pesticide_reg_status`

---

### Table: `treatment_records`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `farm_plot_id` | `CHAR(36)` | NOT NULL (FK -> `farm_plots.id`) | Field `farm_plot_id` |
| `crop_instance_id` | `CHAR(36)` | NOT NULL (FK -> `crop_instances.id`) | Field `crop_instance_id` |
| `applied_by` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `applied_by` |
| `ipm_method_id` | `CHAR(36)` | NOT NULL (FK -> `ipm_methods.id`) | Field `ipm_method_id` |
| `chemical_control_id` | `CHAR(36)` | NULL (FK -> `chemical_controls.id`) | Field `chemical_control_id` |
| `registration_id` | `CHAR(36)` | NULL (FK -> `pesticide_registrations.id`) | Field `registration_id` |
| `application_date` | `DATETIME` | NOT NULL | Field `application_date` |
| `dosage_applied` | `VARCHAR(100)` | NOT NULL | Field `dosage_applied` |
| `weather_conditions_at_spray` | `VARCHAR(150)` | NULL | Field `weather_conditions_at_spray` |
| `safety_equipment_used` | `VARCHAR(200)` | NULL | Field `safety_equipment_used` |
| `notes` | `TEXT` | NULL | Field `notes` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_treatment_records_crop_instance_id` on (crop_instance_id)
- `ix_treatment_records_farm_plot_id` on (farm_plot_id)
- `ix_treatment_records_applied_by` on (applied_by)
- `ix_treatment_records_ipm_method_id` on (ipm_method_id)

---

### Table: `treatment_effectiveness`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `treatment_record_id` | `CHAR(36)` | NOT NULL (FK -> `treatment_records.id`) | Field `treatment_record_id` |
| `evaluation_date` | `DATETIME` | NOT NULL | Field `evaluation_date` |
| `days_post_treatment` | `INTEGER` | NOT NULL | Field `days_post_treatment` |
| `pest_mortality_percentage` | `FLOAT` | NULL | Field `pest_mortality_percentage` |
| `crop_recovery_score` | `INTEGER` | NOT NULL | Field `crop_recovery_score` |
| `phytotoxicity_observed` | `BOOLEAN` | NOT NULL | Field `phytotoxicity_observed` |
| `evaluator_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `evaluator_id` |
| `evaluation_notes` | `TEXT` | NULL | Field `evaluation_notes` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_treatment_effectiveness_treatment_record_id` on (treatment_record_id)

**Check Constraints:**
- `chk_treat_eff_recovery_score`
- `chk_treat_eff_days_nonneg`
- `chk_treat_eff_mortality_range`

---

## Hotspot and Outbreak Database

### Table: `pest_reports`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `reporter_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `reporter_id` |
| `farm_plot_id` | `CHAR(36)` | NULL (FK -> `farm_plots.id`) | Field `farm_plot_id` |
| `reported_pest_id` | `CHAR(36)` | NULL (FK -> `pests.id`) | Field `reported_pest_id` |
| `reported_disease_id` | `CHAR(36)` | NULL (FK -> `diseases.id`) | Field `reported_disease_id` |
| `report_location` | `TEXT` | NOT NULL | Field `report_location` |
| `severity` | `VARCHAR(20)` | NOT NULL | Field `severity` |
| `observation_date` | `DATETIME` | NOT NULL | Field `observation_date` |
| `status` | `VARCHAR(30)` | NOT NULL | Field `status` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `idx_pest_reports_geom` on (report_location)
- `ix_pest_reports_reporter_id` on (reporter_id)
- `ix_pest_reports_reported_pest_id` on (reported_pest_id)
- `ix_pest_reports_reported_disease_id` on (reported_disease_id)
- `ix_pest_reports_farm_plot_id` on (farm_plot_id)

**Check Constraints:**
- `chk_pest_reports_status`
- `chk_pest_reports_severity`
- `chk_pest_report_target_present`

---

### Table: `verified_cases`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `pest_report_id` | `CHAR(36)` | NOT NULL (FK -> `pest_reports.id`) | Field `pest_report_id` |
| `verifier_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `verifier_id` |
| `confirmed_location` | `TEXT` | NOT NULL | Field `confirmed_location` |
| `confirmed_pest_id` | `CHAR(36)` | NULL (FK -> `pests.id`) | Field `confirmed_pest_id` |
| `confirmed_disease_id` | `CHAR(36)` | NULL (FK -> `diseases.id`) | Field `confirmed_disease_id` |
| `confidence_level` | `VARCHAR(20)` | NOT NULL | Field `confidence_level` |
| `verified_at` | `DATETIME` | NOT NULL | Field `verified_at` |
| `notes` | `TEXT` | NULL | Field `notes` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_verified_cases_confirmed_disease_id` on (confirmed_disease_id)
- `ix_verified_cases_confirmed_pest_id` on (confirmed_pest_id)
- `idx_verified_cases_geom` on (confirmed_location)
- `ix_verified_cases_verifier_id` on (verifier_id)

**Check Constraints:**
- `chk_verified_cases_conf`

---

### Table: `hotspot_regions`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `region_name` | `VARCHAR(150)` | NOT NULL | Field `region_name` |
| `boundary_geom` | `TEXT` | NOT NULL | Field `boundary_geom` |
| `pest_id` | `CHAR(36)` | NULL (FK -> `pests.id`) | Field `pest_id` |
| `disease_id` | `CHAR(36)` | NULL (FK -> `diseases.id`) | Field `disease_id` |
| `risk_level` | `VARCHAR(20)` | NOT NULL | Field `risk_level` |
| `active_case_count` | `INTEGER` | NOT NULL | Field `active_case_count` |
| `start_date` | `DATE` | NOT NULL | Field `start_date` |
| `end_date` | `DATE` | NULL | Field `end_date` |
| `is_active` | `BOOLEAN` | NOT NULL | Field `is_active` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_hotspot_regions_disease_id` on (disease_id)
- `ix_hotspot_regions_pest_id` on (pest_id)
- `idx_hotspot_regions_geom` on (boundary_geom)

**Check Constraints:**
- `chk_hotspot_cases_nonneg`
- `chk_hotspot_risk_level`

---

### Table: `regional_pest_statistics`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `region_code` | `VARCHAR(50)` | NOT NULL | Field `region_code` |
| `date_bucket` | `DATE` | NOT NULL | Field `date_bucket` |
| `pest_id` | `CHAR(36)` | NULL (FK -> `pests.id`) | Field `pest_id` |
| `disease_id` | `CHAR(36)` | NULL (FK -> `diseases.id`) | Field `disease_id` |
| `total_reports` | `INTEGER` | NOT NULL | Field `total_reports` |
| `verified_count` | `INTEGER` | NOT NULL | Field `verified_count` |
| `incidence_rate` | `FLOAT` | NOT NULL | Field `incidence_rate` |
| `average_severity` | `FLOAT` | NULL | Field `average_severity` |
| `calculated_at` | `DATETIME` | NOT NULL | Field `calculated_at` |

**Indexes:**
- `ix_regional_pest_statistics_region_code` on (region_code)
- `ix_regional_pest_statistics_date_bucket` on (date_bucket)

---

### Table: `outbreak_predictions`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `region_geom` | `TEXT` | NOT NULL | Field `region_geom` |
| `pest_id` | `CHAR(36)` | NULL (FK -> `pests.id`) | Field `pest_id` |
| `disease_id` | `CHAR(36)` | NULL (FK -> `diseases.id`) | Field `disease_id` |
| `predicted_risk_score` | `NUMERIC(5, 4)` | NOT NULL | Field `predicted_risk_score` |
| `forecast_horizon_days` | `INTEGER` | NOT NULL | Field `forecast_horizon_days` |
| `prediction_model_version` | `CHAR(36)` | NULL (FK -> `ai_model_versions.id`) | Field `prediction_model_version` |
| `prediction_timestamp` | `DATETIME` | NOT NULL | Field `prediction_timestamp` |
| `valid_from` | `DATETIME` | NOT NULL | Field `valid_from` |
| `valid_until` | `DATETIME` | NOT NULL | Field `valid_until` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_outbreak_predictions_pest_id` on (pest_id)
- `ix_outbreak_predictions_disease_id` on (disease_id)
- `idx_outbreak_predictions_geom` on (region_geom)

**Check Constraints:**
- `chk_outbreak_risk_range`
- `chk_outbreak_horizon_pos`

---

### Table: `spread_observations`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `hotspot_id` | `CHAR(36)` | NOT NULL (FK -> `hotspot_regions.id`) | Field `hotspot_id` |
| `observation_location` | `TEXT` | NOT NULL | Field `observation_location` |
| `spread_direction_degrees` | `FLOAT` | NULL | Field `spread_direction_degrees` |
| `spread_rate_km_per_day` | `FLOAT` | NULL | Field `spread_rate_km_per_day` |
| `observed_at` | `DATETIME` | NOT NULL | Field `observed_at` |
| `recorder_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `recorder_id` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_spread_observations_hotspot_id` on (hotspot_id)
- `idx_spread_obs_geom` on (observation_location)

**Check Constraints:**
- `chk_spread_direction_degrees`

---

### Table: `risk_history`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `region_code` | `VARCHAR(50)` | NOT NULL | Field `region_code` |
| `timestamp` | `DATETIME` | NOT NULL | Field `timestamp` |
| `pest_id` | `CHAR(36)` | NULL (FK -> `pests.id`) | Field `pest_id` |
| `historical_risk_score` | `NUMERIC(5, 4)` | NOT NULL | Field `historical_risk_score` |
| `weather_conditions` | `TEXT` | NULL | Field `weather_conditions` |
| `source_run_id` | `VARCHAR(100)` | NULL | Field `source_run_id` |
| `recorded_at` | `DATETIME` | NOT NULL | Field `recorded_at` |

**Indexes:**
- `ix_risk_history_region_code` on (region_code)
- `ix_risk_history_timestamp` on (timestamp)

**Check Constraints:**
- `chk_risk_hist_score_range`

---

### Table: `monitoring_coverage`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `area_name` | `VARCHAR(150)` | NOT NULL | Field `area_name` |
| `boundary` | `TEXT` | NOT NULL | Field `boundary` |
| `assigned_scouts_count` | `INTEGER` | NOT NULL | Field `assigned_scouts_count` |
| `scouting_frequency_days` | `INTEGER` | NOT NULL | Field `scouting_frequency_days` |
| `last_monitored_date` | `DATE` | NULL | Field `last_monitored_date` |
| `coverage_percentage` | `FLOAT` | NOT NULL | Field `coverage_percentage` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `idx_monitoring_coverage_geom` on (boundary)

**Check Constraints:**
- `chk_monitoring_coverage_pct`

---

## Recovery and Inspection Database

### Table: `inspections`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `farm_id` | `CHAR(36)` | NOT NULL (FK -> `farms.id`) | Field `farm_id` |
| `plot_id` | `CHAR(36)` | NULL (FK -> `farm_plots.id`) | Field `plot_id` |
| `inspector_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `inspector_id` |
| `scheduled_date` | `DATE` | NOT NULL | Field `scheduled_date` |
| `conducted_at` | `DATETIME` | NULL | Field `conducted_at` |
| `status` | `VARCHAR(30)` | NOT NULL | Field `status` |
| `overall_health_rating` | `INTEGER` | NULL | Field `overall_health_rating` |
| `findings_summary` | `TEXT` | NULL | Field `findings_summary` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_inspections_farm_id` on (farm_id)
- `ix_inspections_inspector_id` on (inspector_id)
- `ix_inspections_plot_id` on (plot_id)

**Check Constraints:**
- `chk_inspections_health_rating`
- `chk_inspections_status`

---

### Table: `inspection_assignments`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `inspection_id` | `CHAR(36)` | NOT NULL (FK -> `inspections.id`) | Field `inspection_id` |
| `agent_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `agent_id` |
| `assigned_by` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `assigned_by` |
| `assigned_at` | `DATETIME` | NOT NULL | Field `assigned_at` |
| `role_in_inspection` | `VARCHAR(50)` | NOT NULL | Field `role_in_inspection` |
| `status` | `VARCHAR(30)` | NOT NULL | Field `status` |

**Indexes:**
- `ix_inspection_assignments_agent_id` on (agent_id)
- `ix_inspection_assignments_inspection_id` on (inspection_id)

**Check Constraints:**
- `chk_insp_assign_status`

---

### Table: `scouting_records`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `inspection_id` | `CHAR(36)` | NOT NULL (FK -> `inspections.id`) | Field `inspection_id` |
| `waypoint_location` | `TEXT` | NOT NULL | Field `waypoint_location` |
| `plant_count_inspected` | `INTEGER` | NOT NULL | Field `plant_count_inspected` |
| `infested_plant_count` | `INTEGER` | NOT NULL | Field `infested_plant_count` |
| `pest_id` | `CHAR(36)` | NULL (FK -> `pests.id`) | Field `pest_id` |
| `notes` | `TEXT` | NULL | Field `notes` |
| `recorded_at` | `DATETIME` | NOT NULL | Field `recorded_at` |

**Indexes:**
- `idx_scouting_records_geom` on (waypoint_location)
- `ix_scouting_records_inspection_id` on (inspection_id)

**Check Constraints:**
- `chk_scouting_infested_bounds`
- `chk_scouting_inspected_nonneg`

---

### Table: `recovery_records`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `farm_plot_id` | `CHAR(36)` | NOT NULL (FK -> `farm_plots.id`) | Field `farm_plot_id` |
| `crop_instance_id` | `CHAR(36)` | NOT NULL (FK -> `crop_instances.id`) | Field `crop_instance_id` |
| `treatment_record_id` | `CHAR(36)` | NULL (FK -> `treatment_records.id`) | Field `treatment_record_id` |
| `inspection_id` | `CHAR(36)` | NULL (FK -> `inspections.id`) | Field `inspection_id` |
| `recovery_status` | `VARCHAR(30)` | NOT NULL | Field `recovery_status` |
| `recovery_percentage` | `FLOAT` | NOT NULL | Field `recovery_percentage` |
| `assessed_at` | `DATETIME` | NOT NULL | Field `assessed_at` |
| `assessor_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `assessor_id` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_recovery_records_farm_plot_id` on (farm_plot_id)
- `ix_recovery_records_crop_instance_id` on (crop_instance_id)

**Check Constraints:**
- `chk_recovery_pct_range`
- `chk_recovery_status_valid`

---

### Table: `recovery_comparisons`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `recovery_record_id` | `CHAR(36)` | NOT NULL (FK -> `recovery_records.id`) | Field `recovery_record_id` |
| `baseline_media_id` | `CHAR(36)` | NOT NULL (FK -> `media_files.id`) | Field `baseline_media_id` |
| `current_media_id` | `CHAR(36)` | NOT NULL (FK -> `media_files.id`) | Field `current_media_id` |
| `symptom_reduction_percentage` | `FLOAT` | NULL | Field `symptom_reduction_percentage` |
| `foliage_regrowth_score` | `INTEGER` | NULL | Field `foliage_regrowth_score` |
| `comparison_notes` | `TEXT` | NULL | Field `comparison_notes` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_recovery_comparisons_recovery_record_id` on (recovery_record_id)

**Check Constraints:**
- `chk_rec_comp_reduction_pct`
- `chk_rec_comp_regrowth_score`

---

### Table: `seasonal_history`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `farm_plot_id` | `CHAR(36)` | NOT NULL (FK -> `farm_plots.id`) | Field `farm_plot_id` |
| `season_year` | `INTEGER` | NOT NULL | Field `season_year` |
| `season_name` | `VARCHAR(30)` | NOT NULL | Field `season_name` |
| `crop_type_id` | `CHAR(36)` | NOT NULL (FK -> `crop_types.id`) | Field `crop_type_id` |
| `total_yield_kg` | `FLOAT` | NULL | Field `total_yield_kg` |
| `pest_pressure_rating` | `VARCHAR(20)` | NOT NULL | Field `pest_pressure_rating` |
| `weather_summary` | `TEXT` | NULL | Field `weather_summary` |
| `recorded_at` | `DATETIME` | NOT NULL | Field `recorded_at` |

**Indexes:**
- `ix_seasonal_history_farm_plot_id` on (farm_plot_id)

**Check Constraints:**
- `chk_seasonal_hist_season`
- `chk_seasonal_hist_pest_pressure`

---

### Table: `infestation_history`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `farm_plot_id` | `CHAR(36)` | NOT NULL (FK -> `farm_plots.id`) | Field `farm_plot_id` |
| `crop_instance_id` | `CHAR(36)` | NULL (FK -> `crop_instances.id`) | Field `crop_instance_id` |
| `pest_id` | `CHAR(36)` | NULL (FK -> `pests.id`) | Field `pest_id` |
| `disease_id` | `CHAR(36)` | NULL (FK -> `diseases.id`) | Field `disease_id` |
| `outbreak_start_date` | `DATE` | NOT NULL | Field `outbreak_start_date` |
| `peak_severity` | `VARCHAR(20)` | NOT NULL | Field `peak_severity` |
| `containment_date` | `DATE` | NULL | Field `containment_date` |
| `crop_loss_percentage` | `FLOAT` | NULL | Field `crop_loss_percentage` |
| `recorded_at` | `DATETIME` | NOT NULL | Field `recorded_at` |

**Indexes:**
- `ix_infestation_history_farm_plot_id` on (farm_plot_id)

**Check Constraints:**
- `chk_infest_hist_loss_range`

---

## Chatbot and Knowledge Database

### Table: `chat_sessions`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `user_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `user_id` |
| `title` | `VARCHAR(150)` | NOT NULL | Field `title` |
| `language` | `VARCHAR(10)` | NOT NULL | Field `language` |
| `channel` | `VARCHAR(20)` | NOT NULL | Field `channel` |
| `is_active` | `BOOLEAN` | NOT NULL | Field `is_active` |
| `started_at` | `DATETIME` | NOT NULL | Field `started_at` |
| `ended_at` | `DATETIME` | NULL | Field `ended_at` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_chat_sessions_user_id` on (user_id)

**Check Constraints:**
- `chk_chat_sessions_channel`

---

### Table: `chat_messages`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `session_id` | `CHAR(36)` | NOT NULL (FK -> `chat_sessions.id`) | Field `session_id` |
| `sender_type` | `VARCHAR(20)` | NOT NULL | Field `sender_type` |
| `message_text` | `TEXT` | NOT NULL | Field `message_text` |
| `sequence_number` | `INTEGER` | NOT NULL | Field `sequence_number` |
| `cited_sources` | `JSON` | NULL | Field `cited_sources` |
| `sent_at` | `DATETIME` | NOT NULL | Field `sent_at` |

**Indexes:**
- `ix_chat_messages_session_id` on (session_id)

**Check Constraints:**
- `chk_chat_messages_sender_type`

---

### Table: `knowledge_articles`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `title` | `VARCHAR(255)` | NOT NULL | Field `title` |
| `slug` | `VARCHAR(255)` | NOT NULL | Field `slug` |
| `version` | `INTEGER` | NOT NULL | Field `version` |
| `author_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `author_id` |
| `category` | `VARCHAR(100)` | NOT NULL | Field `category` |
| `summary` | `TEXT` | NULL | Field `summary` |
| `content` | `TEXT` | NOT NULL | Field `content` |
| `status` | `VARCHAR(20)` | NOT NULL | Field `status` |
| `is_current` | `BOOLEAN` | NOT NULL | Field `is_current` |
| `published_at` | `DATETIME` | NULL | Field `published_at` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Indexes:**
- `ix_knowledge_articles_category` on (category)
- `ix_knowledge_articles_slug` on (slug)

**Check Constraints:**
- `chk_knowledge_art_status`
- `chk_knowledge_art_version_pos`

---

### Table: `knowledge_chunks`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `article_id` | `CHAR(36)` | NOT NULL (FK -> `knowledge_articles.id`) | Field `article_id` |
| `chunk_index` | `INTEGER` | NOT NULL | Field `chunk_index` |
| `content_chunk` | `TEXT` | NOT NULL | Field `content_chunk` |
| `token_count` | `INTEGER` | NOT NULL | Field `token_count` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_knowledge_chunks_article_id` on (article_id)

**Check Constraints:**
- `chk_chunk_token_pos`
- `chk_chunk_idx_nonneg`

---

### Table: `knowledge_embeddings`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `chunk_id` | `CHAR(36)` | NOT NULL (FK -> `knowledge_chunks.id`) | Field `chunk_id` |
| `embedding_model` | `VARCHAR(100)` | NOT NULL | Field `embedding_model` |
| `embedding_vector` | `TEXT` | NOT NULL | Field `embedding_vector` |
| `dimension` | `INTEGER` | NOT NULL | Field `dimension` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_knowledge_embeddings_chunk_id` on (chunk_id)

**Check Constraints:**
- `chk_embed_dim_positive`

---

### Table: `chatbot_feedback`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `message_id` | `CHAR(36)` | NOT NULL (FK -> `chat_messages.id`) | Field `message_id` |
| `user_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `user_id` |
| `rating` | `INTEGER` | NOT NULL | Field `rating` |
| `is_helpful` | `BOOLEAN` | NOT NULL | Field `is_helpful` |
| `feedback_text` | `TEXT` | NULL | Field `feedback_text` |
| `submitted_at` | `DATETIME` | NOT NULL | Field `submitted_at` |

**Indexes:**
- `ix_chatbot_feedback_message_id` on (message_id)
- `ix_chatbot_feedback_user_id` on (user_id)

**Check Constraints:**
- `chk_chatbot_rating_range`

---

## Notification Database

### Table: `notifications`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `user_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `user_id` |
| `title` | `VARCHAR(200)` | NOT NULL | Field `title` |
| `body` | `TEXT` | NOT NULL | Field `body` |
| `notification_type` | `VARCHAR(50)` | NOT NULL | Field `notification_type` |
| `priority` | `VARCHAR(20)` | NOT NULL | Field `priority` |
| `status` | `VARCHAR(20)` | NOT NULL | Field `status` |
| `channel` | `VARCHAR(20)` | NOT NULL | Field `channel` |
| `retry_count` | `INTEGER` | NOT NULL | Field `retry_count` |
| `sent_at` | `DATETIME` | NULL | Field `sent_at` |
| `read_at` | `DATETIME` | NULL | Field `read_at` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_notifications_user_id` on (user_id)

**Check Constraints:**
- `chk_notif_channel`
- `chk_notif_type`
- `chk_notif_retry_nonneg`
- `chk_notif_priority`
- `chk_notif_status`

---

### Table: `alert_rules`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `rule_name` | `VARCHAR(100)` | NOT NULL | Field `rule_name` |
| `event_type` | `VARCHAR(50)` | NOT NULL | Field `event_type` |
| `condition_expression` | `TEXT` | NOT NULL | Field `condition_expression` |
| `threshold_value` | `NUMERIC(8, 4)` | NULL | Field `threshold_value` |
| `target_role` | `VARCHAR(50)` | NOT NULL | Field `target_role` |
| `is_active` | `BOOLEAN` | NOT NULL | Field `is_active` |
| `created_by` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `created_by` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

---

### Table: `user_alert_preferences`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `user_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `user_id` |
| `push_enabled` | `BOOLEAN` | NOT NULL | Field `push_enabled` |
| `sms_enabled` | `BOOLEAN` | NOT NULL | Field `sms_enabled` |
| `email_enabled` | `BOOLEAN` | NOT NULL | Field `email_enabled` |
| `quiet_hours_start` | `VARCHAR(5)` | NULL | Field `quiet_hours_start` |
| `quiet_hours_end` | `VARCHAR(5)` | NULL | Field `quiet_hours_end` |
| `min_priority_threshold` | `VARCHAR(20)` | NOT NULL | Field `min_priority_threshold` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |
| `updated_at` | `DATETIME` | NOT NULL | Field `updated_at` |

**Check Constraints:**
- `chk_user_alert_min_priority`

---

### Table: `scheduled_tasks`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `task_name` | `VARCHAR(100)` | NOT NULL | Field `task_name` |
| `task_type` | `VARCHAR(50)` | NOT NULL | Field `task_type` |
| `target_user_id` | `CHAR(36)` | NULL (FK -> `users.id`) | Field `target_user_id` |
| `scheduled_time` | `DATETIME` | NOT NULL | Field `scheduled_time` |
| `recurrence_pattern` | `VARCHAR(50)` | NULL | Field `recurrence_pattern` |
| `status` | `VARCHAR(20)` | NOT NULL | Field `status` |
| `last_run_at` | `DATETIME` | NULL | Field `last_run_at` |
| `next_run_at` | `DATETIME` | NULL | Field `next_run_at` |
| `retry_count` | `INTEGER` | NOT NULL | Field `retry_count` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_scheduled_tasks_target_user_id` on (target_user_id)

**Check Constraints:**
- `chk_task_retry_nonneg`
- `chk_task_type_valid`
- `chk_task_status_valid`

---

### Table: `sync_logs`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `CHAR(36)` | NOT NULL **(PK)** | Field `id` |
| `user_id` | `CHAR(36)` | NOT NULL (FK -> `users.id`) | Field `user_id` |
| `device_id` | `VARCHAR(100)` | NULL | Field `device_id` |
| `sync_entity_type` | `VARCHAR(50)` | NOT NULL | Field `sync_entity_type` |
| `client_timestamp` | `DATETIME` | NOT NULL | Field `client_timestamp` |
| `server_timestamp` | `DATETIME` | NOT NULL | Field `server_timestamp` |
| `records_synced` | `INTEGER` | NOT NULL | Field `records_synced` |
| `sync_status` | `VARCHAR(30)` | NOT NULL | Field `sync_status` |
| `conflict_resolution_strategy` | `VARCHAR(50)` | NOT NULL | Field `conflict_resolution_strategy` |
| `error_details` | `TEXT` | NULL | Field `error_details` |
| `created_at` | `DATETIME` | NOT NULL | Field `created_at` |

**Indexes:**
- `ix_sync_logs_user_id` on (user_id)

**Check Constraints:**
- `chk_sync_records_nonneg`
- `chk_sync_status_valid`

---
