"""Security primitives: password hashing, tokens, signed URLs and TOTP.

Secrets and hashes never leave this module as plain values. Logging helpers in
``core.logging`` receive identifiers only.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings

_password_hasher = PasswordHasher()

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
MFA_TOKEN_TYPE = "mfa"


class TokenError(Exception):
    """Raised when a token is missing, malformed, expired or of the wrong type."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:  # malformed hash is a failed verification, never a 500
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _password_hasher.check_needs_rehash(password_hash)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_token(
    *,
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    payload: dict[str, Any] = {
        "sub": subject,
        "typ": token_type,
        "iat": int(_now().timestamp()),
        "exp": int((_now() + expires_delta).timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, *, expected_type: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError as error:
        raise TokenError("token_expired", "Token has expired") from error
    except jwt.PyJWTError as error:
        raise TokenError("invalid_token", "Token is invalid") from error
    if payload.get("typ") != expected_type:
        raise TokenError("invalid_token", "Token type is invalid")
    return payload


def create_access_token(*, user_id: str, role: str, session_id: str, token_version: int) -> str:
    return create_token(
        subject=user_id,
        token_type=ACCESS_TOKEN_TYPE,
        expires_delta=timedelta(minutes=get_settings().access_token_minutes),
        extra={
            "role": role,
            "session_id": session_id,
            "token_version": token_version,
        },
    )


def create_mfa_challenge(*, user_id: str) -> str:
    return create_token(
        subject=user_id,
        token_type=MFA_TOKEN_TYPE,
        expires_delta=timedelta(minutes=get_settings().mfa_challenge_minutes),
        extra={"purpose": "mfa"},
    )


def decode_access_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type=ACCESS_TOKEN_TYPE)


def decode_mfa_challenge(token: str) -> dict[str, Any]:
    payload = decode_token(token, expected_type=MFA_TOKEN_TYPE)
    if payload.get("purpose") != "mfa":
        raise TokenError("invalid_token", "Not an MFA challenge")
    return payload


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_otp(phone_e164: str, code: str) -> str:
    """OTP hashes are salted by the phone number so a dump is not sprayable."""
    return hmac.new(
        get_settings().jwt_secret.encode("utf-8"),
        f"{phone_e164}:{code}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_otp_hash(phone_e164: str, code: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_otp(phone_e164, code), stored_hash)


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def sign_payload(purpose: str, payload: dict[str, Any], ttl_seconds: int) -> str:
    """Create a compact HMAC-signed token for upload/download descriptors."""
    import json

    body = {
        **payload,
        "purpose": purpose,
        "exp": int((_now() + timedelta(seconds=ttl_seconds)).timestamp()),
    }
    raw = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = hmac.new(
        get_settings().jwt_secret.encode("utf-8"), raw, hashlib.sha256
    ).digest()
    return f"{_b64url(raw)}.{_b64url(signature)}"


def verify_signed_payload(purpose: str, token: str) -> dict[str, Any]:
    import json

    try:
        raw_part, signature_part = token.split(".", 1)
        raw = _b64url_decode(raw_part)
        expected = hmac.new(
            get_settings().jwt_secret.encode("utf-8"), raw, hashlib.sha256
        ).digest()
        if not hmac.compare_digest(expected, _b64url_decode(signature_part)):
            raise TokenError("invalid_signature", "Signature does not match")
        body = json.loads(raw.decode("utf-8"))
    except TokenError:
        raise
    except Exception as error:
        raise TokenError("invalid_token", "Signed token is malformed") from error
    if body.get("purpose") != purpose:
        raise TokenError("invalid_token", "Signed token purpose is invalid")
    if int(body.get("exp", 0)) < int(_now().timestamp()):
        raise TokenError("token_expired", "Signed token has expired")
    return body


def new_totp_secret() -> str:
    return pyotp.random_base32()


def totp_uri(secret: str, account: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=account, issuer_name="PS-03")


def verify_totp(secret: str | None, code: str) -> bool:
    if not secret:
        return False
    return pyotp.TOTP(secret).verify(code, valid_window=1)
