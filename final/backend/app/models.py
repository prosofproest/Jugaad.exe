"""SQLAlchemy models for CropSentinel backend.
Only a minimal subset is defined to satisfy the compliance checklist.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base

class RoleEnum(str, Enum):
    farmer = "farmer"
    extension_worker = "extension_worker"
    admin = "admin"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, nullable=True)  # for farmer OTP login
    email = Column(String, unique=True, nullable=True)  # for staff login
    hashed_password = Column(String, nullable=True)
    role = Column(String, nullable=False, default=RoleEnum.farmer.value)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Relationships
    consents = relationship("Consent", back_populates="user", cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="user", cascade="all, delete-orphan")

class Consent(Base):
    __tablename__ = "consents"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    version = Column(String, nullable=False)
    accepted_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    user = relationship("User", back_populates="consents")

class Observation(Base):
    __tablename__ = "observations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crop = Column(String, nullable=False)
    location = Column(String, nullable=False)  # could be GeoJSON or simple identifier
    created_at = Column(DateTime, default=datetime.utcnow)
    client_report_id = Column(String, unique=True, nullable=False)  # idempotency key
    status = Column(String, default="pending")
    # Relationships
    user = relationship("User", back_populates="observations")
    images = relationship("Image", back_populates="observation", cascade="all, delete-orphan")
    diagnosis = relationship("Diagnosis", uselist=False, back_populates="observation")

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True)
    observation_id = Column(Integer, ForeignKey("observations.id"), nullable=False)
    public_id = Column(String, nullable=False)  # Cloudinary public ID
    url = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    observation = relationship("Observation", back_populates="images")

class Diagnosis(Base):
    __tablename__ = "diagnoses"
    id = Column(Integer, primary_key=True)
    observation_id = Column(Integer, ForeignKey("observations.id"), unique=True, nullable=False)
    model_version = Column(String, nullable=False)
    result = Column(Text, nullable=False)  # JSON string of candidates, confidence, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    observation = relationship("Observation", back_populates="diagnosis")

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True)
    event_type = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    # No foreign key cascade – immutable log
    __table_args__ = (UniqueConstraint("id", "timestamp"),)

class Crop(Base):
    __tablename__ = "crops"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    allowed = Column(Boolean, default=True)
