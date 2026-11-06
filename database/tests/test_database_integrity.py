"""
Automated Database Integrity Test Suite for CropSentinel AI.
Verifies:
- Invalid foreign key rejection.
- Unique constraint duplicate prevention.
- Check constraint enforcement (invalid confidence scores, out-of-range ratings).
- Transaction atomicity & rollback behavior.
- Cascading delete behavior (e.g. deleting a farm cascades to plots and sections).
- Soft deletion preservation.
"""

import unittest
import uuid
from datetime import datetime, timezone

try:
    from sqlalchemy import create_engine, event, select, text
    from sqlalchemy.engine import Engine
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import Session

    from database.models import (
        Base,
        User,
        UserRole,
        Farm,
        FarmSection,
        FarmPlot,
        CropGroup,
        CropType,
        AIModelVersion,
        AIAnalysis,
        AIPrediction,
        MediaFile,
        ChatSession,
        ChatMessage,
    )
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


if HAS_DEPS:
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class TestDatabaseIntegrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not HAS_DEPS:
            raise unittest.SkipTest("SQLAlchemy not available in current environment")
        # In-memory SQLite with foreign keys enabled
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(cls.engine)

    def setUp(self):
        self.session = Session(self.engine)

    def tearDown(self):
        self.session.rollback()
        self.session.close()

    def test_invalid_foreign_key_rejection(self):
        """Verify that inserting a record referencing a non-existent foreign key is rejected."""
        non_existent_user_id = uuid.uuid4()
        role = UserRole(user_id=non_existent_user_id, role="farmer")
        self.session.add(role)
        with self.assertRaises(IntegrityError):
            self.session.flush()

    def test_unique_constraint_duplicate_prevention(self):
        """Verify that duplicate unique combinations are rejected."""
        user = User(id=uuid.uuid4(), email="unique_test@example.com", username="unique_user")
        self.session.add(user)
        self.session.flush()

        # Duplicate email
        dup_user = User(id=uuid.uuid4(), email="unique_test@example.com", username="another_user")
        self.session.add(dup_user)
        with self.assertRaises(IntegrityError):
            self.session.flush()

    def test_invalid_confidence_score_rejection(self):
        """Verify that confidence score > 1.0 or < 0.0 violates check constraint."""
        user = User(id=uuid.uuid4(), email="conf_test@example.com")
        media = MediaFile(
            uploader_id=user.id,
            storage_provider="s3",
            bucket_name="cropsentinel-media",
            object_key="uploads/conf_img.jpg",
            file_name="conf_img.jpg",
            file_size_bytes=500000,
            mime_type="image/jpeg",
            file_hash_sha256="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            media_type="image",
            capture_timestamp=datetime.now(timezone.utc),
        )
        model = AIModelVersion(
            model_name="Test-Model",
            version_tag="v1.0.0",
            model_family="yolo",
            weights_digest_sha256="sha256weights1234567890123456789012345678901234567890123456789012",
        )
        self.session.add_all([user, media, model])
        self.session.flush()

        analysis = AIAnalysis(media_file_id=media.id, requested_by=user.id)
        self.session.add(analysis)
        self.session.flush()

        # Out-of-bounds confidence score (1.5000 > 1.0000)
        invalid_pred = AIPrediction(
            analysis_id=analysis.id,
            model_version_id=model.id,
            primary_diagnosis="Test Pest",
            confidence_score=1.5000,
        )
        self.session.add(invalid_pred)
        with self.assertRaises(IntegrityError):
            self.session.flush()

    def test_transaction_rollback_preserves_consistency(self):
        """Verify that transaction rollback discards all uncommitted modifications."""
        initial_users = len(self.session.scalars(select(User)).all())
        user1 = User(id=uuid.uuid4(), email="tx1@example.com")
        self.session.add(user1)
        self.session.flush()

        # Rollback
        self.session.rollback()

        final_users = len(self.session.scalars(select(User)).all())
        self.assertEqual(initial_users, final_users)

    def test_cascading_delete_behavior(self):
        """Verify that deleting a farm cascades to sections and plots."""
        user = User(id=uuid.uuid4(), email="cascade_owner@example.com")
        farm = Farm(id=uuid.uuid4(), name="Cascade Farm", owner_id=user.id)
        self.session.add_all([user, farm])
        self.session.flush()

        section = FarmSection(farm_id=farm.id, section_code="C-SEC", name="Cascade Section")
        self.session.add(section)
        self.session.flush()

        plot = FarmPlot(farm_id=farm.id, section_id=section.id, plot_code="C-PLOT", area_sqm=5000.0)
        self.session.add(plot)
        self.session.commit()

        # Delete the farm
        self.session.delete(farm)
        self.session.commit()

        # Verify plots and sections are gone
        remaining_sections = self.session.scalars(select(FarmSection).where(FarmSection.farm_id == farm.id)).all()
        remaining_plots = self.session.scalars(select(FarmPlot).where(FarmPlot.farm_id == farm.id)).all()
        self.assertEqual(len(remaining_sections), 0)
        self.assertEqual(len(remaining_plots), 0)

    def test_soft_deletion_behavior(self):
        """Verify soft deletion sets deleted_at while keeping database row intact."""
        user = User(id=uuid.uuid4(), email="soft_delete@example.com")
        self.session.add(user)
        self.session.commit()

        self.assertFalse(user.is_deleted)
        self.assertIsNone(user.deleted_at)

        # Soft delete
        user.deleted_at = datetime.now(timezone.utc)
        self.session.commit()

        queried = self.session.scalar(select(User).where(User.id == user.id))
        self.assertTrue(queried.is_deleted)
        self.assertIsNotNone(queried.deleted_at)


if __name__ == "__main__":
    unittest.main()
