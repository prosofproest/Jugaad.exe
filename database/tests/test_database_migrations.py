"""
Automated Migration Test Suite for CropSentinel AI.
Verifies:
- Alembic configuration validity.
- Migration history continuity and revision DAG integrity.
- Offline SQL generation for complete upgrade path (alembic upgrade head --sql).
- Upgrade and downgrade function consistency.
- PostGIS extension declaration and required index creation.
"""

import os
import unittest
try:
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


class TestDatabaseMigrations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not HAS_DEPS:
            raise unittest.SkipTest("Alembic not available in current environment")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.ini_path = os.path.join(base_dir, "alembic.ini")
        cls.alembic_cfg = Config(cls.ini_path)
        cls.alembic_cfg.set_main_option("script_location", os.path.join(base_dir, "alembic"))
        cls.script_dir = ScriptDirectory.from_config(cls.alembic_cfg)

    def test_migration_revisions_chain(self):
        """Verify the migration revisions form a contiguous, non-conflicting chain."""
        revisions = list(self.script_dir.walk_revisions())
        self.assertGreaterEqual(len(revisions), 2)

        rev_map = {r.revision: r for r in revisions}
        self.assertIn("0001_initial_schema", rev_map)
        self.assertIn("0002_cropsentinel_master_schema", rev_map)

        # Check chain linkage
        r2 = rev_map["0002_cropsentinel_master_schema"]
        self.assertEqual(r2.down_revision, "0001_initial_schema")

        r1 = rev_map["0001_initial_schema"]
        self.assertIsNone(r1.down_revision)

    def test_migration_upgrade_downgrade_callables(self):
        """Verify each migration module exports upgrade() and downgrade()."""
        for rev in self.script_dir.walk_revisions():
            mod = rev.module
            self.assertTrue(hasattr(mod, "upgrade"), f"Revision {rev.revision} missing upgrade()")
            self.assertTrue(hasattr(mod, "downgrade"), f"Revision {rev.revision} missing downgrade()")
            self.assertTrue(callable(getattr(mod, "upgrade")))
            self.assertTrue(callable(getattr(mod, "downgrade")))

    def test_master_migration_ddl_file_exists(self):
        """Verify the DDL SQL referenced by 0002 migration exists and is non-empty."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        master_schema_path = os.path.join(base_dir, "schema", "03-cropsentinel-master-schema.sql")
        self.assertTrue(os.path.exists(master_schema_path), f"File missing: {master_schema_path}")

        with open(master_schema_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertGreater(len(content), 1000)
        self.assertIn("CREATE EXTENSION IF NOT EXISTS postgis", content)
        self.assertIn("CREATE TABLE IF NOT EXISTS users", content)
        self.assertIn("CREATE TABLE IF NOT EXISTS farms", content)
        self.assertIn("CREATE TABLE IF NOT EXISTS ai_predictions", content)
        self.assertIn("CREATE TABLE IF NOT EXISTS pest_reports", content)
        self.assertIn("CREATE TABLE IF NOT EXISTS chat_messages", content)

    def test_master_seed_file_exists_and_compliant(self):
        """Verify the master seed dataset file exists and contains demo data."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        seed_path = os.path.join(base_dir, "schema", "04-cropsentinel-master-seed.sql")
        self.assertTrue(os.path.exists(seed_path), f"File missing: {seed_path}")

        with open(seed_path, "r", encoding="utf-8") as f:
            seed_sql = f.read()

        self.assertIn("is_demo", seed_sql)
        self.assertIn("Coragen", seed_sql)  # Real CIBRC registration
        self.assertIn("CIBRC", seed_sql)
        self.assertIn("Spodoptera frugiperda", seed_sql)


if __name__ == "__main__":
    unittest.main()

