"""Private image storage adapter.

The production target is Cloudinary with signed uploads and short-lived signed
delivery. No Cloudinary credentials or SDK are configured in this repository,
so the default local adapter implements the same contract for development and
tests. A production misconfiguration fails closed instead of serving public
files.
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.core.errors import ApiError
from app.core.security import TokenError, sign_payload, verify_signed_payload


def _root() -> Path:
    root = get_settings().storage_root
    root.mkdir(parents=True, exist_ok=True)
    return root


def _resolve(key: str) -> Path:
    root = _root().resolve()
    path = (root / key).resolve()
    if root not in path.parents and path != root:
        raise ApiError(400, "invalid_storage_key", "Invalid storage key")
    return path


def storage_key(observation_id: str, image_id: str) -> str:
    return f"observations/{observation_id}/{image_id}/original"


def write_bytes(key: str, data: bytes) -> None:
    if get_settings().storage_backend == "cloudinary":
        raise ApiError(
            503,
            "storage_not_configured",
            "Cloudinary is the production adapter but no credentials are configured",
        )
    path = _resolve(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def read_bytes(key: str) -> bytes:
    path = _resolve(key)
    if not path.exists():
        raise ApiError(404, "image_missing", "Image bytes are not available")
    return path.read_bytes()


def exists(key: str) -> bool:
    return _resolve(key).exists()


def upload_descriptor(*, observation_id: str, image_id: str, key: str) -> dict:
    settings = get_settings()
    token = sign_payload(
        "upload",
        {"observation_id": observation_id, "image_id": image_id, "key": key},
        settings.upload_url_ttl_seconds,
    )
    return {
        "upload_url": f"/v1/uploads/{token}",
        "method": "PUT",
        "expires_in_seconds": settings.upload_url_ttl_seconds,
        "storage_key": key,
        "note": "Development adapter. Cloudinary signed upload in production.",
    }


def download_descriptor(*, observation_id: str, image_id: str, key: str) -> dict:
    settings = get_settings()
    token = sign_payload(
        "download",
        {"observation_id": observation_id, "image_id": image_id, "key": key},
        settings.signed_url_ttl_seconds,
    )
    return {
        "download_url": f"/v1/uploads/download/{token}",
        "expires_in_seconds": settings.signed_url_ttl_seconds,
    }


def verify_upload_token(token: str) -> dict:
    try:
        return verify_signed_payload("upload", token)
    except TokenError as error:
        raise ApiError(401, error.code, "Upload token is invalid") from error


def verify_download_token(token: str) -> dict:
    try:
        return verify_signed_payload("download", token)
    except TokenError as error:
        raise ApiError(401, error.code, "Download token is invalid") from error
