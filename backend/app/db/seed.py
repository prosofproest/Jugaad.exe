"""Reference-data seed.

Only configuration and clearly-labelled demo context lives here. No demo
observation, prediction or forecast is created automatically: those require the
explicit ``seed_demo_data`` call. Every weather row seeded here carries
``is_demo = True`` and demo geography codes are prefixed ``DEMO_``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import (
    AlertPolicy,
    Crop,
    CropCalendar,
    Geography,
    ModelRegistry,
    Role,
    SystemConfig,
    Target,
    User,
    UserAreaAssignment,
    UserRole,
    WeatherSnapshot,
)

DEMO_BOUNDARY_VERSION = "demo-2026-11"

ROLE_DEFINITIONS = {
    "farmer": "Field user who submits reports and reads advisories",
    "extension_worker": "Verifies reports, captures on behalf of farmers, shares advisories",
    "admin": "Configuration, users, thresholds, exports, audit",
}

# The crop and target codes follow D1a (tomato, Karnataka). Serving still
# depends on the Gate 0/3 sign-offs; the API labels every model output as demo
# until a real model version is approved in the registry.
CROP_DEFINITIONS = [
    {
        "code": "tomato",
        "name": "Tomato",
        "supported": True,
        "targets": [
            ("tomato_late_blight", "Tomato late blight", "disease", True, True),
            ("tomato_early_blight", "Tomato early blight", "disease", True, True),
            ("tomato_septoria_leaf_spot", "Tomato Septoria leaf spot", "disease", True, True),
            ("tomato_leaf_curl", "Tomato leaf curl symptom complex", "disease", True, False),
            ("healthy", "Healthy tomato foliage", "healthy", True, False),
            ("abiotic_lookalike", "Abiotic or management look-alike", "abiotic", True, False),
            ("unknown_other", "Unknown / other", "unknown", True, False),
        ],
    },
    {
        "code": "banana",
        "name": "Banana (open catalogue, no validated target yet)",
        "supported": False,
        "targets": [],
    },
]

GEOGRAPHIES = [
    ("DEMO_STATE_01", "state", "Demo State", None),
    ("DEMO_DISTRICT_01", "district", "Demo District", "DEMO_STATE_01"),
    ("DEMO_BLOCK_01", "block", "Demo Block One", "DEMO_DISTRICT_01"),
    ("DEMO_BLOCK_02", "block", "Demo Block Two", "DEMO_DISTRICT_01"),
]

# Values are illustrative demo configuration, not measured field evidence.
DEMO_WEATHER = {
    "rainfall_mm_10d": 62.0,
    "consecutive_wet_days": 5,
    "temp_min_c": 18.5,
    "temp_max_c": 27.0,
    "relative_humidity_mean": 82.0,
    "leaf_wetness_hours": 44.0,
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def seed_reference_data(session: Session) -> None:
    settings = get_settings()

    for code, description in ROLE_DEFINITIONS.items():
        if session.get(Role, code) is None:
            session.add(Role(code=code, description=description))

    for code, level, name, parent in GEOGRAPHIES:
        if session.scalar(select(Geography).where(Geography.code == code)) is None:
            session.add(
                Geography(
                    code=code,
                    level=level,
                    name=name,
                    parent_code=parent,
                    boundary_version=DEMO_BOUNDARY_VERSION,
                )
            )

    for crop_def in CROP_DEFINITIONS:
        crop = session.get(Crop, crop_def["code"])
        if crop is None:
            crop = Crop(
                code=crop_def["code"],
                name=crop_def["name"],
                supported=crop_def["supported"],
                supported_from=_utc_now() if crop_def["supported"] else None,
            )
            session.add(crop)
        for code, name, kind, supported, forecast_eligible in crop_def["targets"]:
            existing = session.scalar(
                select(Target).where(
                    Target.crop_code == crop_def["code"], Target.code == code
                )
            )
            if existing is None:
                session.add(
                    Target(
                        crop_code=crop_def["code"],
                        code=code,
                        name=name,
                        kind=kind,
                        supported=supported,
                        forecast_eligible=forecast_eligible,
                    )
                )

    if session.scalar(
        select(CropCalendar).where(
            CropCalendar.crop_code == "tomato",
            CropCalendar.geo_code == "DEMO_BLOCK_01",
            CropCalendar.season == "kharif",
        )
    ) is None:
        session.add(
            CropCalendar(
                crop_code="tomato",
                geo_code="DEMO_BLOCK_01",
                season="kharif",
                planting_window={"start_month": 6, "end_month": 7},
                stage_windows={
                    "vegetative": [20, 40],
                    "flowering": [41, 60],
                    "fruiting": [61, 90],
                },
            )
        )

    # A fresh demo weather snapshot exists only so the pipeline can be exercised
    # locally. It is explicitly labelled demo and is never a real observation.
    existing_weather = session.scalar(
        select(WeatherSnapshot).where(
            WeatherSnapshot.geo_code == "DEMO_BLOCK_01",
            WeatherSnapshot.source == "demo-weather-fixture",
        )
    )
    if existing_weather is None:
        session.add(
            WeatherSnapshot(
                geo_code="DEMO_BLOCK_01",
                source="demo-weather-fixture",
                source_timestamp=_utc_now() - timedelta(hours=2),
                fetched_at=_utc_now(),
                variables=DEMO_WEATHER,
                completeness=1.0,
                is_stale=False,
                is_demo=True,
            )
        )

    model_rows = [
        ("image_gate", settings.quality_gate_version),
        ("image_classifier", settings.image_model_version),
        ("forecast", settings.forecast_model_version),
    ]
    for kind, version in model_rows:
        existing = session.scalar(
            select(ModelRegistry).where(
                ModelRegistry.kind == kind, ModelRegistry.version == version
            )
        )
        if existing is None:
            session.add(
                ModelRegistry(
                    kind=kind,
                    version=version,
                    artefact_key=f"demo/{kind}/{version}",
                    checksum="demo-not-a-real-artefact",
                    metrics={"note": "demo configuration; no measured metrics"},
                    status="approved",
                    approved_by="seed",
                    approved_at=_utc_now(),
                )
            )

    default_config = {
        "consent_version": {"value": "consent-2026-11"},
        "risk_band_thresholds": {
            "value": {"low": 0.25, "moderate": 0.5, "high": 0.75, "urgent": 0.9},
            "note": "demo config; thresholds require agronomist approval",
        },
        "coverage_min_active_reporters": {"value": settings.min_active_reporters},
        "small_count_threshold": {"value": settings.small_count_threshold},
        "forecast_horizon_days": {"value": settings.forecast_horizon_days},
        "boundary_version": {"value": DEMO_BOUNDARY_VERSION},
    }
    for key, value in default_config.items():
        if session.get(SystemConfig, key) is None:
            session.add(SystemConfig(key=key, value=value, updated_by="seed"))

    if session.scalar(
        select(AlertPolicy).where(
            AlertPolicy.geo_code == "DEMO_BLOCK_01",
            AlertPolicy.target_code == "tomato_late_blight",
        )
    ) is None:
        session.add(
            AlertPolicy(
                geo_code="DEMO_BLOCK_01",
                target_code="tomato_late_blight",
                min_band="high",
                min_coverage="partial",
                cooldown_hours=24,
                channels=["in_app"],
                approved_by="seed",
                active=True,
            )
        )

    if settings.bootstrap_admin_email and settings.bootstrap_admin_password:
        _bootstrap_admin(session, settings.bootstrap_admin_email, settings.bootstrap_admin_password)

    if settings.seed_demo_users and not settings.is_production:
        _seed_demo_users(session)


def _ensure_user(
    session: Session,
    *,
    email: str | None = None,
    phone: str | None = None,
    display_name: str | None = None,
    password: str | None = None,
    role_code: str = "farmer",
    mfa_secret: str | None = None,
) -> User:
    from app.core.security import hash_password

    existing = None
    if email:
        existing = session.scalar(select(User).where(User.email == email))
    if existing is None and phone:
        existing = session.scalar(select(User).where(User.phone_e164 == phone))
    if existing is not None:
        return existing

    user = User(
        email=email,
        phone_e164=phone,
        display_name=display_name,
        password_hash=hash_password(password) if password else None,
        active_role=role_code,
        mfa_secret=mfa_secret,
    )
    session.add(user)
    session.flush()
    session.add(
        UserRole(user_id=user.id, role_code=role_code, granted_by="seed", granted_at=_utc_now())
    )
    return user


def _bootstrap_admin(session: Session, email: str, password: str) -> None:
    user = _ensure_user(
        session,
        email=email.lower(),
        display_name="Bootstrap admin",
        password=password,
        role_code="admin",
        mfa_secret=get_settings().bootstrap_admin_mfa_secret,
    )
    if user.active_role != "admin":
        user.active_role = "admin"


def _seed_demo_users(session: Session) -> None:
    from app.core.security import new_totp_secret

    farmer = _ensure_user(
        session,
        phone="+919000000001",
        display_name="Demo farmer",
        role_code="farmer",
    )
    worker = _ensure_user(
        session,
        email="worker@example.test",
        phone="+919000000002",
        display_name="Demo extension worker",
        password="demo-password-change-me",
        role_code="extension_worker",
    )
    admin = _ensure_user(
        session,
        email="admin@example.test",
        display_name="Demo admin",
        password="demo-password-change-me",
        role_code="admin",
        mfa_secret=new_totp_secret(),
    )
    for user in (farmer, worker, admin):
        if user.active_role == "extension_worker" and session.scalar(
            select(UserAreaAssignment).where(
                UserAreaAssignment.user_id == user.id,
                UserAreaAssignment.geo_code == "DEMO_BLOCK_01",
            )
        ) is None:
            session.add(
                UserAreaAssignment(
                    user_id=user.id,
                    geo_code="DEMO_BLOCK_01",
                    level="block",
                    active_from=_utc_now(),
                )
            )
