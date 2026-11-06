"""
Unit tests for weather ingestion, boundary loader, historical occurrences, and forecast gating.
Authority: final/feature-specs/05-data-layer.md §4.5, final/feature-specs/06-forecast-and-risk-map.md §3, phase-plan.md §4.6.
"""

from __future__ import annotations

import datetime
import os
import re
import unittest

from database.ingestion.boundary_loader import BoundaryRecord
from database.ingestion.forecast_gate import evaluate_forecast_gate, ForecastGateResult
from database.ingestion.historical_ingest import HistoricalOccurrenceRecord
from database.ingestion.weather_ingest import (
    ALLOWED_SPATIAL_METHODS,
    CORE_WEATHER_VARIABLES,
    PHYSICAL_BOUNDS,
    WeatherIngestRecord,
)


class TestWeatherIngest(unittest.TestCase):
    """Tests for weather snapshot ingestion, normalization, freshness, and physical bounds."""

    def setUp(self):
        self.now = datetime.datetime.now(datetime.timezone.utc)
        self.valid_vars = {
            "temperature_min_c": 19.5,
            "temperature_max_c": 31.0,
            "temperature_mean_c": 25.2,
            "relative_humidity_min_pct": 58.0,
            "relative_humidity_max_pct": 92.0,
            "relative_humidity_mean_pct": 78.5,
            "rainfall_mm": 12.4,
            "wet_day_runs": 2,
            "wind_speed_ms": 3.8,
        }

    def test_valid_weather_ingest_with_derived_leaf_wetness(self):
        """Tests ingestion of complete weather data and auto-derivation of leaf-wetness proxy."""
        rec = WeatherIngestRecord(
            geo_code="KA-MY-HDS-01",
            boundary_version="DEMO-BV-2026-V1",
            source="IMD_AWS_GRID",
            source_timestamp=self.now - datetime.timedelta(hours=2),
            variables=self.valid_vars,
            grid_id="GRID-01284",
            station_id="STN-MYS-04",
            station_distance_km=6.8,
            spatial_matching_method="centroid_nearest_station",
            fetched_at=self.now,
        )

        self.assertEqual(rec.geo_code, "KA-MY-HDS-01")
        self.assertEqual(rec.boundary_version, "DEMO-BV-2026-V1")
        self.assertEqual(rec.spatial_matching_method, "centroid_nearest_station")
        self.assertAlmostEqual(rec.freshness_seconds, 7200, delta=5)
        self.assertFalse(rec.is_stale)
        self.assertEqual(rec.completeness, 1.0)
        # Leaf wetness proxy derived
        self.assertIn("leaf_wetness_proxy_hours", rec.variables)
        self.assertGreaterEqual(rec.variables["leaf_wetness_proxy_hours"], 0.0)

    def test_variable_alias_resolution(self):
        """Tests that aliases like temp_mean, rh_mean, consecutive_wet_days are normalized."""
        alias_vars = {
            "temp_mean": 24.0,
            "rh_mean": 80.0,
            "consecutive_wet_days": 3,
            "precip_mm": 15.0,
            "wind_speed_ms": 2.5,
        }
        rec = WeatherIngestRecord(
            geo_code="KA-MY-HDS-01",
            boundary_version="DEMO-BV-2026-V1",
            source="IMD_GRID",
            source_timestamp=self.now,
            variables=alias_vars,
        )
        self.assertIn("temperature_mean_c", rec.variables)
        self.assertIn("relative_humidity_mean_pct", rec.variables)
        self.assertIn("wet_day_runs", rec.variables)
        self.assertIn("rainfall_mm", rec.variables)

    def test_physical_bounds_violation_rejected(self):
        """Tests that physical limits (e.g. impossible temperature or humidity) raise ValueError."""
        # Unphysical temperature 85°C
        with self.assertRaises(ValueError):
            WeatherIngestRecord(
                geo_code="KA-MY-HDS-01",
                boundary_version="DEMO-BV-2026-V1",
                source="TEST",
                source_timestamp=self.now,
                variables={"temperature_mean_c": 85.0},
            )

        # Unphysical negative humidity
        with self.assertRaises(ValueError):
            WeatherIngestRecord(
                geo_code="KA-MY-HDS-01",
                boundary_version="DEMO-BV-2026-V1",
                source="TEST",
                source_timestamp=self.now,
                variables={"relative_humidity_mean_pct": -5.0},
            )

    def test_invalid_spatial_matching_method_rejected(self):
        """Tests that unknown spatial matching methods are rejected."""
        with self.assertRaises(ValueError):
            WeatherIngestRecord(
                geo_code="KA-MY-HDS-01",
                boundary_version="DEMO-BV-2026-V1",
                source="TEST",
                source_timestamp=self.now,
                variables=self.valid_vars,
                spatial_matching_method="magic_guess",
            )

    def test_stale_data_flagging(self):
        """Tests that weather older than 24 hours is flagged as stale."""
        stale_time = self.now - datetime.timedelta(hours=36)
        rec = WeatherIngestRecord(
            geo_code="KA-MY-HDS-01",
            boundary_version="DEMO-BV-2026-V1",
            source="IMD_GRID",
            source_timestamp=stale_time,
            variables=self.valid_vars,
            fetched_at=self.now,
        )
        self.assertTrue(rec.is_stale)
        self.assertGreater(rec.freshness_seconds, 24 * 3600)

        # Evaluation produces insufficient_data
        eval_res = rec.evaluate_sufficiency(target_boundary_version="DEMO-BV-2026-V1", as_of_time=self.now)
        self.assertFalse(eval_res["is_sufficient"])
        self.assertEqual(eval_res["reason_code"], "weather_stale")


class TestBoundaryLoader(unittest.TestCase):
    """Tests for versioned administrative boundary ingestion and topology validation."""

    def test_valid_boundary_with_wkt_conversion(self):
        geojson_poly = {
            "type": "Polygon",
            "coordinates": [
                [[76.5, 12.2], [76.7, 12.2], [76.7, 12.4], [76.5, 12.4], [76.5, 12.2]]
            ]
        }
        rec = BoundaryRecord(
            code="KA-MY-HDS-01",
            level="mandal",
            name="Hunsur",
            boundary_version="DEMO-BV-2026-V1",
            parent_code="KA-MYS",
            geojson_geometry=geojson_poly,
        )
        self.assertEqual(rec.code, "KA-MY-HDS-01")
        self.assertEqual(rec.boundary_version, "DEMO-BV-2026-V1")
        wkt = rec.to_wkt()
        self.assertIsNotNone(wkt)
        self.assertTrue(wkt.startswith("MULTIPOLYGON"))
        self.assertIn("76.5 12.2", wkt)

    def test_invalid_level_rejected(self):
        with self.assertRaises(ValueError):
            BoundaryRecord(
                code="X-01",
                level="neighborhood",  # Not in allowed levels
                name="Invalid",
                boundary_version="V1",
            )

    def test_out_of_range_coordinates_rejected(self):
        bad_geojson = {
            "type": "Polygon",
            "coordinates": [[[250.0, 95.0], [251.0, 95.0], [251.0, 96.0], [250.0, 95.0]]]
        }
        with self.assertRaises(ValueError):
            BoundaryRecord(
                code="KA-MYS",
                level="district",
                name="Mysuru",
                boundary_version="V1",
                geojson_geometry=bad_geojson,
            )


class TestHistoricalOccurrences(unittest.TestCase):
    """Tests for historical occurrence ingestion, temporal invariants, and deduplication."""

    def setUp(self):
        self.valid_args = {
            "crop_code": "paddy",
            "target_code": "blast",
            "geo_code": "KA-MY-HDS-01",
            "boundary_version": "DEMO-BV-2026-V1",
            "verification_tier": "confirmed",
            "event_date": "2025-10-14",
            "report_date": "2025-10-18",
            "source_link": "https://agri-archive.karnataka.gov.in/clinic/2025/rep-4821",
            "source_dataset": "karnataka_plant_clinic_archives",
            "external_accession_id": "PC-2025-4821",
            "severity": "high",
        }

    def test_valid_historical_occurrence_with_dedupe_key(self):
        rec = HistoricalOccurrenceRecord(**self.valid_args)
        self.assertEqual(rec.crop_code, "paddy")
        self.assertEqual(rec.target_code, "blast")
        self.assertTrue(rec.dedupe_key.startswith("sha256:"))

        # Verify deterministic key
        rec2 = HistoricalOccurrenceRecord(**self.valid_args)
        self.assertEqual(rec.dedupe_key, rec2.dedupe_key)

    def test_temporal_invariant_report_date_earlier_than_event_date_rejected(self):
        """Enforces invariant: report_date cannot precede event_date."""
        args = dict(self.valid_args)
        args["event_date"] = "2025-10-20"
        args["report_date"] = "2025-10-10"  # 10 days before event!
        with self.assertRaises(ValueError) as ctx:
            HistoricalOccurrenceRecord(**args)
        self.assertIn("Temporal violation", str(ctx.exception))

    def test_missing_source_link_rejected(self):
        """Enforces provenance invariant: source_link cannot be empty."""
        args = dict(self.valid_args)
        args["source_link"] = ""
        with self.assertRaises(ValueError):
            HistoricalOccurrenceRecord(**args)

    def test_invalid_verification_tier_rejected(self):
        args = dict(self.valid_args)
        args["verification_tier"] = "hearsay"
        with self.assertRaises(ValueError):
            HistoricalOccurrenceRecord(**args)

    def test_dedupe_history_registration(self):
        rec = HistoricalOccurrenceRecord(**self.valid_args)
        self.assertEqual(len(rec.dedupe_history), 0)
        rec.register_duplicate(
            duplicate_accession="SURV-2025-9912",
            duplicate_source="field_extension_survey_2025",
            match_reason="Exact crop, target, admin unit, and window match (+-2 days)",
        )
        self.assertEqual(len(rec.dedupe_history), 1)
        self.assertEqual(rec.dedupe_history[0]["matched_accession"], "SURV-2025-9912")
        self.assertEqual(rec.dedupe_history[0]["resolution"], "merged_into_canonical_record")


class TestForecastGateAndZeroSilentImputation(unittest.TestCase):
    """
    Tests forecast gate enforcement:
    Missing/stale data produces explicit `insufficient_data` with probability=None.
    Never silent imputation.
    """

    def setUp(self):
        self.now = datetime.datetime.now(datetime.timezone.utc)
        self.valid_rec = WeatherIngestRecord(
            geo_code="KA-MY-HDS-01",
            boundary_version="DEMO-BV-2026-V1",
            source="IMD_AWS_GRID",
            source_timestamp=self.now - datetime.timedelta(hours=2),
            variables={
                "temperature_mean_c": 25.0,
                "relative_humidity_mean_pct": 82.0,
                "rainfall_mm": 10.0,
                "wet_day_runs": 2,
                "wind_speed_ms": 3.0,
            },
            spatial_matching_method="centroid_nearest_station",
            fetched_at=self.now,
        )

    def test_missing_weather_produces_insufficient_data(self):
        gate = evaluate_forecast_gate(
            weather_snapshot=None,
            target_boundary_version="DEMO-BV-2026-V1",
            as_of_time=self.now,
        )
        self.assertFalse(gate.can_forecast)
        self.assertEqual(gate.risk_band, "insufficient_data")
        self.assertIsNone(gate.probability)
        self.assertEqual(gate.reason_code, "weather_missing")

    def test_stale_weather_produces_insufficient_data(self):
        stale_rec = WeatherIngestRecord(
            geo_code="KA-MY-HDS-01",
            boundary_version="DEMO-BV-2026-V1",
            source="IMD_AWS_GRID",
            source_timestamp=self.now - datetime.timedelta(hours=30),  # 30h > 24h SLA
            variables=self.valid_rec.variables,
            fetched_at=self.now,
        )
        gate = evaluate_forecast_gate(
            weather_snapshot=stale_rec,
            target_boundary_version="DEMO-BV-2026-V1",
            as_of_time=self.now,
        )
        self.assertFalse(gate.can_forecast)
        self.assertEqual(gate.risk_band, "insufficient_data")
        self.assertIsNone(gate.probability)
        self.assertEqual(gate.reason_code, "weather_stale")

    def test_boundary_mismatch_produces_insufficient_data(self):
        gate = evaluate_forecast_gate(
            weather_snapshot=self.valid_rec,
            target_boundary_version="DEMO-BV-2027-V2",  # Mismatch!
            as_of_time=self.now,
        )
        self.assertFalse(gate.can_forecast)
        self.assertEqual(gate.risk_band, "insufficient_data")
        self.assertIsNone(gate.probability)
        self.assertEqual(gate.reason_code, "boundary_mismatch")

    def test_incomplete_weather_produces_insufficient_data_never_silent_imputation(self):
        # Missing rainfall and wind
        incomplete_rec = WeatherIngestRecord(
            geo_code="KA-MY-HDS-01",
            boundary_version="DEMO-BV-2026-V1",
            source="IMD_AWS_GRID",
            source_timestamp=self.now - datetime.timedelta(hours=1),
            variables={
                "temperature_mean_c": 25.0,
                "relative_humidity_mean_pct": 82.0,
                # rainfall_mm missing!
                # wet_day_runs missing!
                "wind_speed_ms": 3.0,
            },
            fetched_at=self.now,
        )
        gate = evaluate_forecast_gate(
            weather_snapshot=incomplete_rec,
            target_boundary_version="DEMO-BV-2026-V1",
            as_of_time=self.now,
        )
        self.assertFalse(gate.can_forecast)
        self.assertEqual(gate.risk_band, "insufficient_data")
        self.assertIsNone(gate.probability)
        self.assertEqual(gate.reason_code, "weather_incomplete")
        self.assertIn("rainfall_mm", gate.detail)

    def test_insufficient_data_with_probability_raises_contract_violation(self):
        """Invariant: risk_band='insufficient_data' MUST NOT carry a numeric probability."""
        with self.assertRaises(ValueError):
            ForecastGateResult(
                can_forecast=False,
                risk_band="insufficient_data",
                probability=0.45,  # Illegal! Must be None
                reason_code="weather_stale",
                detail="Test",
                boundary_version="DEMO-BV-2026-V1",
            )

    def test_sufficient_weather_allows_scoring(self):
        gate = evaluate_forecast_gate(
            weather_snapshot=self.valid_rec,
            target_boundary_version="DEMO-BV-2026-V1",
            as_of_time=self.now,
        )
        self.assertTrue(gate.can_forecast)
        self.assertEqual(gate.risk_band, "ready_for_scoring")
        self.assertEqual(gate.reason_code, "sufficient")


class TestSchemaAndSeedConstraints(unittest.TestCase):
    """Verifies DDL schema and demo seed for weather, historical occurrences, and refusal constraints."""

    @classmethod
    def setUpClass(cls):
        schema_path = os.path.join(os.path.dirname(__file__), "..", "schema", "01-schema.sql")
        seed_path = os.path.join(os.path.dirname(__file__), "..", "schema", "02-demo-seed.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            cls.schema_sql = f.read()
        with open(seed_path, "r", encoding="utf-8") as f:
            cls.seed_sql = f.read()

    def test_historical_occurrences_table_and_constraints(self):
        # Table exists
        self.assertTrue(bool(re.search(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?historical_occurrences", self.schema_sql, re.I)))
        # Check constraints
        self.assertIn("CONSTRAINT ck_hist_tier CHECK", self.schema_sql)
        self.assertIn("CONSTRAINT ck_hist_dates CHECK (report_date >= event_date)", self.schema_sql)
        self.assertIn("CONSTRAINT uq_hist_dedupe_key UNIQUE (dedupe_key)", self.schema_sql)
        # Trigger
        self.assertIn("CREATE TRIGGER trg_historical_occurrences_immutable", self.schema_sql)

    def test_weather_spatial_method_constraint(self):
        self.assertIn("CONSTRAINT ck_weather_spatial_method CHECK (spatial_matching_method IN (", self.schema_sql)
        for method in ALLOWED_SPATIAL_METHODS:
            self.assertIn(f"'{method}'", self.schema_sql)

    def test_forecast_no_imputation_constraint(self):
        self.assertIn("CONSTRAINT ck_forecasts_no_imputation CHECK", self.schema_sql)
        self.assertIn("risk_band <> 'insufficient_data' OR probability IS NULL", self.schema_sql)

    def test_check_weather_sufficiency_function_in_ddl(self):
        self.assertIn("CREATE OR REPLACE FUNCTION check_weather_sufficiency", self.schema_sql)
        self.assertIn("boundary_mismatch", self.schema_sql)
        self.assertIn("weather_stale", self.schema_sql)
        self.assertIn("weather_incomplete", self.schema_sql)

    def test_demo_seed_contains_historical_and_weather_refusal_rows(self):
        self.assertIn("INSERT INTO historical_occurrences", self.seed_sql)
        self.assertIn("sha256:", self.seed_sql)
        self.assertIn("karnataka_plant_clinic_archive", self.seed_sql)
        self.assertIn("centroid_nearest_station", self.seed_sql)
        # Test insufficient_data seed entry
        self.assertIn("insufficient_data", self.seed_sql)
        self.assertIn("weather_stale", self.seed_sql)


if __name__ == "__main__":
    unittest.main()
