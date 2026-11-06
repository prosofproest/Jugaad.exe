"""Gate 4 forecast reproducibility and input-sensitivity tests.

The database is an in-memory SQLite transport. Every crop, target, geography,
weather value, report and boundary version below is a synthetic fixture. The
ruled baseline is demo configuration: these tests prove plumbing and
determinism, not field accuracy, calibration or an approved operating point.

Gate 4 exit criterion: a forecast can be reproduced from fixtures, and its
inputs provably affect the output.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from app.core.config import get_settings
from app.core.errors import ApiError
from app.db.base import Base
from app.db.models import (
    Crop,
    CropCalendar,
    FeatureSnapshot,
    Forecast,
    ForecastRun,
    Geography,
    ModelRegistry,
    Observation,
    ObservationVerification,
    SystemConfig,
    Target,
    User,
    WeatherSnapshot,
)
from app.modules.forecast import service
from app.modules.forecast.rules import BAND_RANK, score_weather
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

CROP = "crop-synthetic"
TARGET = "target-synthetic"
GEO = "geo-synthetic"
BOUNDARY_VERSION = "bv-synthetic-1"

DRY_WEATHER = {
    "rainfall_mm_10d": 5.0,
    "consecutive_wet_days": 1,
    "relative_humidity_mean": 55.0,
    "temp_min_c": 8.0,
    "temp_max_c": 34.0,
    "leaf_wetness_hours": 2.0,
}

WET_WEATHER = {
    "rainfall_mm_10d": 62.0,
    "consecutive_wet_days": 5,
    "relative_humidity_mean": 82.0,
    "temp_min_c": 18.5,
    "temp_max_c": 27.0,
    "leaf_wetness_hours": 44.0,
}


@dataclass(frozen=True)
class Generated:
    """A generated forecast plus the lineage needed to re-derive its score."""

    forecast_id: str
    risk_band: str
    probability: float | None
    drivers: tuple[str, ...]
    reason_code: str | None
    coverage: str
    features: dict
    created: bool


def _session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def db() -> Iterator[Session]:
    yield from _session()


def _seed(
    db: Session,
    *,
    weather: dict | None = WET_WEATHER,
    weather_age: timedelta = timedelta(hours=1),
    weather_completeness: float = 1.0,
    reporters: int = 3,
    verified_reports: int = 0,
    boundary_version: str = BOUNDARY_VERSION,
    configured_boundary: str = BOUNDARY_VERSION,
    calendar: bool = True,
    model_status: str = "approved",
) -> None:
    settings = get_settings()
    now = datetime.now(UTC)

    db.add(Crop(code=CROP, name="Synthetic crop", supported=True))
    db.add(
        Target(
            id="tgt-synthetic",
            crop_code=CROP,
            code=TARGET,
            name="Synthetic target",
            kind="disease",
            supported=True,
            forecast_eligible=True,
        )
    )
    db.add(
        Geography(
            id="geo-synthetic",
            code=GEO,
            level="block",
            name="Synthetic Block",
            boundary_version=boundary_version,
        )
    )
    if calendar:
        db.add(
            CropCalendar(
                id="ccal-synthetic",
                crop_code=CROP,
                geo_code=GEO,
                season="synthetic-season",
                planting_window={},
                stage_windows={},
            )
        )
    db.add(SystemConfig(key="boundary_version", value={"value": configured_boundary}))
    db.add(
        ModelRegistry(
            kind="forecast",
            version=settings.forecast_model_version,
            artefact_key="synthetic/forecast",
            checksum="synthetic-not-a-real-artefact",
            metrics={"note": "synthetic fixture; no measured metrics"},
            status=model_status,
        )
    )
    if weather is not None:
        db.add(
            WeatherSnapshot(
                id="wxs-synthetic",
                geo_code=GEO,
                source="synthetic",
                source_timestamp=now - weather_age,
                fetched_at=now,
                variables=dict(weather),
                completeness=weather_completeness,
                is_stale=weather_age > timedelta(hours=24),
                is_demo=True,
            )
        )

    for index in range(reporters):
        user_id = f"usr-synthetic-{index}"
        db.add(
            User(
                id=user_id,
                phone_e164=f"+1000000000{index}",
                display_name=f"Synthetic reporter {index}",
                status="active",
            )
        )
        observation = Observation(
            id=f"obs-synthetic-{index}",
            client_report_id=f"client-synthetic-{index}",
            user_id=user_id,
            area_code=GEO,
            crop_code=CROP,
            submitted_at=now,
            created_at=now,
            status="submitted",
            is_demo=True,
        )
        db.add(observation)
        db.flush()
        status = "confirmed" if index < verified_reports else "pending_review"
        db.add(
            ObservationVerification(
                observation_id=observation.id,
                status=status,
                evidence_tier="synthetic",
            )
        )

    db.commit()


def _generate(db: Session, *, force: bool = False) -> Generated:
    forecast, created = service.generate_forecast(
        db,
        actor=None,
        crop_code=CROP,
        target_code=TARGET,
        geo_code=GEO,
        force=force,
    )
    db.commit()
    snapshot = db.get(FeatureSnapshot, forecast.feature_snapshot_id)
    assert snapshot is not None
    return Generated(
        forecast_id=forecast.id,
        risk_band=forecast.risk_band,
        probability=(None if forecast.probability is None else float(forecast.probability)),
        drivers=tuple(forecast.drivers),
        reason_code=forecast.reason_code,
        coverage=forecast.coverage,
        features=dict(snapshot.features),
        created=created,
    )


def _one(**seed_overrides) -> Generated:
    generator = _session()
    db = next(generator)
    try:
        _seed(db, **seed_overrides)
        return _generate(db)
    finally:
        generator.close()


def test_forecast_is_reproducible_from_the_stored_feature_snapshot() -> None:
    result = _one(verified_reports=1)

    features = result.features
    recomputed = score_weather(
        features["weather"],
        verified_reports_14d=features["verified_reports_14d"],
    )

    assert recomputed.score == features["rule_score"]
    assert recomputed.risk_band == result.risk_band
    assert recomputed.drivers == result.drivers
    assert features["rule_result"]["score"] == features["rule_score"]
    assert features["rule_result"]["drivers"] == list(result.drivers)
    assert features["weather_source_timestamp"]


def test_two_weather_fixtures_change_the_band_and_drivers() -> None:
    dry = _one(weather=DRY_WEATHER)
    wet = _one(weather=WET_WEATHER)

    assert dry.features["rule_score"] == 0.0
    assert wet.features["rule_score"] == 0.9
    assert dry.risk_band == "low"
    assert wet.risk_band == "urgent"
    assert BAND_RANK[wet.risk_band] > BAND_RANK[dry.risk_band]
    assert dry.drivers == ()
    assert "recent_rainfall" in wet.drivers


def test_verified_reports_change_the_score_with_identical_weather() -> None:
    without = _one(weather=WET_WEATHER, verified_reports=0)
    with_report = _one(weather=WET_WEATHER, verified_reports=1)

    assert with_report.features["weather"] == without.features["weather"]
    assert with_report.coverage == without.coverage == "good"
    difference = with_report.features["rule_score"] - without.features["rule_score"]
    assert round(difference, 3) == 0.1
    assert "verified_local_reports" not in without.drivers
    assert "verified_local_reports" in with_report.drivers


def test_missing_weather_is_insufficient_data_with_no_probability() -> None:
    result = _one(weather=None, reporters=3)

    assert result.risk_band == "insufficient_data"
    assert result.probability is None
    assert result.reason_code == "weather_stale"
    assert "rule_score" not in result.features


def test_stale_weather_is_insufficient_data_with_no_probability() -> None:
    result = _one(weather=WET_WEATHER, weather_age=timedelta(hours=48))

    assert result.risk_band == "insufficient_data"
    assert result.probability is None
    assert result.reason_code == "weather_stale"


def test_low_coverage_is_insufficient_data_with_no_probability() -> None:
    result = _one(weather=WET_WEATHER, reporters=0)

    assert result.risk_band == "insufficient_data"
    assert result.probability is None
    assert result.reason_code == "insufficient_coverage"
    assert result.coverage == "low"


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    [
        ({"calendar": False}, "calendar_missing"),
        (
            {
                "boundary_version": "bv-synthetic-2",
                "configured_boundary": BOUNDARY_VERSION,
            },
            "boundary_mismatch",
        ),
    ],
)
def test_other_gate_failures_refuse_a_score(overrides: dict, expected_reason: str) -> None:
    result = _one(weather=WET_WEATHER, **overrides)

    assert result.risk_band == "insufficient_data"
    assert result.probability is None
    assert result.reason_code == expected_reason


def test_same_day_generation_is_idempotent_unless_forced(db: Session) -> None:
    _seed(db, weather=WET_WEATHER)

    first = _generate(db)
    second = _generate(db)
    forced = _generate(db, force=True)

    assert first.created is True
    assert second.created is False
    assert second.forecast_id == first.forecast_id
    assert forced.created is True
    assert forced.forecast_id != first.forecast_id

    runs = db.scalars(select(ForecastRun)).all()
    assert len(runs) == 2
    assert {run.status for run in runs} == {"succeeded"}
    assert sum(run.areas_scored for run in runs) == 2


def test_unapproved_model_refuses_to_generate(db: Session) -> None:
    _seed(db, weather=WET_WEATHER, model_status="draft")

    with pytest.raises(ApiError) as error:
        _generate(db)

    assert error.value.status_code == 409
    assert error.value.code == "model_not_approved"
    assert db.scalars(select(Forecast)).all() == []
