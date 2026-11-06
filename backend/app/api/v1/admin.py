"""Admin identity routes (spec 03 §3, §6, §8 and §11).

Every route requires the admin role. Individual record views need a reason and
write ``admin.record_viewed`` before the record is returned. Exports carry a
written purpose and audit event.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query, status

from app.modules.identity.dependencies import get_identity_service, require_roles
from app.modules.identity.models import (
    AdminExportRequest,
    AdminExportSummary,
    AdminUserDetail,
    MaintenanceRequest,
    RetentionResult,
    RoleUpdateRequest,
    StaffCreateRequest,
    StaffProvisioned,
    UserStatusUpdate,
    UserSummary,
)
from app.modules.identity.service import AuthContext, IdentityService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserSummary])
def list_users(
    context: AuthContext = Depends(require_roles("admin")),
    service: IdentityService = Depends(get_identity_service),
) -> list[UserSummary]:
    return service.list_users(context)


@router.post(
    "/users",
    response_model=StaffProvisioned,
    status_code=status.HTTP_201_CREATED,
)
def provision_staff(
    payload: StaffCreateRequest,
    context: AuthContext = Depends(require_roles("admin")),
    service: IdentityService = Depends(get_identity_service),
) -> StaffProvisioned:
    """Provision an extension worker, pathologist, agronomist or admin.

    The MFA secret is returned once so the account holder can enrol it. It is
    never written to logs or audit details.
    """

    return service.provision_staff(context, payload)


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def view_user(
    user_id: str = Path(..., min_length=3, max_length=80),
    reason: str = Query(..., max_length=500),
    context: AuthContext = Depends(require_roles("admin")),
    service: IdentityService = Depends(get_identity_service),
) -> AdminUserDetail:
    return service.admin_view_user(context, user_id, reason)


@router.patch("/users/{user_id}/roles", response_model=UserSummary)
def change_roles(
    payload: RoleUpdateRequest,
    user_id: str = Path(..., min_length=3, max_length=80),
    context: AuthContext = Depends(require_roles("admin")),
    service: IdentityService = Depends(get_identity_service),
) -> UserSummary:
    return service.change_roles(context, user_id, payload)


@router.patch("/users/{user_id}/status", response_model=UserSummary)
def change_status(
    payload: UserStatusUpdate,
    user_id: str = Path(..., min_length=3, max_length=80),
    context: AuthContext = Depends(require_roles("admin")),
    service: IdentityService = Depends(get_identity_service),
) -> UserSummary:
    return service.set_user_status(context, user_id, payload)


@router.post("/maintenance/retention", response_model=RetentionResult)
def run_retention(
    payload: MaintenanceRequest,
    context: AuthContext = Depends(require_roles("admin")),
    service: IdentityService = Depends(get_identity_service),
) -> RetentionResult:
    return service.run_retention(context, payload.reason)


@router.post("/exports", response_model=AdminExportSummary)
def export_aggregates(
    payload: AdminExportRequest,
    context: AuthContext = Depends(require_roles("admin")),
    service: IdentityService = Depends(get_identity_service),
) -> AdminExportSummary:
    return service.export_aggregates(context, payload)
