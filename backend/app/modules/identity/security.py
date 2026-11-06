"""Cryptographic primitives for the identity module.

Deliberately dependency-free: password hashing uses stdlib ``scrypt``, compact
tokens use an HS256 JWT we sign and verify ourselves, and TOTP follows RFC 6238.
The feature spec names Argon2id; switching to it needs a reviewed dependency, so
this scaffold records the deviation rather than silently changing the contract.

Nothing in this module logs, prints or returns a secret. Callers decide what is
exposed and the API layer keeps it to the one-time MFA provisioning response.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import struct
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

_PASSWORD_SCHEME = "scrypt"
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_BYTES = 16
_KEY_BYTES = 32


class TokenError(Exception):
    """A compact token is missing, malformed, expired or signed with the wrong key."""

    def __init__(self, code: str = "token_invalid", detail: str = "Token is invalid.") -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class ScryptParameters:
    n: int = _SCRYPT_N
    r: int = _SCRYPT_R
    p: int = _SCRYPT_P
    salt_bytes: int = _SALT_BYTES
    key_bytes: int = _KEY_BYTES


DEFAULT_SCRYPT = ScryptParameters()


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def hash_password(password: str, parameters: ScryptParameters = DEFAULT_SCRYPT) -> str:
    """Return ``scrypt$n$r$p$salt$key`` with a fresh random salt."""

    salt = secrets.token_bytes(parameters.salt_bytes)
    key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=parameters.n,
        r=parameters.r,
        p=parameters.p,
        dklen=parameters.key_bytes,
    )
    return "$".join(
        (
            _PASSWORD_SCHEME,
            str(parameters.n),
            str(parameters.r),
            str(parameters.p),
            _b64e(salt),
            _b64e(key),
        )
    )


def verify_password(
    password: str,
    stored: str | None,
    parameters: ScryptParameters = DEFAULT_SCRYPT,
) -> bool:
    if not stored:
        return False
    try:
        scheme, n, r, p, salt_b64, key_b64 = stored.split("$")
    except ValueError:
        return False
    if scheme != _PASSWORD_SCHEME:
        return False
    try:
        salt = _b64d(salt_b64)
        expected = _b64d(key_b64)
        candidate = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, expected)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(code: str, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        f"otp:{code}".encode(),
        hashlib.sha256,
    ).hexdigest()


def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def _totp_counter(at: datetime, step_seconds: int) -> int:
    return int(at.timestamp()) // step_seconds


def totp_code(secret: str, at: datetime, *, step_seconds: int = 30, digits: int = 6) -> str:
    padded = secret + "=" * (-len(secret) % 8)
    key = base64.b32decode(padded)
    counter = _totp_counter(at, step_seconds)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(binary % (10**digits)).zfill(digits)


def verify_totp(
    secret: str | None,
    code: str,
    at: datetime,
    *,
    step_seconds: int = 30,
    digits: int = 6,
    window: int = 1,
) -> bool:
    if not secret or len(code) != digits or not code.isdigit():
        return False
    for offset in range(-window, window + 1):
        moment = at + timedelta(seconds=offset * step_seconds)
        if hmac.compare_digest(totp_code(secret, moment, step_seconds=step_seconds), code):
            return True
    return False


def otpauth_uri(secret: str, email: str, issuer: str = "PS-03") -> str:
    label = f"{issuer}:{email}"
    return (
        f"otpauth://totp/{label}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"
    )


def mask_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    if len(phone) <= 4:
        return "*" * len(phone)
    return f"{phone[:3]}{'*' * (len(phone) - 6)}{phone[-3:]}"


def utcnow() -> datetime:
    return datetime.now(UTC)


class AccessTokenCodec:
    """Small HS256 JWT implementation with an explicit type and expiry check."""

    def __init__(self, secret: str, ttl: timedelta) -> None:
        if len(secret) < 16:
            raise ValueError("Token secret must contain at least 16 characters.")
        self._secret = secret.encode("utf-8")
        self.ttl = ttl

    def _sign(self, signing_input: bytes) -> bytes:
        return hmac.new(self._secret, signing_input, hashlib.sha256).digest()

    def issue(self, claims: dict[str, object], now: datetime) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        payload = dict(claims)
        payload["iat"] = int(now.timestamp())
        payload["exp"] = int((now + self.ttl).timestamp())
        header_b64 = _b64e(json.dumps(header, separators=(",", ":"), sort_keys=True).encode())
        payload_b64 = _b64e(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        return f"{header_b64}.{payload_b64}.{_b64e(self._sign(signing_input))}"

    def verify(self, token: str, now: datetime, *, expected_type: str) -> dict[str, object]:
        try:
            header_b64, payload_b64, signature_b64 = token.split(".")
            header = json.loads(_b64d(header_b64))
            payload = json.loads(_b64d(payload_b64))
            signature = _b64d(signature_b64)
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            raise TokenError(detail="Token is malformed.") from error

        if header.get("alg") != "HS256" or header.get("typ") != "JWT":
            raise TokenError(detail="Unsupported token header.")
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        if not hmac.compare_digest(self._sign(signing_input), signature):
            raise TokenError(detail="Token signature is invalid.")
        if payload.get("typ") != expected_type:
            raise TokenError(detail="Wrong token type.")
        try:
            expires_at = int(payload["exp"])
        except (KeyError, TypeError, ValueError) as error:
            raise TokenError(detail="Token has no expiry.") from error
        if expires_at <= int(now.timestamp()):
            raise TokenError(code="token_expired", detail="Token has expired.")
        return payload


def monotonic_seconds() -> int:
    """Only used by callers that need a coarse TTL without a wall clock."""

    return int(time.monotonic())
