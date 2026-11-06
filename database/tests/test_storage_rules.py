"""
Unit tests for storage layout and presigned URL rules.
"""

import unittest
from datetime import datetime, timezone
import uuid

from database.storage.storage_rules import (
    generate_observation_storage_key,
    validate_storage_key,
    validate_payload_limits,
    validate_presigned_request,
    MAX_PRESIGNED_TTL_SECONDS,
)


class TestStorageRules(unittest.TestCase):

    def setUp(self):
        self.obs_id = str(uuid.uuid4())
        self.img_id = str(uuid.uuid4())
        self.farmer_id = str(uuid.uuid4())
        self.other_farmer_id = str(uuid.uuid4())
        self.ext_id = str(uuid.uuid4())
        self.pathologist_id = str(uuid.uuid4())

    def test_key_generation_and_validation(self):
        fixed_dt = datetime(2026, 9, 14, 10, 0, 0, tzinfo=timezone.utc)
        key = generate_observation_storage_key(
            self.obs_id, self.img_id, "image/jpeg", timestamp=fixed_dt
        )
        self.assertEqual(
            key,
            f"observations/2026/09/{self.obs_id}/{self.img_id}/original.jpg",
        )

        meta = validate_storage_key(key)
        self.assertEqual(meta["kind"], "original")
        self.assertEqual(meta["year"], "2026")
        self.assertEqual(meta["month"], "09")
        self.assertEqual(meta["obs_id"], self.obs_id)
        self.assertEqual(meta["img_id"], self.img_id)

    def test_derivative_key_generation(self):
        fixed_dt = datetime(2026, 9, 14, 10, 0, 0, tzinfo=timezone.utc)
        key = generate_observation_storage_key(
            self.obs_id,
            self.img_id,
            "image/jpeg",
            timestamp=fixed_dt,
            is_original=False,
            derived_name="preview",
            pipeline_version="v1.0",
        )
        self.assertEqual(
            key,
            f"observations/2026/09/{self.obs_id}/{self.img_id}/derived/v1.0/preview.jpg",
        )
        meta = validate_storage_key(key)
        self.assertEqual(meta["kind"], "derivative")

    def test_payload_limits(self):
        # Valid
        validate_payload_limits("image/jpeg", 500 * 1024)

        # Unsupported MIME
        with self.assertRaises(ValueError):
            validate_payload_limits("application/pdf", 500 * 1024)

        # Under size
        with self.assertRaises(ValueError):
            validate_payload_limits("image/jpeg", 1024)

        # Over size
        with self.assertRaises(ValueError):
            validate_payload_limits("image/jpeg", 20 * 1024 * 1024)

    def test_presigned_ttl_boundary(self):
        key = generate_observation_storage_key(self.obs_id, self.img_id, "image/jpeg")

        # 300s OK
        approved_ttl = validate_presigned_request(
            "farmer", self.farmer_id, "upload", key, requested_ttl_seconds=300,
            observation_owner_id=self.farmer_id
        )
        self.assertEqual(approved_ttl, 300)

        # > 600s must fail (Rule P1)
        with self.assertRaises(ValueError):
            validate_presigned_request(
                "farmer", self.farmer_id, "upload", key, requested_ttl_seconds=601,
                observation_owner_id=self.farmer_id
            )

    def test_farmer_cross_tenant_isolation(self):
        key = generate_observation_storage_key(self.obs_id, self.img_id, "image/jpeg")

        # Trying to download another farmer's observation
        with self.assertRaises(PermissionError):
            validate_presigned_request(
                "farmer", self.farmer_id, "download", key, requested_ttl_seconds=300,
                observation_owner_id=self.other_farmer_id
            )

    def test_extension_worker_area_scoping(self):
        key = generate_observation_storage_key(self.obs_id, self.img_id, "image/jpeg")

        # Within assigned area: OK
        validate_presigned_request(
            "extension_worker", self.ext_id, "download", key,
            assigned_geo_codes=["DEMO-BLK-001"], observation_geo_code="DEMO-BLK-001"
        )

        # Outside assigned area: Rejection
        with self.assertRaises(PermissionError):
            validate_presigned_request(
                "extension_worker", self.ext_id, "download", key,
                assigned_geo_codes=["DEMO-BLK-001"], observation_geo_code="DEMO-BLK-002"
            )


if __name__ == "__main__":
    unittest.main()

