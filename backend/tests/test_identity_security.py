"""Unit checks for the dependency-free cryptographic primitives (spec 03 §4)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from app.modules.identity.security import (
    AccessTokenCodec,
    TokenError,
    hash_otp,
    hash_password,
    mask_phone,
    totp_code,
    verify_password,
    verify_totp,
)

from tests.support_identity import FIXED_NOW, SECRET, TOTP_SECRET

PASSWORD = "synthetic password for primitives"


def test_password_hash_is_salted_and_verifiable() -> None:
    first = hash_password(PASSWORD)
    second = hash_password(PASSWORD)

    assert first != second
    assert PASSWORD not in first
    assert verify_password(PASSWORD, first)
    assert not verify_password("wrong password", first)
    assert not verify_password(PASSWORD, None)


def test_password_hash_rejects_a_malformed_record() -> None:
    assert not verify_password(PASSWORD, "not-a-hash")
    assert not verify_password(PASSWORD, "argon2id$not$ours")


def test_otp_hash_is_keyed_and_not_the_code() -> None:
    digest = hash_otp("123456", SECRET)

    assert "123456" not in digest
    assert digest != hash_otp("123456", "a different key")


def test_totp_verifies_current_and_adjacent_step_only() -> None:
    code = totp_code(TOTP_SECRET, FIXED_NOW)

    assert verify_totp(TOTP_SECRET, code, FIXED_NOW)
    assert verify_totp(TOTP_SECRET, code, FIXED_NOW + timedelta(seconds=20))
    assert not verify_totp(TOTP_SECRET, code, FIXED_NOW + timedelta(minutes=5))
    assert not verify_totp(None, code, FIXED_NOW)
    assert not verify_totp(TOTP_SECRET, "abcdef", FIXED_NOW)


def test_access_token_round_trip_and_type_check() -> None:
    codec = AccessTokenCodec(SECRET, timedelta(minutes=15))
    token = codec.issue({"typ": "access", "sub": "usr_1", "role": "farmer"}, FIXED_NOW)

    payload = codec.verify(token, FIXED_NOW, expected_type="access")

    assert payload["sub"] == "usr_1"
    assert payload["role"] == "farmer"
    with pytest.raises(TokenError):
        codec.verify(token, FIXED_NOW, expected_type="mfa")


def test_access_token_expiry_and_tampering_are_rejected() -> None:
    codec = AccessTokenCodec(SECRET, timedelta(minutes=15))
    token = codec.issue({"typ": "access", "sub": "usr_1"}, FIXED_NOW)

    with pytest.raises(TokenError) as expired:
        codec.verify(token, FIXED_NOW + timedelta(minutes=16), expected_type="access")
    assert expired.value.code == "token_expired"

    header, payload, signature = token.split(".")
    tampered = f"{header}.{payload}.{signature[:-1]}A"
    with pytest.raises(TokenError):
        codec.verify(tampered, FIXED_NOW, expected_type="access")


def test_short_token_secret_is_refused() -> None:
    with pytest.raises(ValueError):
        AccessTokenCodec("too-short", timedelta(minutes=1))


def test_phone_is_masked_for_audit_and_admin_listings() -> None:
    assert mask_phone("+10000000001") == "+10******001"
    assert mask_phone(None) is None
    assert mask_phone("1234") == "****"
