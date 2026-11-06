"""Authentication routes (spec 03 §4 and §8).

Public routes are intentionally limited to OTP request/verify, staff login,
MFA verification and refresh. Everything else resolves a bearer token.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from app.modules.identity.dependencies import get_current_context, get_identity_service
from app.modules.identity.models import (
    LoginRequest,
    LoginResponse,
    MfaVerifyRequest,
    OtpRequest,
    OtpRequested,
    OtpVerifyRequest,
    RefreshRequest,
    TokenPair,
)
from app.modules.identity.service import AuthContext, IdentityService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/otp/request", response_model=OtpRequested, status_code=status.HTTP_202_ACCEPTED)
def request_otp(
    payload: OtpRequest,
    request: Request,
    service: IdentityService = Depends(get_identity_service),
) -> OtpRequested:
    """Send a farmer sign-in code. The response never reveals account existence."""

    source_ip = request.client.host if request.client else None
    return service.request_otp(payload.phone, source_ip)


@router.post("/otp/verify", response_model=TokenPair)
def verify_otp(
    payload: OtpVerifyRequest,
    service: IdentityService = Depends(get_identity_service),
) -> TokenPair:
    return service.verify_otp(payload.phone, payload.code, payload.device_id)


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    service: IdentityService = Depends(get_identity_service),
) -> LoginResponse:
    return service.login_staff(payload)


@router.post("/mfa/verify", response_model=TokenPair)
def verify_mfa(
    payload: MfaVerifyRequest,
    service: IdentityService = Depends(get_identity_service),
) -> TokenPair:
    return service.verify_mfa(payload.challenge, payload.totp)


@router.post("/refresh", response_model=TokenPair)
def refresh(
    payload: RefreshRequest,
    service: IdentityService = Depends(get_identity_service),
) -> TokenPair:
    return service.refresh(payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    context: AuthContext = Depends(get_current_context),
    service: IdentityService = Depends(get_identity_service),
) -> None:
    service.logout(context)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(
    context: AuthContext = Depends(get_current_context),
    service: IdentityService = Depends(get_identity_service),
) -> None:
    service.logout_all(context)
