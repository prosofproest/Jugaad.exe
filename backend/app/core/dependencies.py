"""Authentication, role and object-scope dependencies.

Deny by default: a route without an explicit dependency is a defect. Object
checks live here so routers cannot accidentally filter after fetch.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.security import TokenError, decode_access_token
from app.db.models import Session as AuthSession
from app.db.models import User, UserAreaAssignment, UserPermission, UserRole
from app.db.session import get_db


def _now() -> datetime:
    return datetime.now(UTC)


def _bearer(request: Request) -> str | None:
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    token = header[7:].strip()
    return token or None


def active_roles(db: Session, user_id: str) -> list[str]:
    rows = db.scalars(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.revoked_at.is_(None))
    ).all()
    return [row.role_code for row in rows]


def active_permissions(db: Session, user_id: str) -> set[str]:
    rows = db.scalars(
        select(UserPermission).where(
            UserPermission.user_id == user_id, UserPermission.revoked_at.is_(None)
        )
    ).all()
    return {row.permission for row in rows}


def user_has_permission(db: Session, user_id: str, permission: str) -> bool:
    return permission in active_permissions(db, user_id)


def assigned_area_codes(db: Session, user_id: str) -> set[str]:
    now = _now()
    rows = db.scalars(
        select(UserAreaAssignment).where(
            UserAreaAssignment.user_id == user_id,
            UserAreaAssignment.active_from <= now,
            (UserAreaAssignment.active_to.is_(None)) | (UserAreaAssignment.active_to > now),
        )
    ).all()
    return {row.geo_code for row in rows}


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = _bearer(request)
    if not token:
        raise ApiError(401, "unauthorized", "Authentication required")
    try:
        payload = decode_access_token(token)
    except TokenError as error:
        raise ApiError(401, error.code, "Authentication failed", detail=error.detail) from error

    user = db.get(User, payload.get("sub", ""))
    if user is None or user.status != "active" or user.deleted_at is not None:
        raise ApiError(401, "unauthorized", "Account is not active")

    session_id = payload.get("session_id")
    auth_session = db.get(AuthSession, session_id) if session_id else None
    if auth_session is None or auth_session.revoked_at is not None:
        raise ApiError(401, "token_revoked", "Session has been revoked")
    if auth_session.expires_at <= _now():
        raise ApiError(401, "token_expired", "Session has expired")
    if (
        auth_session.token_version != user.token_version
        or payload.get("token_version") != user.token_version
    ):
        raise ApiError(401, "token_stale", "Token is out of date; sign in again")

    roles = active_roles(db, user.id)
    if payload.get("role") not in roles:
        raise ApiError(401, "token_stale", "Active role is no longer granted")

    request.state.user = user
    request.state.roles = roles
    request.state.permissions = active_permissions(db, user.id)
    request.state.session_id = session_id
    return user


def current_roles(request: Request) -> list[str]:
    return getattr(request.state, "roles", [])


def current_permissions(request: Request) -> set[str]:
    return getattr(request.state, "permissions", set())


def require_roles(*allowed: str):
    def _dependency(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if not set(active_roles(db, user.id)).intersection(allowed):
            raise ApiError(403, "forbidden", "Your role cannot perform this action")
        return user

    return _dependency


def require_permission(permission: str):
    def _dependency(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if not user_has_permission(db, user.id, permission):
            raise ApiError(
                403,
                "forbidden",
                "Missing required permission",
                detail=f"Permission '{permission}' is required.",
            )
        return user

    return _dependency


def require_any_role_or_permission(roles: Iterable[str], permission: str | None = None):
    role_set = set(roles)

    def _dependency(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if set(active_roles(db, user.id)).intersection(role_set):
            return user
        if permission and user_has_permission(db, user.id, permission):
            return user
        raise ApiError(403, "forbidden", "Your role cannot perform this action")

    return _dependency


def require_idempotency_key(
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> str:
    if not idempotency_key or len(idempotency_key) > 200:
        raise ApiError(
            400,
            "idempotency_key_required",
            "Idempotency-Key header is required",
            detail="Send a client-generated idempotency key with this request.",
        )
    return idempotency_key


def can_read_observation(
    db: Session, user: User, observation, *, roles: list[str] | None = None
) -> bool:
    roles = roles if roles is not None else active_roles(db, user.id)
    if observation.user_id == user.id or observation.subject_user_id == user.id:
        return True
    if "admin" in roles:
        return True
    if "extension_worker" in roles:
        return observation.area_code in assigned_area_codes(db, user.id)
    return False
