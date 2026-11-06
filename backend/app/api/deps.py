"""Authentication and authorisation dependencies.

Routes declare their role/permission dependency. A protected route without one
is a defect, not a default.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.db.models import Session as AuthSession
from app.db.models import User
from app.db.session import get_db
from app.modules.identity import service as identity


@dataclass(frozen=True)
class Principal:
    user: User
    session: AuthSession
    role: str
    permissions: tuple[str, ...]
    areas: tuple[str, ...]

    @property
    def id(self) -> str:
        return self.user.id

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_staff(self) -> bool:
        return self.role in {"extension_worker", "admin"}

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions


def get_principal(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Principal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ApiError(401, "unauthorized", "Authentication required")
    token = authorization.split(" ", 1)[1].strip()
    user, session, payload = identity.authenticate_access_token(db, token)
    role = payload.get("role") or ""
    roles = identity.user_roles(db, user.id)
    if role not in roles:
        raise ApiError(403, "forbidden", "Active role is no longer held")
    return Principal(
        user=user,
        session=session,
        role=role,
        permissions=tuple(identity.user_permissions(db, user.id)),
        areas=tuple(identity.active_area_codes(db, user.id)),
    )


def require_roles(*roles: str):
    def _dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if principal.role not in roles:
            raise ApiError(403, "forbidden", "This action is not permitted for your role")
        return principal

    return _dependency


def require_admin(principal: Principal = Depends(get_principal)) -> Principal:
    if principal.role != "admin":
        raise ApiError(403, "forbidden", "Administrator access is required")
    return principal


def require_staff(principal: Principal = Depends(get_principal)) -> Principal:
    if principal.role not in {"extension_worker", "admin"}:
        raise ApiError(403, "forbidden", "Staff access is required")
    return principal


def require_permission(permission: str):
    def _dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if principal.role == "admin" or permission in principal.permissions:
            return principal
        raise ApiError(403, "forbidden", f"Missing permission: {permission}")

    return _dependency
