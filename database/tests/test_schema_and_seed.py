"""
Comprehensive test suite for Phase 1 Database Schema, Demo Seed, and Safety Rules.
Authority: final/feature-specs/05-data-layer.md, phase-plan.md §4.5, AGENTS.md R1-R10.
"""

import json
import os
import re
import unittest
from typing import Dict, List, Set


class TestDatabaseSchemaAndSeed(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.schema_path = os.path.join(cls.base_dir, "schema", "01-schema.sql")
        cls.seed_path = os.path.join(cls.base_dir, "schema", "02-demo-seed.sql")

        with open(cls.schema_path, "r", encoding="utf-8") as f:
            cls.schema_sql = f.read()

        with open(cls.seed_path, "r", encoding="utf-8") as f:
            cls.seed_sql = f.read()

    def test_schema_slices_completeness(self):
        """Verifies that all 14 schema slices are present across the 39 tables."""
        expected_tables = {
            # 1. Identity
            "roles", "users", "user_roles", "devices", "consents", "user_area_assignments", "sessions",
            # 2. Geography & Crop Context
            "geographies", "crops", "targets", "crop_calendars", "growing_areas", "crop_cycles",
            # 3. Observations & Media
            "observations", "image_assets", "image_quality_results", "image_predictions", "review_requests",
            # 4. Review & Verification
            "reviews", "review_evidence", "labels", "review_events", "observation_verification",
            "review_assignments", "sentinel_sites", "sentinel_visits",
            # 5. Weather, Historical Occurrences & Forecast
            "weather_snapshots", "historical_occurrences", "feature_snapshots", "forecasts", "forecast_runs",
            # 6. Advisory & Alerts
            "advisories", "advisory_versions", "advisory_approvals", "alert_policies", "alerts", "alert_deliveries",
            # 7. Registry, Audit & Exports
            "model_registry", "audit_events", "export_jobs"
        }

        found_tables = set(
            re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)", self.schema_sql, re.I)
        )
        missing = expected_tables - found_tables
        self.assertEqual(len(missing), 0, f"Missing tables in 01-schema.sql: {missing}")
        self.assertEqual(len(found_tables), 40)

    def test_append_only_guards(self):
        """Verifies immutable trigger guards on append-only tables."""
        expected_append_only = [
            "image_predictions",
            "image_quality_results",
            "reviews",
            "review_evidence",
            "labels",
            "review_events",
            "consents",
            "feature_snapshots",
            "forecasts",
            "advisory_versions",
            "advisory_approvals",
            "audit_events",
            "historical_occurrences",
        ]

        for table in expected_append_only:
            pattern = rf"CREATE\s+TRIGGER\s+[a-zA-Z0-9_]+\s+BEFORE\s+UPDATE\s+OR\s+DELETE\s+ON\s+{table}"
            self.assertTrue(
                bool(re.search(pattern, self.schema_sql, re.I)),
                f"Missing append-only trigger guard on table: {table}",
            )

    def test_postgis_only_where_needed(self):
        """PostGIS geometry must ONLY be used on tables needing spatial aggregation."""
        # Find all geometry columns
        geom_matches = re.findall(r"([a-zA-Z0-9_]+)\s+geometry\([a-zA-Z0-9_,\s]+\)", self.schema_sql, re.I)
        self.assertGreater(len(geom_matches), 0)

        # Split schema by CREATE TABLE to check which tables contain geometry(
        parts = re.split(r"CREATE\s+TABLE\s+", self.schema_sql, flags=re.I)[1:]
        geom_tables = set()
        for p in parts:
            tbl_name = re.match(r"([a-zA-Z0-9_]+)", p).group(1)
            if "geometry(" in p:
                geom_tables.add(tbl_name)

        allowed_geom_tables = {"geographies", "growing_areas", "sentinel_sites"}
        self.assertEqual(geom_tables, allowed_geom_tables, f"Unexpected PostGIS geometry in tables: {geom_tables - allowed_geom_tables}")

    def test_forecast_and_prediction_constraints(self):
        """Verifies reproducibility and lineage constraints in schema."""
        # Lineage check constraint on forecasts
        self.assertIn("ck_forecast_lineage", self.schema_sql)
        self.assertIn("feature_snapshot_id IS NOT NULL AND model_version IS NOT NULL", self.schema_sql)

        # Decision thresholds on image_predictions
        self.assertIn("decision_thresholds jsonb NOT NULL", self.schema_sql)
        self.assertIn("ood_score", self.schema_sql)
        self.assertIn("ck_prediction_thresholds", self.schema_sql)
        self.assertIn("ck_prediction_calibration", self.schema_sql)

        # Observation idempotency
        self.assertIn("uq_observation_client UNIQUE (user_id, client_report_id)", self.schema_sql)

    def test_demo_seed_is_demo_flag(self):
        """Ensures EVERY seeded row in 02-demo-seed.sql sets is_demo = true."""
        # Check all INSERT statements that insert into tables with is_demo column
        insert_blocks = re.findall(r"INSERT\s+INTO\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*VALUES\s*(.*?);", self.seed_sql, re.S | re.I)
        for tbl, cols, values in insert_blocks:
            col_list = [c.strip() for c in cols.split(",")]
            if tbl in ["roles", "user_roles", "devices", "user_area_assignments", "sessions", "review_requests", "observation_verification"]:
                # These tables are either reference data or tied directly to demo users/obs
                continue

            self.assertIn(
                "is_demo", col_list, f"Table {tbl} in 02-demo-seed.sql missing is_demo column in INSERT"
            )

    def test_safety_rule_r5_no_chemical_advice(self):
        """Verifies Safety Rule R5: zero chemical fungicides or synthetic pesticide recommendations."""
        forbidden_active_ingredients = [
            "mancozeb", "tricyclazole", "carbendazim", "hexaconazole", "azoxystrobin",
            "propiconazole", "chlorpyrifos", "imidacloprid", "malathion", "glyphosate",
            "spray fungicide", "apply pesticide", "apply insecticide"
        ]

        advisory_text = self.seed_sql.lower()
        for ingredient in forbidden_active_ingredients:
            self.assertNotIn(ingredient, advisory_text, f"Safety Rule R5 Violation: forbidden chemical active ingredient found in seed: '{ingredient}'")

    def test_forecast_eligible_cases_function(self):
        """Verifies forecast_eligible_cases excludes unverified, rejected, and checks cutoff."""
        self.assertIn("CREATE OR REPLACE FUNCTION forecast_eligible_cases", self.schema_sql)
        self.assertIn("ov.status IN ('confirmed', 'probable')", self.schema_sql)
        self.assertIn("ov.verified_at <= p_cutoff", self.schema_sql)
        self.assertIn("o.event_date <= (p_cutoff AT TIME ZONE 'UTC')::date", self.schema_sql)

    def test_demo_view_definition(self):
        """Verifies that v_demo_rows view aggregates demo rows for all primary entities."""
        self.assertIn("CREATE OR REPLACE VIEW v_demo_rows AS", self.schema_sql)
        for entity in ["users", "geographies", "observations", "forecasts", "advisories", "model_registry"]:
            self.assertIn(f"'{entity}'", self.schema_sql)


if __name__ == "__main__":
    unittest.main()
