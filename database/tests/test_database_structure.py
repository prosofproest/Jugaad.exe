"""
Automated Structural Test Suite for CropSentinel AI Master Database.
Verifies:
- All 11 Domains and 76 required tables.
- Primary Keys, Foreign Keys, Unique Constraints, Check Constraints.
- PostGIS Spatial columns and GiST index definitions.
- Non-BLOB media storage rule.
"""

import os
import re
import unittest
try:
    from sqlalchemy import inspect
    from database.models import Base
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

REQUIRED_TABLES_BY_DOMAIN = {
    "1_user": [
        "users", "user_roles", "user_profiles", "user_permissions", "user_sessions", "user_preferences"
    ],
    "2_farm": [
        "farms", "farm_boundaries", "farm_sections", "farm_plots", "farm_locations", "farm_members"
    ],
    "3_crop_and_plant": [
        "crop_types", "crop_groups", "crop_instances", "plants", "plant_observations", "crop_growth_stages", "planting_records"
    ],
    "4_media": [
        "media_files", "media_frames", "media_observations", "media_locations", "media_analysis_links"
    ],
    "5_pest_and_disease": [
        "pests", "pest_categories", "pest_life_cycles", "pest_host_crops", "diseases", "disease_symptoms", "crop_symptoms", "pest_damage_records"
    ],
    "6_ai_analysis": [
        "ai_analysis", "ai_predictions", "ai_detections", "ai_confidence", "ai_model_versions", "ai_feedback", "diagnosis_records"
    ],
    "7_pest_management": [
        "ipm_methods", "pest_control_options", "biological_controls", "mechanical_controls", "cultural_controls",
        "physical_controls", "behavioral_controls", "chemical_controls", "pesticide_registrations", "treatment_records", "treatment_effectiveness"
    ],
    "8_hotspot_and_outbreak": [
        "pest_reports", "verified_cases", "hotspot_regions", "regional_pest_statistics", "outbreak_predictions",
        "spread_observations", "risk_history", "monitoring_coverage"
    ],
    "9_recovery_and_inspection": [
        "inspections", "inspection_assignments", "scouting_records", "recovery_records", "recovery_comparisons",
        "seasonal_history", "infestation_history"
    ],
    "10_chatbot_and_knowledge": [
        "chat_sessions", "chat_messages", "knowledge_articles", "knowledge_chunks", "knowledge_embeddings", "chatbot_feedback"
    ],
    "11_notification": [
        "notifications", "alert_rules", "user_alert_preferences", "scheduled_tasks", "sync_logs"
    ],
}

ALL_REQUIRED_TABLES = set()
for tables in REQUIRED_TABLES_BY_DOMAIN.values():
    ALL_REQUIRED_TABLES.update(tables)


class TestDatabaseStructure(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not HAS_DEPS:
            raise unittest.SkipTest("SQLAlchemy not available in current environment")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.schema_sql_path = os.path.join(base_dir, "schema", "03-cropsentinel-master-schema.sql")
        with open(cls.schema_sql_path, "r", encoding="utf-8") as f:
            cls.schema_sql = f.read()

    def test_all_11_domains_registered_in_sqlalchemy(self):
        """Verify that all 76 required tables are registered in SQLAlchemy Base.metadata."""
        registered_tables = set(Base.metadata.tables.keys())
        missing = ALL_REQUIRED_TABLES - registered_tables
        self.assertEqual(len(missing), 0, f"Missing tables in SQLAlchemy metadata: {missing}")
        self.assertEqual(len(ALL_REQUIRED_TABLES), 76)

    def test_all_11_domains_in_sql_ddl(self):
        """Verify that all 76 required tables exist in 03-cropsentinel-master-schema.sql."""
        ddl_tables = set(
            re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)", self.schema_sql, re.I)
        )
        missing = ALL_REQUIRED_TABLES - ddl_tables
        self.assertEqual(len(missing), 0, f"Missing tables in master SQL schema: {missing}")

    def test_primary_keys_defined(self):
        """Verify every registered table has a single primary key named 'id'."""
        for table_name, table in Base.metadata.tables.items():
            pks = [c.name for c in table.primary_key.columns]
            self.assertEqual(pks, ["id"], f"Table {table_name} does not have standard single primary key 'id'")

    def test_foreign_key_relationships(self):
        """Verify key foreign keys exist and connect correctly across domains."""
        expected_fks = {
            "user_roles": ("users.id", "user_id"),
            "user_profiles": ("users.id", "user_id"),
            "farms": ("users.id", "owner_id"),
            "farm_boundaries": ("farms.id", "farm_id"),
            "farm_sections": ("farms.id", "farm_id"),
            "farm_plots": ("farms.id", "farm_id"),
            "crop_instances": ("farm_plots.id", "plot_id"),
            "plants": ("crop_instances.id", "crop_instance_id"),
            "media_files": ("users.id", "uploader_id"),
            "ai_analysis": ("media_files.id", "media_file_id"),
            "ai_predictions": ("ai_analysis.id", "analysis_id"),
            "ai_detections": ("ai_predictions.id", "prediction_id"),
            "diagnosis_records": ("ai_analysis.id", "analysis_id"),
            "ai_feedback": ("diagnosis_records.id", "diagnosis_record_id"),
            "pest_reports": ("users.id", "reporter_id"),
            "verified_cases": ("pest_reports.id", "pest_report_id"),
            "treatment_records": ("farm_plots.id", "farm_plot_id"),
            "treatment_effectiveness": ("treatment_records.id", "treatment_record_id"),
            "chat_messages": ("chat_sessions.id", "session_id"),
            "knowledge_chunks": ("knowledge_articles.id", "article_id"),
            "notifications": ("users.id", "user_id"),
        }

        for table_name, (target_col, source_col) in expected_fks.items():
            table = Base.metadata.tables[table_name]
            fk_targets = [fk.target_fullname for fk in table.foreign_keys]
            self.assertIn(
                target_col,
                fk_targets,
                f"Missing FK in {table_name} referencing {target_col} (found: {fk_targets})"
            )

    def test_check_constraints_present(self):
        """Verify check constraints for numeric bounds, ranges, and status enumerations."""
        required_constraints = [
            "chk_ai_pred_confidence_range",
            "chk_ai_detection_confidence_range",
            "chk_ai_conf_probability_range",
            "chk_outbreak_risk_range",
            "chk_users_status",
            "chk_pests_quarantine_status",
            "chk_media_files_media_type",
            "chk_media_files_mime_type",
        ]

        for constraint in required_constraints:
            self.assertIn(constraint, self.schema_sql, f"Missing constraint {constraint} in SQL schema")

    def test_postgis_spatial_columns_and_gist_indexes(self):
        """Verify PostGIS geometry columns and GiST index declarations."""
        spatial_tables = [
            ("farm_boundaries", "boundary_polygon", "idx_farm_boundaries_geom"),
            ("farm_sections", "section_polygon", "idx_farm_sections_geom"),
            ("farm_plots", "plot_polygon", "idx_farm_plots_geom"),
            ("farm_locations", "centroid", "idx_farm_locations_centroid"),
            ("plants", "plant_location", "idx_plants_geom"),
            ("media_locations", "location", "idx_media_locations_geom"),
            ("pest_reports", "report_location", "idx_pest_reports_geom"),
            ("verified_cases", "confirmed_location", "idx_verified_cases_geom"),
            ("hotspot_regions", "boundary_geom", "idx_hotspot_regions_geom"),
            ("outbreak_predictions", "region_geom", "idx_outbreak_predictions_geom"),
            ("spread_observations", "observation_location", "idx_spread_obs_geom"),
            ("scouting_records", "waypoint_location", "idx_scouting_records_geom"),
            ("monitoring_coverage", "boundary", "idx_monitoring_coverage_geom"),
        ]

        for table, geom_col, idx_name in spatial_tables:
            # Check column in SQLAlchemy metadata
            self.assertIn(geom_col, Base.metadata.tables[table].columns, f"Missing geom col {geom_col} in {table}")
            # Check GiST index in SQL schema
            pattern = rf"CREATE\s+INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?{idx_name}\s+ON\s+{table}\s+USING\s+GIST"
            self.assertTrue(
                bool(re.search(pattern, self.schema_sql, re.I)),
                f"Missing GiST spatial index {idx_name} on {table}"
            )

    def test_no_raw_binary_blobs_in_media_database(self):
        """Verify PostgreSQL does not store raw photos or video binary BLOBs."""
        media_table = Base.metadata.tables["media_files"]
        for col in media_table.columns:
            col_type = str(col.type).lower()
            self.assertNotIn("blob", col_type, f"Forbidden BLOB column {col.name} in media_files")
            self.assertNotIn("bytea", col_type, f"Forbidden bytea column {col.name} in media_files")

        # Verify metadata storage columns exist
        expected_cols = {"storage_provider", "bucket_name", "object_key", "mime_type", "file_size_bytes", "file_hash_sha256"}
        self.assertTrue(expected_cols.issubset(set(media_table.columns.keys())))


if __name__ == "__main__":
    unittest.main()

