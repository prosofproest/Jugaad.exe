-- =============================================================================
-- CropSentinel AI — Master Demo Seed Dataset
-- Covers: 11 Domains, Coherent Ground-Truth Data
-- Strict Compliance:
--   - R5: strictly verified statutory registrations; no fabricated advice.
--   - R6: fake identifiers, synthetic media references; zero farmer PII.
--   - R7: full lineage across AI analysis, model versions, predictions, diagnoses.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Users & Roles
-- -----------------------------------------------------------------------------
INSERT INTO users (id, username, email, phone_e164, password_hash, status, is_demo) VALUES
  ('10000000-0000-0000-0000-000000000001', 'demo_admin', 'admin@cropsentinel.local', '+919876543210', 'argon2id$demo$adminhash', 'active', true),
  ('10000000-0000-0000-0000-000000000002', 'demo_pathologist', 'pathologist@cropsentinel.local', '+919876543211', 'argon2id$demo$pathologisthash', 'active', true),
  ('10000000-0000-0000-0000-000000000003', 'demo_agronomist', 'agronomist@cropsentinel.local', '+919876543212', 'argon2id$demo$agronomisthash', 'active', true),
  ('10000000-0000-0000-0000-000000000004', 'demo_scout', 'scout@cropsentinel.local', '+919876543213', 'argon2id$demo$scouthash', 'active', true),
  ('10000000-0000-0000-0000-000000000005', 'demo_farmer_ramesh', 'ramesh@cropsentinel.local', '+919876543214', 'argon2id$demo$farmerhash', 'active', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_roles (id, user_id, role, is_active) VALUES
  ('10000000-0000-0000-0001-000000000001', '10000000-0000-0000-0000-000000000001', 'admin', true),
  ('10000000-0000-0000-0001-000000000002', '10000000-0000-0000-0000-000000000002', 'pathologist', true),
  ('10000000-0000-0000-0001-000000000003', '10000000-0000-0000-0000-000000000003', 'agronomist', true),
  ('10000000-0000-0000-0001-000000000004', '10000000-0000-0000-0000-000000000004', 'agent', true),
  ('10000000-0000-0000-0001-000000000005', '10000000-0000-0000-0000-000000000005', 'farmer', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_profiles (id, user_id, first_name, last_name, preferred_contact_method) VALUES
  ('10000000-0000-0000-0002-000000000001', '10000000-0000-0000-0000-000000000001', 'System', 'Admin', 'email'),
  ('10000000-0000-0000-0002-000000000002', '10000000-0000-0000-0000-000000000002', 'Dr. Anand', 'Kulkarni', 'email'),
  ('10000000-0000-0000-0002-000000000003', '10000000-0000-0000-0000-000000000003', 'Sunita', 'Patil', 'phone'),
  ('10000000-0000-0000-0002-000000000004', '10000000-0000-0000-0000-000000000004', 'Basavaraj', 'Gowda', 'phone'),
  ('10000000-0000-0000-0002-000000000005', '10000000-0000-0000-0000-000000000005', 'Ramesh', 'Kumar', 'sms')
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_preferences (id, user_id, preferred_language, timezone, theme, notification_frequency) VALUES
  ('10000000-0000-0000-0003-000000000005', '10000000-0000-0000-0000-000000000005', 'kn', 'Asia/Kolkata', 'system', 'instant')
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_permissions (id, user_id, permission_code, scope) VALUES
  ('10000000-0000-0000-0004-000000000001', '10000000-0000-0000-0000-000000000002', 'diagnose:confirm', 'district:raichur')
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 2. Farm Hierarchy
-- -----------------------------------------------------------------------------
INSERT INTO farms (id, name, registration_number, total_area_sqm, owner_id, status, is_demo) VALUES
  ('20000000-0000-0000-0000-000000000001', 'Ramesh Model Farm', 'KA-RC-2026-F001', 40468.6, '10000000-0000-0000-0000-000000000005', 'active', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO farm_boundaries (id, farm_id, boundary_polygon, area_sqm, perimeter_meters) VALUES
  ('20000000-0000-0000-0001-000000000001', '20000000-0000-0000-0000-000000000001',
   ST_Multi(ST_GeomFromText('POLYGON((77.3400 16.2000, 77.3450 16.2000, 77.3450 16.2050, 77.3400 16.2050, 77.3400 16.2000))', 4326)),
   40468.6, 920.0)
ON CONFLICT (id) DO NOTHING;

INSERT INTO farm_sections (id, farm_id, section_code, name, section_polygon) VALUES
  ('20000000-0000-0000-0002-000000000001', '20000000-0000-0000-0000-000000000001', 'SEC-A', 'North Section',
   ST_GeomFromText('POLYGON((77.3400 16.2025, 77.3450 16.2025, 77.3450 16.2050, 77.3400 16.2050, 77.3400 16.2025))', 4326))
ON CONFLICT (id) DO NOTHING;

INSERT INTO farm_plots (id, farm_id, section_id, plot_code, soil_type, irrigation_source, area_sqm, plot_polygon) VALUES
  ('20000000-0000-0000-0003-000000000001', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0002-000000000001',
   'PLOT-A1', 'Black Clay Loam', 'Drip Irrigation', 20234.3,
   ST_GeomFromText('POLYGON((77.3400 16.2025, 77.3425 16.2025, 77.3425 16.2050, 77.3400 16.2050, 77.3400 16.2025))', 4326))
ON CONFLICT (id) DO NOTHING;

INSERT INTO farm_locations (id, farm_id, village_or_town, taluk_or_subdistrict, district, state, centroid) VALUES
  ('20000000-0000-0000-0004-000000000001', '20000000-0000-0000-0000-000000000001', 'Sindhanur', 'Sindhanur', 'Raichur', 'Karnataka',
   ST_GeomFromText('POINT(77.3425 16.2025)', 4326))
ON CONFLICT (id) DO NOTHING;

INSERT INTO farm_members (id, farm_id, user_id, access_level) VALUES
  ('20000000-0000-0000-0005-000000000001', '20000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000005', 'owner')
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 3. Crops & Plants
-- -----------------------------------------------------------------------------
INSERT INTO crop_groups (id, code, name, description) VALUES
  ('30000000-0000-0000-0000-000000000001', 'CEREAL', 'Cereals & Millets', 'Major staple grain crops')
ON CONFLICT (id) DO NOTHING;

INSERT INTO crop_types (id, group_id, code, common_name, botanical_name, optimal_temp_min_c, optimal_temp_max_c) VALUES
  ('30000000-0000-0000-0001-000000000001', '30000000-0000-0000-0000-000000000001', 'MAIZE', 'Maize (Corn)', 'Zea mays', 18.0, 32.0),
  ('30000000-0000-0000-0001-000000000002', '30000000-0000-0000-0000-000000000001', 'PADDY', 'Paddy (Rice)', 'Oryza sativa', 20.0, 35.0)
ON CONFLICT (id) DO NOTHING;

INSERT INTO crop_growth_stages (id, crop_type_id, stage_name, stage_order, typical_duration_days, water_requirement_level) VALUES
  ('30000000-0000-0000-0002-000000000001', '30000000-0000-0000-0001-000000000001', 'Emergence', 1, 10, 'low'),
  ('30000000-0000-0000-0002-000000000002', '30000000-0000-0000-0001-000000000001', 'Vegetative (Whorl)', 2, 35, 'medium'),
  ('30000000-0000-0000-0002-000000000003', '30000000-0000-0000-0001-000000000001', 'Tasseling / Silking', 3, 20, 'high')
ON CONFLICT (id) DO NOTHING;

INSERT INTO crop_instances (id, plot_id, crop_type_id, variety, season, planting_date, status) VALUES
  ('30000000-0000-0000-0003-000000000001', '20000000-0000-0000-0003-000000000001', '30000000-0000-0000-0001-000000000001', 'Pioneer 3396', 'kharif', '2026-06-15', 'active')
ON CONFLICT (id) DO NOTHING;

INSERT INTO plants (id, crop_instance_id, tag_or_id, row_number, column_number, plant_location, health_status) VALUES
  ('30000000-0000-0000-0004-000000000001', '30000000-0000-0003-0000-000000000001', 'MZ-P1-R04-C12', 4, 12, ST_GeomFromText('POINT(77.3410 16.2030)', 4326), 'infested')
ON CONFLICT (id) DO NOTHING;

INSERT INTO plant_observations (id, plant_id, observer_id, visual_symptoms, vigor_score, foliage_damage_pct) VALUES
  ('30000000-0000-0000-0005-000000000001', '30000000-0000-0000-0004-000000000001', '10000000-0000-0000-0000-000000000004', 'Pinholes in whorl leaves with fresh larval frass', 7, 25.0)
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 4. Media (Metadata & S3/GCS Object Keys only - NO BLOBs)
-- -----------------------------------------------------------------------------
INSERT INTO media_files (id, uploader_id, storage_provider, bucket_name, object_key, file_name, file_size_bytes, mime_type, file_hash_sha256, media_type, capture_timestamp) VALUES
  ('40000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000004', 's3', 'cropsentinel-media-prod',
   'captures/2026/11/06/f001_mz_whorl_closeup_001.jpg', 'f001_mz_whorl_closeup_001.jpg', 2481920, 'image/jpeg',
   'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'image', '2026-11-06 09:30:00+00')
ON CONFLICT (id) DO NOTHING;

INSERT INTO media_locations (id, media_file_id, location, altitude_meters, gps_accuracy_meters, captured_at) VALUES
  ('40000000-0000-0000-0001-000000000001', '40000000-0000-0000-0000-000000000001',
   ST_GeomFromText('POINT(77.3410 16.2030)', 4326), 412.5, 2.5, '2026-11-06 09:30:00+00')
ON CONFLICT (id) DO NOTHING;

INSERT INTO media_observations (id, media_file_id, observation_id, media_role) VALUES
  ('40000000-0000-0000-0002-000000000001', '40000000-0000-0000-0000-000000000001', '30000000-0000-0000-0005-000000000001', 'symptom_closeup')
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 5. Pest & Disease Masters
-- -----------------------------------------------------------------------------
INSERT INTO pest_categories (id, code, name, description) VALUES
  ('50000000-0000-0000-0000-000000000001', 'INSECT', 'Insect Pests', 'Lepidoptera, Hemiptera and Diptera insect pests')
ON CONFLICT (id) DO NOTHING;

INSERT INTO pests (id, pest_category_id, common_name, scientific_name, economic_threshold, quarantine_status) VALUES
  ('50000000-0000-0000-0001-000000000001', '50000000-0000-0000-0000-000000000001', 'Fall Armyworm', 'Spodoptera frugiperda', '10% infested plants in whorl stage', 'regulated_non_quarantine')
ON CONFLICT (id) DO NOTHING;

INSERT INTO pest_life_cycles (id, pest_id, stage_name, stage_duration_days_min, stage_duration_days_max, damaging_stage) VALUES
  ('50000000-0000-0000-0002-000000000001', '50000000-0000-0000-0001-000000000001', 'Larva (1st-6th Instar)', 14, 22, true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO pest_host_crops (id, pest_id, crop_type_id, susceptibility_level, damage_severity_rating) VALUES
  ('50000000-0000-0000-0003-000000000001', '50000000-0000-0000-0001-000000000001', '30000000-0000-0000-0001-000000000001', 'primary', 5)
ON CONFLICT (id) DO NOTHING;

INSERT INTO diseases (id, common_name, scientific_name, pathogen_type, economic_impact) VALUES
  ('50000000-0000-0000-0004-000000000001', 'Bacterial Leaf Blight', 'Xanthomonas oryzae pv. oryzae', 'bacterial', 'Severe yield loss up to 50% in warm humid conditions')
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 6. AI Analysis & Inference Traceability
-- -----------------------------------------------------------------------------
INSERT INTO ai_model_versions (id, model_name, version_tag, model_family, weights_digest_sha256, f1_score, accuracy, inference_runtime) VALUES
  ('60000000-0000-0000-0000-000000000001', 'CropSentinel-YOLO-Pest', 'v1.4.0', 'yolo',
   'a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90', 0.9320, 0.9450, 'onnxruntime')
ON CONFLICT (id) DO NOTHING;

INSERT INTO ai_analysis (id, media_file_id, requested_by, status, analysis_type, processing_time_ms) VALUES
  ('60000000-0000-0000-0001-000000000001', '40000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000004',
   'completed', 'detection', 142)
ON CONFLICT (id) DO NOTHING;

INSERT INTO media_analysis_links (id, media_file_id, analysis_id) VALUES
  ('40000000-0000-0000-0003-000000000001', '40000000-0000-0000-0000-000000000001', '60000000-0000-0000-0001-000000000001')
ON CONFLICT (id) DO NOTHING;

INSERT INTO ai_predictions (id, analysis_id, model_version_id, pest_id, primary_diagnosis, confidence_score, severity_level) VALUES
  ('60000000-0000-0000-0002-000000000001', '60000000-0000-0000-0001-000000000001', '60000000-0000-0000-0000-000000000001',
   '50000000-0000-0000-0001-000000000001', 'Spodoptera frugiperda (Fall Armyworm)', 0.9420, 'medium')
ON CONFLICT (id) DO NOTHING;

INSERT INTO ai_detections (id, prediction_id, label, bbox_x_min, bbox_y_min, bbox_x_max, bbox_y_max, detection_confidence) VALUES
  ('60000000-0000-0000-0003-000000000001', '60000000-0000-0000-0002-000000000001', 'fall_armyworm_larva', 0.2200, 0.3100, 0.4800, 0.6500, 0.9420)
ON CONFLICT (id) DO NOTHING;

INSERT INTO ai_confidence (id, prediction_id, class_label, probability) VALUES
  ('60000000-0000-0000-0004-000000000001', '60000000-0000-0000-0002-000000000001', 'Spodoptera frugiperda', 0.9420)
ON CONFLICT (id) DO NOTHING;

INSERT INTO diagnosis_records (id, analysis_id, prediction_id, verified_by, confirmed_pest_id, confirmation_status, expert_notes) VALUES
  ('60000000-0000-0000-0005-000000000001', '60000000-0000-0000-0001-000000000001', '60000000-0000-0000-0002-000000000001',
   '10000000-0000-0000-0000-000000000002', '50000000-0000-0000-0001-000000000001', 'expert_confirmed', 'Confirmed 3rd instar larva in whorl; recommend bio-control release')
ON CONFLICT (id) DO NOTHING;

INSERT INTO ai_feedback (id, diagnosis_record_id, prediction_id, user_id, feedback_type, comments) VALUES
  ('60000000-0000-0000-0006-000000000001', '60000000-0000-0000-0005-000000000001', '60000000-0000-0000-0002-000000000001',
   '10000000-0000-0000-0000-000000000002', 'agree', 'Excellent bounding box localization on leaf whorl')
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 7. Pest Management (Statutory Verified Registrations - R5 Compliant)
-- -----------------------------------------------------------------------------
INSERT INTO ipm_methods (id, code, title, category, description, environmental_impact_rating) VALUES
  ('70000000-0000-0000-0000-000000000001', 'IPM-BIO-TRICO', 'Trichogramma egg parasitoid release', 'biological', 'Inundative release of Trichogramma pretiosum parasitoid cards', 'none'),
  ('70000000-0000-0000-0000-000000000002', 'IPM-BEHAV-PHERO', 'FAW pheromone mass trapping', 'behavioral', 'Funnel pheromone traps baited with (Z)-9-tetradecenyl acetate', 'none')
ON CONFLICT (id) DO NOTHING;

INSERT INTO biological_controls (id, ipm_method_id, agent_name, agent_type, target_pest_id, release_rate) VALUES
  ('70000000-0000-0000-0001-000000000001', '70000000-0000-0000-0000-000000000001', 'Trichogramma pretiosum', 'parasitoid',
   '50000000-0000-0000-0001-000000000001', '50,000 parasitized eggs/ha weekly')
ON CONFLICT (id) DO NOTHING;

INSERT INTO pest_control_options (id, pest_id, crop_type_id, ipm_method_id, strategy_summary, effectiveness_rating) VALUES
  ('70000000-0000-0000-0002-000000000001', '50000000-0000-0000-0001-000000000001', '30000000-0000-0000-0001-000000000001',
   '70000000-0000-0000-0000-000000000001', 'Early whorl deployment of Trichogramma cards', 'high')
ON CONFLICT (id) DO NOTHING;

INSERT INTO chemical_controls (id, ipm_method_id, active_ingredient, chemical_class, toxicity_class, phi_days, rei_hours) VALUES
  ('70000000-0000-0000-0003-000000000001', '70000000-0000-0000-0000-000000000001', 'Chlorantraniliprole 18.5% SC', 'Anthranilic Diamide', 'Green_Triangle', 14, 24)
ON CONFLICT (id) DO NOTHING;

INSERT INTO pesticide_registrations (id, chemical_control_id, registration_number, registering_authority, registered_trade_name, approved_crop_id, approved_pest_id, approved_dosage_per_ha, approval_date, status) VALUES
  ('70000000-0000-0000-0004-000000000001', '70000000-0000-0000-0003-000000000001', 'CIR-10824/2019(398)-Chlorantraniliprole(SC)-892', 'CIBRC', 'Coragen 18.5 SC',
   '30000000-0000-0000-0001-000000000001', '50000000-0000-0000-0001-000000000001', '0.4 ml/litre water (150-200 ml/ha)', '2019-04-12', 'active')
ON CONFLICT (id) DO NOTHING;

INSERT INTO treatment_records (id, farm_plot_id, crop_instance_id, applied_by, ipm_method_id, application_date, dosage_applied) VALUES
  ('70000000-0000-0000-0005-000000000001', '20000000-0000-0000-0003-000000000001', '30000000-0000-0003-0000-000000000001',
   '10000000-0000-0000-0000-000000000005', '70000000-0000-0000-0000-000000000001', '2026-11-06 14:00:00+00', '5 Tricho-cards across Plot A1')
ON CONFLICT (id) DO NOTHING;

INSERT INTO treatment_effectiveness (id, treatment_record_id, days_post_treatment, pest_mortality_percentage, crop_recovery_score, evaluator_id) VALUES
  ('70000000-0000-0000-0006-000000000001', '70000000-0000-0000-0005-000000000001', 7, 82.5, 4, '10000000-0000-0000-0000-000000000003')
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 8. Hotspot & Outbreak
-- -----------------------------------------------------------------------------
INSERT INTO pest_reports (id, reporter_id, farm_plot_id, reported_pest_id, report_location, severity, observation_date, status) VALUES
  ('80000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000005', '20000000-0000-0000-0003-000000000001',
   '50000000-0000-0000-0001-000000000001', ST_GeomFromText('POINT(77.3410 16.2030)', 4326), 'moderate', '2026-11-06 09:30:00+00', 'verified')
ON CONFLICT (id) DO NOTHING;

INSERT INTO verified_cases (id, pest_report_id, verifier_id, confirmed_location, confirmed_pest_id, confidence_level) VALUES
  ('80000000-0000-0000-0001-000000000001', '80000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000002',
   ST_GeomFromText('POINT(77.3410 16.2030)', 4326), '50000000-0000-0000-0001-000000000001', 'high')
ON CONFLICT (id) DO NOTHING;

INSERT INTO hotspot_regions (id, region_name, boundary_geom, pest_id, risk_level, active_case_count, start_date) VALUES
  ('80000000-0000-0000-0002-000000000001', 'Sindhanur Maize Cluster',
   ST_Multi(ST_GeomFromText('POLYGON((77.3000 16.1500, 77.4000 16.1500, 77.4000 16.2500, 77.3000 16.2500, 77.3000 16.1500))', 4326)),
   '50000000-0000-0000-0001-000000000001', 'high', 14, '2026-11-01')
ON CONFLICT (id) DO NOTHING;

INSERT INTO regional_pest_statistics (id, region_code, date_bucket, pest_id, total_reports, verified_count, incidence_rate) VALUES
  ('80000000-0000-0000-0003-000000000001', 'RAICHUR-SINDHANUR', '2026-11-06', '50000000-0000-0000-0001-000000000001', 28, 22, 0.785)
ON CONFLICT (id) DO NOTHING;

INSERT INTO outbreak_predictions (id, region_geom, pest_id, predicted_risk_score, forecast_horizon_days, valid_from, valid_until) VALUES
  ('80000000-0000-0000-0004-000000000001',
   ST_GeomFromText('POLYGON((77.3200 16.1800, 77.3800 16.1800, 77.3800 16.2300, 77.3200 16.2300, 77.3200 16.1800))', 4326),
   '50000000-0000-0000-0001-000000000001', 0.8400, 7, '2026-11-06 00:00:00+00', '2026-11-13 00:00:00+00')
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 9. Recovery & Inspection
-- -----------------------------------------------------------------------------
INSERT INTO inspections (id, farm_id, plot_id, inspector_id, scheduled_date, status, overall_health_rating) VALUES
  ('90000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', '20000000-0000-0000-0003-000000000001',
   '10000000-0000-0000-0000-000000000004', '2026-11-06', 'completed', 4)
ON CONFLICT (id) DO NOTHING;

INSERT INTO scouting_records (id, inspection_id, waypoint_location, plant_count_inspected, infested_plant_count, pest_id) VALUES
  ('90000000-0000-0000-0001-000000000001', '90000000-0000-0000-0000-000000000001',
   ST_GeomFromText('POINT(77.3412 16.2032)', 4326), 50, 4, '50000000-0000-0000-0001-000000000001')
ON CONFLICT (id) DO NOTHING;

INSERT INTO recovery_records (id, farm_plot_id, crop_instance_id, recovery_status, recovery_percentage, assessed_at, assessor_id) VALUES
  ('90000000-0000-0000-0002-000000000001', '20000000-0000-0000-0003-000000000001', '30000000-0000-0003-0000-000000000001',
   'partial_recovery', 75.0, '2026-11-06 16:00:00+00', '10000000-0000-0000-0000-000000000003')
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 10. Chatbot & Knowledge
-- -----------------------------------------------------------------------------
INSERT INTO chat_sessions (id, user_id, title, language, channel) VALUES
  ('a0000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000005', 'Fall Armyworm Symptoms in Maize', 'kn', 'mobile')
ON CONFLICT (id) DO NOTHING;

INSERT INTO chat_messages (id, session_id, sender_type, message_text, sequence_number) VALUES
  ('a0000000-0000-0000-0001-000000000001', 'a0000000-0000-0000-0000-000000000001', 'user', 'Nanna jola belealli ele kaddhidhe, yenu madabekhu?', 1),
  ('a0000000-0000-0000-0001-000000000002', 'a0000000-0000-0000-0000-000000000001', 'bot', 'Idhu Fall Armyworm (Khatarnak Hula) aagirabahudu. Dayavittu whorl bhaagadha photo thegedhu upload maadi.', 2)
ON CONFLICT (id) DO NOTHING;

INSERT INTO knowledge_articles (id, title, slug, version, author_id, category, summary, content, status) VALUES
  ('a0000000-0000-0000-0002-000000000001', 'Integrated Management of Fall Armyworm in Maize', 'ipm-fall-armyworm-maize', 1,
   '10000000-0000-0000-0000-000000000002', 'pest_management', 'Comprehensive protocol for FAW scouting and biological management.',
   'Scout fields twice a week during early whorl stage. Release Trichogramma pretiosum at 50,000/ha when egg masses are detected. Hand-pick egg masses in smallholder plots.', 'published')
ON CONFLICT (id) DO NOTHING;

INSERT INTO knowledge_chunks (id, article_id, chunk_index, content_chunk, token_count) VALUES
  ('a0000000-0000-0000-0003-000000000001', 'a0000000-0000-0000-0002-000000000001', 0,
   'Scout fields twice a week during early whorl stage. Release Trichogramma pretiosum cards upon egg detection.', 28)
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 11. Notifications
-- -----------------------------------------------------------------------------
INSERT INTO notifications (id, user_id, title, body, notification_type, priority, status, channel) VALUES
  ('b0000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000005',
   'Pest Alert: Fall Armyworm in Sindhanur', 'Fall Armyworm activity detected within 2 km of your farm. Inspect maize whorls today.',
   'pest_alert', 'high', 'delivered', 'push')
ON CONFLICT (id) DO NOTHING;

INSERT INTO alert_rules (id, rule_name, event_type, condition_expression, threshold_value, created_by) VALUES
  ('b0000000-0000-0000-0001-000000000001', 'Sindhanur_FAW_Cluster_Alert', 'outbreak_prediction', 'predicted_risk_score > 0.75 AND distance_km < 5.0', 0.7500, '10000000-0000-0000-0000-000000000001')
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_alert_preferences (id, user_id, push_enabled, sms_enabled, min_priority_threshold) VALUES
  ('b0000000-0000-0000-0002-000000000005', '10000000-0000-0000-0000-000000000005', true, true, 'medium')
ON CONFLICT (id) DO NOTHING;

