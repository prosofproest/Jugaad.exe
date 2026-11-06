"""Authentication and profile routes."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.errors import ApiError
from app.core.security import hash_password
from app.db.models import AuditEvent, User, UserRole
from app.db.session import get_db
from app.modules.audit.service import record_audit
from app.modules.identity import service
from app.modules.identity.service import (
    ALL_CONSENTS,
    grant_consent,
    me_payload,
    missing_required_consents,
)

router = APIRouter(tags=["auth"])


class OtpRequest(BaseModel):
    phone: str = Field(min_length=6, max_length=24)


class OtpVerify(BaseModel):
    phone: str = Field(min_length=6, max_length=24)
    code: str = Field(min_length=4, max_length=10)
    device_id: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class MfaVerify(BaseModel):
    challenge: str
    totp: str = Field(min_length=6, max_length=10)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class ConsentRequest(BaseModel):
    type: str
    granted: bool
    channel: str = "app"


class ProfileUpdate(BaseModel):
    locale: str | None = None
    display_name: str | None = None


def _ip_hash(request: Request) -> str | None:
    import hashlib

    client = request.client.host if request.client else None
    if not client:
        return None
    return hashlib.sha256(client.encode("utf-8")).hexdigest()


@router.post("/auth/otp/request", status_code=status.HTTP_202_ACCEPTED)
def otp_request(payload: OtpRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    result = service.request_otp(db, phone=payload.phone, ip=_ip_hash(request))
    db.commit()
    return result


@router.post("/auth/otp/verify")
def otp_verify(payload: OtpVerify, request: Request, db: Session = Depends(get_db)) -> dict:
    tokens = service.verify_otp(
        db,
        phone=payload.phone,
        code=payload.code,
        device_id=payload.device_id,
        user_agent=request.headers.get("User-Agent"),
        ip_hash=_ip_hash(request),
    )
    db.commit()
    return tokens


@router.post("/auth/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    result = service.login(
        db,
        email=str(payload.email),
        password=payload.password,
        user_agent=request.headers.get("User-Agent"),
        ip_hash=_ip_hash(request),
    )
    db.commit()
    return result


@router.post("/auth/mfa/verify")
def mfa_verify(payload: MfaVerify, request: Request, db: Session = Depends(get_db)) -> dict:
    tokens = service.verify_mfa(
        db,
        challenge=payload.challenge,
        totp=payload.totp,
        user_agent=request.headers.get("User-Agent"),
        ip_hash=_ip_hash(request),
    )
    db.commit()
    return tokens


@router.post("/auth/refresh")
def refresh(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    tokens = service.refresh_tokens(
        db,
        refresh_token=payload.refresh_token,
        user_agent=request.headers.get("User-Agent"),
        ip_hash=_ip_hash(request),
    )
    db.commit()
    return tokens


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    service.logout(db, user=user, session_id=getattr(request.state, "session_id", None))
    db.commit()


@router.post("/auth/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    service.logout_all(db, user=user)
    db.commit()


@router.post("/auth/mfa/setup")
def mfa_setup(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    secret, uri = service.ensure_mfa_secret(db, user)
    db.commit()
    return {
        "secret": secret,
        "provisioning_uri": uri,
        "note": "Scan the URI with an authenticator app before signing in again.",
    }


@router.get("/me")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return me_payload(db, user)


@router.patch("/me")
def update_me(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if payload.locale is not None:
        if payload.locale not in {"en", "kn"}:
            raise ApiError(422, "unsupported_language", "Supported languages are en and kn")
        user.locale = payload.locale
    if payload.display_name is not None:
        user.display_name = payload.display_name[:200]
    db.commit()
    return me_payload(db, user)


@router.get("/me/consents")
def list_consents(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return {
        "consents": service.consent_snapshot(db, user.id),
        "missing_required": missing_required_consents(db, user.id),
        "allowed_types": list(ALL_CONSENTS),
    }


@router.post("/me/consents", status_code=status.HTTP_201_CREATED)
def create_consent(
    payload: ConsentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    grant_consent(
        db,
        user,
        consent_type=payload.type,
        granted=payload.granted,
        channel=payload.channel,
    )
    db.commit()
    return {
        "consents": service.consent_snapshot(db, user.id),
        "missing_required": missing_required_consents(db, user.id),
    }


@router.delete("/me", status_code=status.HTTP_202_ACCEPTED)
def delete_me(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Soft-delete the account and revoke every session.

    Queued reports must be resolved or discarded first; this backend cannot see
    a device queue, so it refuses while the user has unfinished observations.
    """

    from app.db.models import Observation

    unfinished = db.query(Observation).filter(
        Observation.user_id == user.id,
        Observation.deleted_at.is_(None),
        Observation.status.in_(["draft", "pending_upload", "uploading", "failed"]),
    ).count()
    if unfinished:
        raise ApiError(
            409,
            "queue_not_empty",
            "Resolve or discard queued reports before deleting the account",
            detail=f"{unfinished} unfinished report(s) remain.",
        )
    user.status = "deleted"
    user.deleted_at = datetime.now(timezone.utc)
    user.token_version += 1
    service.logout_all(db, user=user)
    record_audit(
        db, action="privacy.deleted", actor=user, entity_type="user", entity_id=user.id
    )
    db.commit()
    return {"status": "scheduled_for_deletion", "request_id": getattr(request.state, "request_id", None)}


# ---------------------------------------------------------------------------
# Admin: user and role management
# ---------------------------------------------------------------------------
admin_router = APIRouter(prefix="/admin", tags=["admin"])


class RoleChangeRequest(BaseModel):
    role_code: str
    granted: bool = True
    reason: str | None = None


class PermissionChangeRequest(BaseModel):
    permission: str
    granted: bool = True
    reason: str | None = None


def _require_admin(db: Session, user: User) -> None:
    if "admin" not in service.active_roles(db, user.id):
        raise ApiError(403, "forbidden", "Admin role required")


@admin_router.get("/users")
def admin_list_users(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    _require_admin(db, user)
    rows = db.query(User).order_by(User.created_at.desc()).limit(500).all()
    return {
        "items": [
            {
                "id": row.id,
                "email": row.email,
                "phone": row.phone_e164,
                "display_name": row.display_name,
                "status": row.status,
                "active_role": row.active_role,
                "roles": service.active_roles(db, row.id),
                "permissions": sorted(service.active_permissions(db, row.id)),
            }
            for row in rows
        ]
    }


@admin_router.patch("/users/{user_id}/roles")
def admin_change_role(
    user_id: str,
    payload: RoleChangeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _require_admin(db, user)
    from app.db.models import Role

    target = db.get(User, user_id)
    if target is None:
        raise ApiError(404, "not_found", "User not found")
    if db.get(Role, payload.role_code) is None:
        raise ApiError(422, "unknown_role", "Unknown role code")
    existing = db.query(UserRole).filter(
        UserRole.user_id == target.id,
        UserRole.role_code == payload.role_code,
        UserRole.revoked_at.is_(None),
    ).first()
    if payload.granted and existing is None:
        db.add(
            UserRole(
                user_id=target.id,
                role_code=payload.role_code,
                granted_by=user.id,
            )
        )
    elif not payload.granted and existing is not None:
        existing.revoked_at = datetime.now(timezone.utc)
    target.token_version += 1
    record_audit(
        db,
        action="user.role_changed",
        actor=user,
        entity_type="user",
        entity_id=target.id,
        reason=payload.reason,
        detail={"role_code": payload.role_code, "granted": payload.granted},
    )
    db.commit()
    return {"user_id": target.id, "roles": service.active_roles(db, target.id)}


@admin_router.patch("/users/{user_id}/permissions")
def admin_change_permission(
    user_id: str,
    payload: PermissionChangeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _require_admin(db, user)
    from app.db.models import UserPermission

    if payload.permission not in {"can_confirm", "can_approve_advisory"}:
        raise ApiError(422, "unknown_permission", "Unknown permission")
    target = db.get(User, user_id)
    if target is None:
        raise ApiError(404, "not_found", "User not found")
    existing = db.query(UserPermission).filter(
        UserPermission.user_id == target.id,
        UserPermission.permission == payload.permission,
        UserPermission.revoked_at.is_(None),
    ).first()
    if payload.granted and existing is None:
        db.add(
            UserPermission(
                user_id=target.id,
                permission=payload.permission,
                granted_by=user.id,
            )
        )
    elif not payload.granted and existing is not None:
        existing.revoked_at = datetime.now(timezone.utc)
    target.token_version += 1
    record_audit(
        db,
        action="user.permission_changed",
        actor=user,
        entity_type="user",
        entity_id=target.id,
        reason=payload.reason,
        detail={"permission": payload.permission, "granted": payload.granted},
    )
    db.commit()
    return {
        "user_id": target.id,
        "permissions": sorted(service.active_permissions(db, target.id)),
    }


@admin_router.get("/audit")
def admin_audit_log(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 100,
) -> dict:
    _require_admin(db, user)
    rows = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(min(limit, 500)).all()
    return {
        "items": [
            {
                "id": row.id,
                "actor_id": row.actor_id,
                "actor_role": row.actor_role,
                "action": row.action,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "reason": row.reason,
                "request_id": row.request_id,
                "detail": row.detail,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }
