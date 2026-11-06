-- =============================================================================
-- AI-Based Early Pest and Disease — Demo Seed Dataset
-- =============================================================================
-- Authority: final/feature-specs/05-data-layer.md §10
-- Rule compliance:
--   - R5: strictly NO chemical advice in advisories.
--   - R6: strictly fake identifiers, synthetic images; NO real farmer PII.
--   - R7: full lineage on every prediction and forecast.
--   - All seeded rows explicitly carry is_demo = true.
-- =============================================================================

-- Ensure reference roles exist (seeded in 01-schema.sql)
INSERT INTO roles (code, description) VALUES
  ('farmer', 'Field user who submits reports and reads advisories'),
  ('extension_worker', 'Verifies reports, captures on behalf, records sentinel visits'),
  ('pathologist', 'Escalation reviewer, taxonomy owner, sole role that can confirm'),
  ('agronomist', 'Advisory and risk-band approval; cannot verify or correct labels'),
  ('admin', 'Configuration, users, queue rules; cannot verify')
ON CONFLICT (code) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 1. Demo Identity (users, user_roles, devices, consents, assignments, sessions)
-- -----------------------------------------------------------------------------

INSERT INTO users (id, phone_e164, email, password_hash, status, locale, token_version, is_demo) VALUES
  ('00000000-0000-0000-0000-000000000001', '+919999000001', 'demo-admin@pestdisease.local', 'argon2id$demo$adminhash', 'active', 'en', 1, true),
  ('00000000-0000-0000-0000-000000000002', '+919999000002', 'demo-pathologist@pestdisease.local', 'argon2id$demo$pathologisthash', 'active', 'en', 1, true),
  ('00000000-0000-0000-0000-000000000003', '+919999000003', 'demo-agronomist@pestdisease.local', 'argon2id$demo$agronomisthash', 'active', 'en', 1, true),
  ('00000000-0000-0000-0000-000000000004', '+919999000004', 'demo-extworker@pestdisease.local', 'argon2id$demo$extworkerhash', 'active', 'en', 1, true),
  ('00000000-0000-0000-0000-000000000005', '+919999000005', 'demo-farmer1@pestdisease.local', 'argon2id$demo$farmer1hash', 'active', 'kn', 1, true),
  ('00000000-0000-0000-0000-000000000006', '+919999000006', 'demo-farmer2@pestdisease.local', 'argon2id$demo$farmer2hash', 'active', 'kn', 1, true)
ON CONFLICT (id) DO UPDATE SET updated_at = now();

INSERT INTO user_roles (id, user_id, role_code, granted_by, granted_at) VALUES
  ('00000000-0000-0000-000a-000000000001', '00000000-0000-0000-0000-000000000001', 'admin', '00000000-0000-0000-0000-000000000001', now()),
  ('00000000-0000-0000-000a-000000000002', '00000000-0000-0000-0000-000000000002', 'pathologist', '00000000-0000-0000-0000-000000000001', now()),
  ('00000000-0000-0000-000a-000000000003', '00000000-0000-0000-0000-000000000003', 'agronomist', '00000000-0000-0000-0000-000000000001', now()),
  ('00000000-0000-0000-000a-000000000004', '00000000-0000-0000-0000-000000000004', 'extension_worker', '00000000-0000-0000-0000-000000000001', now()),
  ('00000000-0000-0000-000a-000000000005', '00000000-0000-0000-0000-000000000005', 'farmer', '00000000-0000-0000-0000-000000000004', now()),
  ('00000000-0000-0000-000a-000000000006', '00000000-0000-0000-0000-000000000006', 'farmer', '00000000-0000-0000-0000-000000000004', now())
ON CONFLICT (id) DO NOTHING;

INSERT INTO devices (id, user_id, platform, app_version, last_seen_at, push_token) VALUES
  ('00000000-0000-0000-000b-000000000001', '00000000-0000-0000-0000-000000000005', 'android', '1.0.0-demo', now(), 'fcm_token_demo_farmer1'),
  ('00000000-0000-0000-000b-000000000002', '00000000-0000-0000-0000-000000000006', 'android', '1.0.0-demo', now(), 'fcm_token_demo_farmer2'),
  ('00000000-0000-0000-000b-000000000003', '00000000-0000-0000-0000-000000000004', 'android', '1.0.0-demo', now(), 'fcm_token_demo_extworker')
ON CONFLICT (id) DO NOTHING;

INSERT INTO consents (id, user_id, type, version, granted, text_hash, channel, is_demo) VALUES
  ('00000000-0000-0000-000c-000000000001', '00000000-0000-0000-0000-000000000005', 'service_privacy', 'v1.0', true, 'sha256:consent_privacy_v1', 'mobile', true),
  ('00000000-0000-0000-000c-000000000002', '00000000-0000-0000-0000-000000000005', 'image_assessment', 'v1.0', true, 'sha256:consent_image_v1', 'mobile', true),
  ('00000000-0000-0000-000c-000000000003', '00000000-0000-0000-0000-000000000005', 'approximate_location', 'v1.0', true, 'sha256:consent_location_v1', 'mobile', true),
  ('00000000-0000-0000-000c-000000000004', '00000000-0000-0000-0000-000000000005', 'research_model_improvement', 'v1.0', true, 'sha256:consent_research_v1', 'mobile', true),
  ('00000000-0000-0000-000c-000000000005', '00000000-0000-0000-0000-000000000006', 'service_privacy', 'v1.0', true, 'sha256:consent_privacy_v1', 'mobile', true),
  ('00000000-0000-0000-000c-000000000006', '00000000-0000-0000-0000-000000000006', 'image_assessment', 'v1.0', true, 'sha256:consent_image_v1', 'mobile', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_area_assignments (id, user_id, geo_code, level, active_from) VALUES
  ('00000000-0000-0000-000d-000000000001', '00000000-0000-0000-0000-000000000004', 'DEMO-BLK-001', 'block', now() - interval '30 days'),
  ('00000000-0000-0000-000d-000000000002', '00000000-0000-0000-0000-000000000004', 'DEMO-BLK-002', 'block', now() - interval '30 days')
ON CONFLICT (id) DO NOTHING;

INSERT INTO sessions (id, user_id, refresh_hash, family_id, expires_at, ip_hash, user_agent) VALUES
  ('00000000-0000-0000-000e-000000000001', '00000000-0000-0000-0000-000000000005', 'sha256:refresh_token_farmer1_demo', '00000000-0000-0000-000f-000000000001', now() + interval '30 days', 'sha256:ip_demo_01', 'AntigravityMobile/1.0 (Android)'),
  ('00000000-0000-0000-000e-000000000002', '00000000-0000-0000-0000-000000000004', 'sha256:refresh_token_extworker_demo', '00000000-0000-0000-000f-000000000002', now() + interval '30 days', 'sha256:ip_demo_02', 'AntigravityMobile/1.0 (Android)')
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 2. Demo Geography, Crops, Targets, Calendars, Growing Areas & Cycles
-- -----------------------------------------------------------------------------

INSERT INTO geographies (id, code, level, name, parent_code, boundary_version, geom, valid_from, is_demo) VALUES
  ('00000000-0000-0000-0010-000000000001', 'DEMO-IN-KA', 'state', 'Karnataka (Demo)', NULL, 'DEMO-BV-2026-V1',
   ST_Multi(ST_GeomFromText('MULTIPOLYGON(((74.0 11.5, 78.5 11.5, 78.5 18.5, 74.0 18.5, 74.0 11.5)))', 4326)), '2026-01-01', true),
  ('00000000-0000-0000-0010-000000000002', 'DEMO-IN-KA-MY', 'district', 'Mysuru District (Demo)', 'DEMO-IN-KA', 'DEMO-BV-2026-V1',
   ST_Multi(ST_GeomFromText('MULTIPOLYGON(((75.8 11.8, 77.2 11.8, 77.2 12.6, 75.8 12.6, 75.8 11.8)))', 4326)), '2026-01-01', true),
  ('00000000-0000-0000-0010-000000000003', 'DEMO-IN-KA-MY-HD', 'mandal', 'Hunsur Taluk (Demo)', 'DEMO-IN-KA-MY', 'DEMO-BV-2026-V1',
   ST_Multi(ST_GeomFromText('MULTIPOLYGON(((76.1 12.2, 76.4 12.2, 76.4 12.4, 76.1 12.4, 76.1 12.2)))', 4326)), '2026-01-01', true),
  ('00000000-0000-0000-0010-000000000004', 'DEMO-BLK-001', 'block', 'Hunsur Rural Block (Demo)', 'DEMO-IN-KA-MY-HD', 'DEMO-BV-2026-V1',
   ST_Multi(ST_GeomFromText('MULTIPOLYGON(((76.15 12.25, 76.30 12.25, 76.30 12.35, 76.15 12.35, 76.15 12.25)))', 4326)), '2026-01-01', true),
  ('00000000-0000-0000-0010-000000000005', 'DEMO-BLK-002', 'block', 'Bilikere Block (Demo)', 'DEMO-IN-KA-MY-HD', 'DEMO-BV-2026-V1',
   ST_Multi(ST_GeomFromText('MULTIPOLYGON(((76.30 12.25, 76.40 12.25, 76.40 12.35, 76.30 12.35, 76.30 12.25)))', 4326)), '2026-01-01', true)
ON CONFLICT (code, boundary_version) DO NOTHING;

INSERT INTO crops (code, name, supported, supported_from, is_demo) VALUES
  ('DEMO_RICE', 'Rice / Paddy (Demo)', true, '2026-01-01', true),
  ('DEMO_TOMATO', 'Tomato (Demo)', true, '2026-01-01', true)
ON CONFLICT (code) DO UPDATE SET supported = EXCLUDED.supported;

INSERT INTO targets (id, code, crop_code, name, kind, class_kind, supported, taxonomy_note, is_demo) VALUES
  ('00000000-0000-0000-0011-000000000001', 'DEMO_RICE_BLAST', 'DEMO_RICE', 'Rice Blast (Magnaporthe oryzae)', 'disease', 'pathogen_identity', true, 'Demo blast taxonomy', true),
  ('00000000-0000-0000-0011-000000000002', 'DEMO_RICE_BPH', 'DEMO_RICE', 'Brown Plant Hopper (Nilaparvata lugens)', 'pest', 'pest_damage', true, 'Demo hopper damage', true),
  ('00000000-0000-0000-0011-000000000003', 'DEMO_RICE_HEALTHY', 'DEMO_RICE', 'Healthy Paddy Leaf', 'healthy', 'non_condition', true, 'Demo healthy leaf class', true),
  ('00000000-0000-0000-0011-000000000004', 'DEMO_TOM_EBLIGHT', 'DEMO_TOMATO', 'Tomato Early Blight (Alternaria solani)', 'disease', 'pathogen_identity', true, 'Demo early blight target', true),
  ('00000000-0000-0000-0011-000000000005', 'DEMO_TOM_HEALTHY', 'DEMO_TOMATO', 'Healthy Tomato Leaf', 'healthy', 'non_condition', true, 'Demo healthy tomato leaf', true),
  ('00000000-0000-0000-0011-000000000006', 'DEMO_UNKNOWN', 'DEMO_RICE', 'Uncertain/Unknown Condition', 'unknown', 'non_condition', false, 'Abstention fall-through demo class', true)
ON CONFLICT (crop_code, code) DO NOTHING;

INSERT INTO crop_calendars (id, crop_code, geo_code, season, planting_window, stage_windows, is_demo) VALUES
  ('00000000-0000-0000-0012-000000000001', 'DEMO_RICE', 'DEMO-BLK-001', 'Kharif-2026',
   '{"start_doy": 160, "end_doy": 200}'::jsonb,
   '{"nursery": [160, 185], "tillering": [186, 230], "panicle": [231, 260], "maturity": [261, 290]}'::jsonb, true),
  ('00000000-0000-0000-0012-000000000002', 'DEMO_TOMATO', 'DEMO-BLK-001', 'Rabi-2026',
   '{"start_doy": 240, "end_doy": 270}'::jsonb,
   '{"vegetative": [240, 275], "flowering": [276, 310], "fruiting": [311, 350]}'::jsonb, true)
ON CONFLICT (crop_code, geo_code, season) DO NOTHING;

INSERT INTO growing_areas (id, owner_user_id, geo_code, precision, geom, label, is_demo) VALUES
  ('00000000-0000-0000-0013-000000000001', '00000000-0000-0000-0000-000000000005', 'DEMO-BLK-001', 'block',
   ST_GeomFromText('POINT(76.22 12.30)', 4326), 'Demo North Field - Rice', true),
  ('00000000-0000-0000-0013-000000000002', '00000000-0000-0000-0000-000000000006', 'DEMO-BLK-002', 'block',
   ST_GeomFromText('POINT(76.35 12.28)', 4326), 'Demo Plot B - Tomato', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO crop_cycles (id, growing_area_id, crop_code, variety, planting_date, stage, stage_updated_at, is_demo) VALUES
  ('00000000-0000-0000-0014-000000000001', '00000000-0000-0000-0013-000000000001', 'DEMO_RICE', 'Jaya (Demo Variety)', '2026-07-01', 'tillering', now() - interval '10 days', true),
  ('00000000-0000-0000-0014-000000000002', '00000000-0000-0000-0013-000000000002', 'DEMO_TOMATO', 'Arka Rakshak (Demo Variety)', '2026-08-15', 'flowering', now() - interval '5 days', true)
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 3. Demo Observations, Image Assets, Quality Results, Predictions, Requests
-- -----------------------------------------------------------------------------

INSERT INTO observations (
  id, client_report_id, user_id, subject_user_id, growing_area_id, crop_code,
  variety, growth_stage, notes, captured_at, submitted_at, event_date, status,
  geo_code, urgency_score, is_demo
) VALUES
  (
    '00000000-0000-0000-0020-000000000001', 'DEMO-REP-2026-001',
    '00000000-0000-0000-0000-000000000005', NULL,
    '00000000-0000-0000-0013-000000000001', 'DEMO_RICE',
    'Jaya', 'tillering', 'Demo observation: Spindle-shaped lesions with ash grey center on upper leaf blade.',
    now() - interval '6 days', now() - interval '6 days', '2026-09-10', 'reviewed',
    'DEMO-BLK-001', 82.500, true
  ),
  (
    '00000000-0000-0000-0020-000000000002', 'DEMO-REP-2026-002',
    '00000000-0000-0000-0000-000000000006', NULL,
    '00000000-0000-0000-0013-000000000002', 'DEMO_TOMATO',
    'Arka Rakshak', 'flowering', 'Demo observation: Concentric dark brown rings on bottom foliage.',
    now() - interval '4 days', now() - interval '4 days', '2026-09-12', 'pending_review',
    'DEMO-BLK-002', 64.000, true
  ),
  (
    '00000000-0000-0000-0020-000000000003', 'DEMO-REP-2026-003',
    '00000000-0000-0000-0000-000000000005', NULL,
    '00000000-0000-0000-0013-000000000001', 'DEMO_RICE',
    'Jaya', 'tillering', 'Demo observation: Blurry underexposed photo during rain.',
    now() - interval '2 days', now() - interval '2 days', '2026-09-14', 'abstained',
    'DEMO-BLK-001', 5.000, true
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO image_assets (
  id, observation_id, storage_key, original_width, original_height, bytes,
  content_hash, mime, source, compression, upload_status, exif_gps_present, exif_stripped, is_demo
) VALUES
  (
    '00000000-0000-0000-0021-000000000001', '00000000-0000-0000-0020-000000000001',
    'observations/2026/09/00000000-0000-0000-0020-000000000001/00000000-0000-0000-0021-000000000001/original.jpg',
    1920, 1080, 1420500,
    'sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    'image/jpeg', 'camera', '{"quality": 85, "format": "jpeg"}'::jsonb,
    'complete', true, true, true
  ),
  (
    '00000000-0000-0000-0021-000000000002', '00000000-0000-0000-0020-000000000002',
    'observations/2026/09/00000000-0000-0000-0020-000000000002/00000000-0000-0000-0021-000000000002/original.jpg',
    2048, 1536, 1789200,
    'sha256:ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb',
    'image/jpeg', 'camera', '{"quality": 85, "format": "jpeg"}'::jsonb,
    'complete', false, false, true
  ),
  (
    '00000000-0000-0000-0021-000000000003', '00000000-0000-0000-0020-000000000003',
    'observations/2026/09/00000000-0000-0000-0020-000000000003/00000000-0000-0000-0021-000000000003/original.jpg',
    1280, 720, 542000,
    'sha256:3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d',
    'image/jpeg', 'camera', '{"quality": 80, "format": "jpeg"}'::jsonb,
    'complete', false, false, true
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO image_quality_results (
  id, image_id, gate_version, result, flags, thresholds, is_demo
) VALUES
  (
    '00000000-0000-0000-0022-000000000001', '00000000-0000-0000-0021-000000000001',
    'v1.0-demo', 'pass',
    '{"blur": false, "underexposed": false, "overexposed": false}'::jsonb,
    '{"blur_threshold": 0.85, "min_resolution": 720}'::jsonb, true
  ),
  (
    '00000000-0000-0000-0022-000000000002', '00000000-0000-0000-0021-000000000002',
    'v1.0-demo', 'pass',
    '{"blur": false, "underexposed": false, "overexposed": false}'::jsonb,
    '{"blur_threshold": 0.85, "min_resolution": 720}'::jsonb, true
  ),
  (
    '00000000-0000-0000-0022-000000000003', '00000000-0000-0000-0021-000000000003',
    'v1.0-demo', 'abstain',
    '{"blur": true, "underexposed": true, "overexposed": false}'::jsonb,
    '{"blur_threshold": 0.85, "min_resolution": 720}'::jsonb, true
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO image_predictions (
  id, image_id, model_version, candidates, probabilities, confidence_band,
  calibrated, calibration_version, abstained, abstain_reason, decision_thresholds,
  ood_score, generated_at, is_demo
) VALUES
  (
    '00000000-0000-0000-0023-000000000001', '00000000-0000-0000-0021-000000000001',
    'demo-classifier-v1',
    '[{"code": "DEMO_RICE_BLAST", "probability": 0.932}, {"code": "DEMO_RICE_HEALTHY", "probability": 0.045}]'::jsonb,
    '{"DEMO_RICE_BLAST": 0.932, "DEMO_RICE_HEALTHY": 0.045, "DEMO_RICE_BPH": 0.023}'::jsonb,
    'high', true, 'demo-platt-cal-v1', false, NULL,
    '{"tau_c": {"DEMO_RICE_BLAST": 0.85, "DEMO_RICE_BPH": 0.80}, "margin": 0.20, "entropy": 0.40, "ood_max": 0.70}'::jsonb,
    0.142, now() - interval '6 days', true
  ),
  (
    '00000000-0000-0000-0023-000000000002', '00000000-0000-0000-0021-000000000002',
    'demo-classifier-v1',
    '[{"code": "DEMO_TOM_EBLIGHT", "probability": 0.745}, {"code": "DEMO_TOM_HEALTHY", "probability": 0.210}]'::jsonb,
    '{"DEMO_TOM_EBLIGHT": 0.745, "DEMO_TOM_HEALTHY": 0.210}'::jsonb,
    'medium', true, 'demo-platt-cal-v1', false, NULL,
    '{"tau_c": {"DEMO_TOM_EBLIGHT": 0.70}, "margin": 0.15, "entropy": 0.50, "ood_max": 0.70}'::jsonb,
    0.285, now() - interval '4 days', true
  ),
  (
    '00000000-0000-0000-0023-000000000003', '00000000-0000-0000-0021-000000000003',
    'demo-classifier-v1',
    '[]'::jsonb, NULL, 'low', false, NULL,
    true, 'quality_gate_failed',
    '{"tau_c": {"DEMO_RICE_BLAST": 0.85}, "margin": 0.20, "entropy": 0.40, "ood_max": 0.70}'::jsonb,
    0.910, now() - interval '2 days', true
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO review_requests (
  id, observation_id, requested_by, reason, status
) VALUES
  ('00000000-0000-0000-0024-000000000001', '00000000-0000-0000-0020-000000000001', '00000000-0000-0000-0000-000000000004', 'High-confidence blast triage escalation', 'fulfilled'),
  ('00000000-0000-0000-0024-000000000002', '00000000-0000-0000-0020-000000000002', '00000000-0000-0000-0000-000000000004', 'Medium-confidence early blight confirmation request', 'open')
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 4. Demo Reviews, Evidence, Labels, Events & Projections
-- -----------------------------------------------------------------------------

INSERT INTO reviews (
  id, observation_id, reviewer_id, decision, reason_code, corrected_label, severity, note, created_at, is_demo
) VALUES
  (
    '00000000-0000-0000-0030-000000000001', '00000000-0000-0000-0020-000000000001',
    '00000000-0000-0000-0000-000000000002', 'confirmed',
    'microscopic_spore_morphology', 'DEMO_RICE_BLAST', 'moderate',
    'Confirmed Magnaporthe oryzae conidia under microscope; spindle lesions typical.',
    now() - interval '5 days', true
  ),
  (
    '00000000-0000-0000-0030-000000000002', '00000000-0000-0000-0020-000000000002',
    '00000000-0000-0000-0000-000000000004', 'probable',
    'visual_symptom_match', 'DEMO_TOM_EBLIGHT', 'low',
    'Concentric target-like rings on lower leaves; awaiting pathology lab confirmation.',
    now() - interval '3 days', true
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO review_evidence (
  id, review_id, type, value, source, is_demo
) VALUES
  (
    '00000000-0000-0000-0031-000000000001', '00000000-0000-0000-0030-000000000001',
    'lab_result', 'Microscopy spore count: 3-celled pyriform conidia verified.',
    'District Diagnostic Lab (Demo)', true
  ),
  (
    '00000000-0000-0000-0031-000000000002', '00000000-0000-0000-0030-000000000001',
    'field_observation', 'Leaf canopy shows 15% leaf area affected on susceptible variety.',
    'Extension Scout Visit (Demo)', true
  ),
  (
    '00000000-0000-0000-0031-000000000003', '00000000-0000-0000-0030-000000000002',
    'image_note', 'Concentric chlorotic halos clearly visible on 3 leaflet samples.',
    'Mobile Review Portal (Demo)', true
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO labels (
  id, observation_id, image_id, review_id, target_code, class_kind, label_origin,
  verification_tier, severity, severity_basis, reviewer_id, reviewed_at,
  handbook_version, taxonomy_version, label_status, hard_negative, abstention_role, is_demo
) VALUES
  (
    '00000000-0000-0000-0032-000000000001', '00000000-0000-0000-0020-000000000001',
    '00000000-0000-0000-0021-000000000001', '00000000-0000-0000-0030-000000000001',
    'DEMO_RICE_BLAST', 'pathogen_identity', 'lab_confirmed', 'confirmed',
    'moderate', 'leaf_area_lesion_percentage', '00000000-0000-0000-0000-000000000002',
    now() - interval '5 days', 'v1.0-demo', 'v1.0-demo', 'active', false, 'none', true
  ),
  (
    '00000000-0000-0000-0032-000000000002', '00000000-0000-0000-0020-000000000002',
    '00000000-0000-0000-0021-000000000002', '00000000-0000-0000-0030-000000000002',
    'DEMO_TOM_EBLIGHT', 'pathogen_identity', 'expert_confirmed', 'probable',
    'low', 'visual_count_of_rings', '00000000-0000-0000-0000-000000000004',
    now() - interval '3 days', 'v1.0-demo', 'v1.0-demo', 'active', false, 'none', true
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO review_events (
  id, observation_id, from_status, to_status, actor_id, reason, is_demo
) VALUES
  (
    '00000000-0000-0000-0033-000000000001', '00000000-0000-0000-0020-000000000001',
    'pending_review', 'confirmed', '00000000-0000-0000-0000-000000000002',
    'Laboratory confirmation completed by state pathologist.', true
  ),
  (
    '00000000-0000-0000-0033-000000000002', '00000000-0000-0000-0020-000000000002',
    'pending_review', 'probable', '00000000-0000-0000-0000-000000000004',
    'Field officer triaged and verified probable early blight.', true
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO observation_verification (
  observation_id, status, evidence_tier, verified_at, verified_by, review_id
) VALUES
  (
    '00000000-0000-0000-0020-000000000001', 'confirmed', 'confirmed',
    now() - interval '5 days', '00000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0030-000000000001'
  ),
  (
    '00000000-0000-0000-0020-000000000002', 'probable', 'probable',
    now() - interval '3 days', '00000000-0000-0000-0000-000000000004',
    '00000000-0000-0000-0030-000000000002'
  )
ON CONFLICT (observation_id) DO UPDATE SET
  status = EXCLUDED.status,
  evidence_tier = EXCLUDED.evidence_tier,
  verified_at = EXCLUDED.verified_at;

INSERT INTO sentinel_sites (
  id, crop_code, geo_code, precision, geom, active_from, panel_version, approved_by, is_demo
) VALUES
  (
    '00000000-0000-0000-0034-000000000001', 'DEMO_RICE', 'DEMO-BLK-001', 'approximate',
    ST_GeomFromText('POINT(76.24 12.31)', 4326), '2026-06-01', 'DEMO-PANEL-2026-V1',
    '00000000-0000-0000-0000-000000000002', true
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO sentinel_visits (
  id, site_id, visit_date, scheduled, observer_id, target_code, observed,
  evidence_ref, coverage_pass, is_demo
) VALUES
  (
    '00000000-0000-0000-0035-000000000001', '00000000-0000-0000-0034-000000000001',
    '2026-09-08', true, '00000000-0000-0000-0000-000000000004',
    'DEMO_RICE_BPH', 'absent',
    'Demo sentinel protocol: 20 hills sampled randomly, zero BPH nymphs or adults found.',
    true, true
  )
ON CONFLICT (site_id, visit_date, target_code) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 4.b Historical Occurrence Records (Plant Clinics, Surveys, Provenance & Dedupe)
-- -----------------------------------------------------------------------------

INSERT INTO historical_occurrences (
  id, crop_code, target_code, geo_code, boundary_version, verification_tier,
  event_date, report_date, source_link, source_dataset, dedupe_key, dedupe_history,
  severity, evidence_summary, notes, is_demo
) VALUES
  (
    '00000000-0000-0000-0038-000000000001', 'DEMO_RICE', 'DEMO_RICE_BLAST', 'DEMO-BLK-001',
    'DEMO-BV-2026-V1', 'confirmed', '2023-08-12', '2023-08-15',
    'https://farm-archives.karnataka.gov.in/clinics/2023/rep-10492',
    'karnataka_plant_clinic_archive_2020_2024',
    'sha256:hist-clinic-2023-08-12-rice-blast-blk1',
    '[{"source": "survey_field_849", "matched_at": "2023-08-18T10:00:00Z", "status": "deduplicated_into_clinic_record"}]'::jsonb,
    'moderate',
    'Microscopy confirmation of Piricularia oryzae conidia; diamond/spindle shaped lesions on flag leaf.',
    'Historical outbreak in Hunsur rural block during continuous wet week of Kharif 2023.',
    true
  ),
  (
    '00000000-0000-0000-0038-000000000002', 'DEMO_TOMATO', 'DEMO_TOM_EBLIGHT', 'DEMO-BLK-001',
    'DEMO-BV-2026-V1', 'probable', '2023-10-04', '2023-10-05',
    'https://farm-archives.karnataka.gov.in/surveys/2023/surv-0421',
    'uas_bangalore_extension_surveys_2023',
    'sha256:hist-survey-2023-10-04-tom-eblight-blk1',
    '[]'::jsonb,
    'mild',
    'Concentric ring target-pattern leaf spots on lower tomato canopy.',
    'Field extension survey record; high humidity conditions.',
    true
  ),
  (
    '00000000-0000-0000-0038-000000000003', 'DEMO_RICE', 'DEMO_RICE_BPH', 'DEMO-BLK-002',
    'DEMO-BV-2026-V1', 'confirmed', '2024-09-20', '2024-09-22',
    'https://farm-archives.karnataka.gov.in/clinics/2024/rep-12044',
    'karnataka_plant_clinic_archive_2020_2024',
    'sha256:hist-clinic-2024-09-20-rice-bph-blk2',
    '[]'::jsonb,
    'severe',
    'Hopper burn circular patches; density >15 nymphs per hill.',
    'Confirmed in Bilikere block; drainage advisories issued.',
    true
  )
ON CONFLICT (dedupe_key) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 5. Demo Weather, Feature Snapshots, Forecast Runs & Forecasts
-- -----------------------------------------------------------------------------

INSERT INTO weather_snapshots (
  id, grid_id, geo_code, boundary_version, spatial_matching_method, station_id,
  station_distance_km, source, source_timestamp, fetched_at, freshness_seconds,
  variables, completeness, is_stale, is_demo
) VALUES
  (
    '00000000-0000-0000-0040-000000000001', 'GRID-DEMO-001', 'DEMO-BLK-001',
    'DEMO-BV-2026-V1', 'centroid_nearest_station', 'IMD-KAR-CHIKKABALLAPUR-01',
    6.80, 'IMD-AutoStation-Demo', now() - interval '2 hours', now() - interval '1 hour', 3600,
    '{
      "temperature_min_c": 19.5,
      "temperature_max_c": 29.8,
      "temperature_mean_c": 24.6,
      "relative_humidity_min_pct": 68.0,
      "relative_humidity_max_pct": 96.0,
      "relative_humidity_mean_pct": 84.5,
      "rainfall_mm": 18.5,
      "wet_day_runs": 4,
      "wind_speed_ms": 3.8,
      "leaf_wetness_proxy_hours": 9.5
    }'::jsonb,
    1.000, false, true
  ),
  (
    '00000000-0000-0000-0040-000000000002', 'GRID-DEMO-002', 'DEMO-BLK-002',
    'DEMO-BV-2026-V1', 'grid_areal_weighted_mean', 'IMD-GRID-0.1DEG-76.35',
    4.20, 'IMD-AutoStation-Demo', now() - interval '3 hours', now() - interval '1 hour', 7200,
    '{
      "temperature_min_c": 21.0,
      "temperature_max_c": 31.2,
      "temperature_mean_c": 26.1,
      "relative_humidity_min_pct": 55.0,
      "relative_humidity_max_pct": 86.0,
      "relative_humidity_mean_pct": 72.0,
      "rainfall_mm": 2.5,
      "wet_day_runs": 1,
      "wind_speed_ms": 2.9,
      "leaf_wetness_proxy_hours": 4.0
    }'::jsonb,
    1.000, false, true
  ),
  (
    -- Explicit STALE weather snapshot (age 48 hours > 24 hours threshold)
    '00000000-0000-0000-0040-000000000003', 'GRID-DEMO-001', 'DEMO-BLK-001',
    'DEMO-BV-2026-V1', 'centroid_nearest_station', 'IMD-KAR-CHIKKABALLAPUR-01',
    6.80, 'IMD-AutoStation-Demo', now() - interval '48 hours', now() - interval '1 hour', 169200,
    '{
      "temperature_min_c": 18.0,
      "temperature_max_c": 28.0,
      "temperature_mean_c": 23.0,
      "relative_humidity_min_pct": 60.0,
      "relative_humidity_max_pct": 90.0,
      "relative_humidity_mean_pct": 78.0,
      "rainfall_mm": 0.0,
      "wet_day_runs": 0,
      "wind_speed_ms": 2.0,
      "leaf_wetness_proxy_hours": 2.0
    }'::jsonb,
    1.000, true, true
  ),
  (
    -- Explicit INCOMPLETE weather snapshot (missing rainfall, wet_day_runs, wind)
    '00000000-0000-0000-0040-000000000004', 'GRID-DEMO-002', 'DEMO-BLK-002',
    'DEMO-BV-2026-V1', 'station_idw', 'IMD-KAR-CHIKKABALLAPUR-02',
    12.40, 'IMD-AutoStation-Demo', now() - interval '2 hours', now() - interval '1 hour', 3600,
    '{
      "temperature_min_c": 22.0,
      "temperature_mean_c": 27.0,
      "relative_humidity_mean_pct": 65.0
    }'::jsonb,
    0.400, false, true
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO feature_snapshots (
  id, crop_code, target_code, geo_code, boundary_version, horizon_days, issue_time,
  features, source_refs, is_demo
) VALUES
  (
    '00000000-0000-0000-0041-000000000001', 'DEMO_RICE', 'DEMO_RICE_BLAST', 'DEMO-BLK-001',
    'DEMO-BV-2026-V1', 7, now() - interval '2 hours',
    '{
      "consecutive_wet_days": 4,
      "mean_temp_7d": 24.6,
      "mean_rh_7d": 84.5,
      "rainfall_sum_7d": 18.5,
      "leaf_wetness_hours_7d": 9.5,
      "cases_prev_14d": 2,
      "sentinel_negatives": 1
    }'::jsonb,
    '{"weather_snapshot_id": "00000000-0000-0000-0040-000000000001", "boundary_version": "DEMO-BV-2026-V1"}'::jsonb,
    true
  ),
  (
    -- Feature snapshot with stale weather reference for insufficient_data forecast demonstration
    '00000000-0000-0000-0041-000000000002', 'DEMO_RICE', 'DEMO_RICE_BLAST', 'DEMO-BLK-001',
    'DEMO-BV-2026-V1', 7, now() - interval '1 hour',
    '{
      "consecutive_wet_days": null,
      "mean_temp_7d": null,
      "gate_status": "insufficient_data",
      "refusal_reason": "weather_stale"
    }'::jsonb,
    '{"weather_snapshot_id": "00000000-0000-0000-0040-000000000003", "boundary_version": "DEMO-BV-2026-V1"}'::jsonb,
    true
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO forecast_runs (
  id, started_at, finished_at, status, model_version, areas_total, areas_scored, areas_insufficient, is_demo
) VALUES
  (
    '00000000-0000-0000-0042-000000000001', now() - interval '2 hours', (now() - interval '2 hours') + interval '4 minutes',
    'succeeded', 'demo-forecast-model-v1', 5, 4, 1, true
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO forecasts (
  id, crop_code, target_code, geo_code, boundary_version, horizon_days, issue_time,
  valid_from, valid_to, risk_band, probability, confidence_band, coverage, drivers,
  model_version, feature_snapshot_id, is_demo
) VALUES
  (
    '00000000-0000-0000-0043-000000000001', 'DEMO_RICE', 'DEMO_RICE_BLAST', 'DEMO-BLK-001',
    'DEMO-BV-2026-V1', 7, now() - interval '2 hours', now() - interval '2 hours', now() + interval '5 days',
    'high', 0.765, 'medium', 'good',
    '[{"feature": "consecutive_wet_days", "weight": 0.45}, {"feature": "mean_rh_7d", "weight": 0.38}, {"feature": "leaf_wetness_hours_7d", "weight": 0.17}]'::jsonb,
    'demo-forecast-model-v1', '00000000-0000-0000-0041-000000000001', true
  ),
  (
    -- Explicit insufficient_data forecast: NO silent imputation, probability IS NULL
    '00000000-0000-0000-0043-000000000002', 'DEMO_RICE', 'DEMO_RICE_BLAST', 'DEMO-BLK-001',
    'DEMO-BV-2026-V1', 7, now() - interval '1 hour', now() - interval '1 hour', now() + interval '5 days',
    'insufficient_data', NULL, 'not_calibrated', 'low',
    '[{"reason": "weather_stale", "message": "Weather snapshot age exceeds 24h freshness SLA; forecast refused without imputation."}]'::jsonb,
    'demo-forecast-model-v1', '00000000-0000-0000-0041-000000000002', true
  )
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 6. Demo Advisories (R5 NON-CHEMICAL ONLY), Versions, Approvals, Policies & Alerts
-- -----------------------------------------------------------------------------

INSERT INTO advisories (
  id, crop_code, target_code, geo_scope, language, title, current_version_id, status, is_demo
) VALUES
  (
    '00000000-0000-0000-0050-000000000001', 'DEMO_RICE', 'DEMO_RICE_BLAST', 'DEMO-BLK-001', 'en',
    'Rice Blast Cultural Canopy and Water Management (Demo)',
    NULL, 'approved', true
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO advisory_versions (
  id, advisory_id, version, body_md, action_types, author_id, valid_from, valid_to,
  content_hash, is_demo
) VALUES
  (
    '00000000-0000-0000-0051-000000000001', '00000000-0000-0000-0050-000000000001', 1,
    '## Rice Blast Cultural Management Protocol (Demo Advisory)

> [!IMPORTANT]
> **Safety Rule R5:** Strictly non-chemical recommendations only. Only non-chemical cultural, physical and biological sanitation practices are prescribed.

### Recommended Cultural Actions:
1. **Water Regime:** Maintain continuous shallow standing water (2–3 cm) in paddy beds during high humidity windows; prevent fields from drying out to uncracked moisture stress.
2. **Nutrient Balance:** Delay top-dressing of nitrogenous fertilizers until leaf wetness periods subside. Excessive leaf nitrogen softens tissues for fungal penetration.
3. **Canopy Aeration:** Rogue infected wild rice species and weeds on bunds (*Leersia hexandra*) that act as secondary inoculum sources.
4. **Field Drainage:** In low-lying pockets with stagnant dew, provide surface aeration trenches between every 8 rows.',
    '["water_management", "nutrient_adjustment", "canopy_aeration", "sanitation"]'::jsonb,
    '00000000-0000-0000-0000-000000000003',
    now() - interval '10 days', now() + interval '30 days',
    'sha256:7b5d63f0e8f26ab45091c06830be1e5647a4693ef27c38c8230722a5786f1e29',
    true
  )
ON CONFLICT (advisory_id, version) DO NOTHING;

-- Link advisory to current version
UPDATE advisories
SET current_version_id = '00000000-0000-0000-0051-000000000001'
WHERE id = '00000000-0000-0000-0050-000000000001';

INSERT INTO advisory_approvals (
  id, version_id, approver_id, role, approved_at, notes, is_demo
) VALUES
  (
    '00000000-0000-0000-0052-000000000001', '00000000-0000-0000-0051-000000000001',
    '00000000-0000-0000-0000-000000000003', 'agronomist', now() - interval '9 days',
    'Approved agronomic cultural water schedule for demo Kharif cycle.', true
  ),
  (
    '00000000-0000-0000-0052-000000000002', '00000000-0000-0000-0051-000000000001',
    '00000000-0000-0000-0000-000000000002', 'pathologist', now() - interval '8 days',
    'Approved pathology recommendations: non-chemical sanitation confirmed appropriate.', true
  )
ON CONFLICT (version_id, approver_id) DO NOTHING;

INSERT INTO alert_policies (
  id, geo_code, target_code, min_band, min_coverage, cooldown_hours, channels, approved_by, active, is_demo
) VALUES
  (
    '00000000-0000-0000-0053-000000000001', 'DEMO-BLK-001', 'DEMO_RICE_BLAST', 'high', 'good', 48,
    '["push", "sms"]'::jsonb, '00000000-0000-0000-0000-000000000003', true, true
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO alerts (
  id, forecast_id, geo_code, target_code, band, window_from, window_to,
  message_version, dedupe_key, is_demo
) VALUES
  (
    '00000000-0000-0000-0054-000000000001', '00000000-0000-0000-0043-000000000001',
    'DEMO-BLK-001', 'DEMO_RICE_BLAST', 'high', now() - interval '2 days', now() + interval '5 days',
    'demo-blast-alert-v1', 'DEMO-ALERT-2026-09-14-BLK001-BLAST', true
  )
ON CONFLICT (dedupe_key) DO NOTHING;

INSERT INTO alert_deliveries (
  id, alert_id, user_id, channel, status, provider_ref, sent_at, delivered_at, is_demo
) VALUES
  (
    '00000000-0000-0000-0055-000000000001', '00000000-0000-0000-0054-000000000001',
    '00000000-0000-0000-0000-000000000005', 'push', 'delivered', 'fcm_msg_demo_001',
    now() - interval '2 days', now() - interval '2 days', true
  )
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 7. Demo Model Registry, Audit Events & Export Jobs
-- -----------------------------------------------------------------------------

INSERT INTO model_registry (
  id, kind, version, artefact_key, checksum, metrics, status, approved_by, approved_at, is_demo
) VALUES
  (
    '00000000-0000-0000-0060-000000000001', 'image_gate', 'v1.0.0-demo',
    'models/image_gate/v1.0.0-demo/gate.onnx',
    'sha256:d41d8cd98f00b204e9800998ecf8427e11111111111111111111111111111111',
    '{"auc": 0.965, "f1": 0.940, "eval_dataset": "gate-eval-v1-demo"}'::jsonb,
    'approved', '00000000-0000-0000-0000-000000000001', now() - interval '30 days', true
  ),
  (
    '00000000-0000-0000-0060-000000000002', 'image_classifier', 'demo-classifier-v1',
    'models/image_classifier/demo-classifier-v1/weights.onnx',
    'sha256:9e107d9d372bb6826bd81d3542a419d622222222222222222222222222222222',
    '{"macro_f1": 0.892, "top1_acc": 0.915, "calibration_ece": 0.038}'::jsonb,
    'approved', '00000000-0000-0000-0000-000000000002', now() - interval '20 days', true
  ),
  (
    '00000000-0000-0000-0060-000000000003', 'forecast', 'demo-forecast-model-v1',
    'models/forecast/demo-forecast-model-v1/model.joblib',
    'sha256:4b227777d4dd1fc61c6f884f48641d0233333333333333333333333333333333',
    '{"roc_auc": 0.875, "pr_auc": 0.740, "brier_score": 0.125}'::jsonb,
    'approved', '00000000-0000-0000-0000-000000000003', now() - interval '15 days', true
  )
ON CONFLICT (kind, version) DO NOTHING;

INSERT INTO audit_events (
  id, actor_id, actor_role, action, entity_type, entity_id, reason, request_id, ip_hash, is_demo
) VALUES
  (
    '00000000-0000-0000-0061-000000000001', '00000000-0000-0000-0000-000000000001',
    'admin', 'seed_demo_environment', 'database', 'global',
    'Initialized Phase 1 test and demo dataset slice', 'req_demo_init_001', 'sha256:ip_localhost', true
  ),
  (
    '00000000-0000-0000-0061-000000000002', '00000000-0000-0000-0000-000000000002',
    'pathologist', 'approve_model_version', 'model_registry', '00000000-0000-0000-0060-000000000002',
    'Verified classifier calibration on evaluation benchmark', 'req_demo_model_appr', 'sha256:ip_localhost', true
  )
ON CONFLICT (id) DO NOTHING;

INSERT INTO export_jobs (
  id, requested_by, purpose, filters, status, row_count, is_demo
) VALUES
  (
    '00000000-0000-0000-0062-000000000001', '00000000-0000-0000-0000-000000000002',
    'Generate frozen demo test manifest for Gate 1 evaluation',
    '{"crop_code": "DEMO_RICE", "status": "confirmed"}'::jsonb,
    'complete', 1, true
  )
ON CONFLICT (id) DO NOTHING;
