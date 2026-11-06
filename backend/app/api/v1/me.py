"""Self-service identity, consent, export and privacy routes (spec 03 §5–§8)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.modules.identity.dependencies import get_current_context, get_identity_service
from app.modules.identity.models import (
    ConsentOverview,
    ConsentUpdate,
    DeletionRequest,
    DeletionResult,
    ExportBundle,
    PrivacyRequest,
    PrivacyRequestCreate,
    UserProfile,
)
from app.modules.identity.service import AuthContext, IdentityService

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserProfile)
def get_profile(
    context: AuthContext = Depends(get_current_context),
    service: IdentityService = Depends(get_identity_service),
) -> UserProfile:
    return service.profile(context)


@router.get("/consents", response_model=ConsentOverview)
def get_consents(
    context: AuthContext = Depends(get_current_context),
    service: IdentityService = Depends(get_identity_service),
) -> ConsentOverview:
    return service.consent_overview(context.user.user_id)


@router.post("/consents", response_model=ConsentOverview)
def update_consents(
    payload: ConsentUpdate,
    context: AuthContext = Depends(get_current_context),
    service: IdentityService = Depends(get_identity_service),
) -> ConsentOverview:
    return service.update_consents(context, payload)


@router.get("/export", response_model=ExportBundle)
def export_own_data(
    purpose: str = Query(..., min_length=8, max_length=500),
    context: AuthContext = Depends(get_current_context),
    service: IdentityService = Depends(get_identity_service),
) -> ExportBundle:
    """Machine-readable export of this account. Every export records a purpose."""

    return service.export_user_data(context, purpose=purpose)


@router.get("/privacy-requests", response_model=list[PrivacyRequest])
def list_privacy_requests(
    context: AuthContext = Depends(get_current_context),
    service: IdentityService = Depends(get_identity_service),
) -> list[PrivacyRequest]:
    return service.list_privacy_requests(context)


@router.post(
    "/privacy-requests",
    response_model=PrivacyRequest,
    status_code=status.HTTP_201_CREATED,
)
def create_privacy_request(
    payload: PrivacyRequestCreate,
    context: AuthContext = Depends(get_current_context),
    service: IdentityService = Depends(get_identity_service),
) -> PrivacyRequest:
    return service.record_privacy_request(context, payload)


@router.delete("", response_model=DeletionResult)
def delete_account(
    payload: DeletionRequest,
    context: AuthContext = Depends(get_current_context),
    service: IdentityService = Depends(get_identity_service),
) -> DeletionResult:
    return service.delete_account(
        context,
        confirmation=payload.confirmation,
        reason=payload.reason,
    )
