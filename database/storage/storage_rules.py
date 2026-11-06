"""
Validation and key generation logic for S3 Object Storage and Presigned URLs.
Enforces rules defined in 01-object-storage-and-presigned-urls.md and 05-data-layer.md §8.
"""

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Union
import uuid

# Allowed MIME types and corresponding extensions
ALLOWED_MIMES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

# Size boundaries (Bytes)
MIN_IMAGE_BYTES = 50 * 1024        # 50 KB
MAX_IMAGE_BYTES = 15 * 1024 * 1024  # 15 MB

# TTL Limits (Seconds)
DEFAULT_PRESIGNED_TTL_SECONDS = 300
MAX_PRESIGNED_TTL_SECONDS = 600

# Canonical Regex Patterns
OBSERVATION_ORIGINAL_PATTERN = re.compile(
    r"^observations/(?P<year>\d{4})/(?P<month>\d{2})/(?P<obs_id>[0-9a-f-]{36})/(?P<img_id>[0-9a-f-]{36})/original\.(?P<ext>jpg|png|webp)$"
)

OBSERVATION_DERIVED_PATTERN = re.compile(
    r"^observations/(?P<year>\d{4})/(?P<month>\d{2})/(?P<obs_id>[0-9a-f-]{36})/(?P<img_id>[0-9a-f-]{36})/derived/(?P<version>[a-zA-Z0-9._-]+)/(?P<filename>[a-zA-Z0-9._-]+)\.(?P<ext>jpg|png|webp)$"
)


def generate_observation_storage_key(
    observation_id: Union[str, uuid.UUID],
    image_id: Union[str, uuid.UUID],
    mime_type: str,
    timestamp: Optional[datetime] = None,
    is_original: bool = True,
    derived_name: Optional[str] = None,
    pipeline_version: Optional[str] = None,
) -> str:
    """Generates a canonical, opaque S3 storage key."""
    if mime_type not in ALLOWED_MIMES:
        raise ValueError(f"Unsupported MIME type: {mime_type}. Allowed: {list(ALLOWED_MIMES.keys())}")

    ext = ALLOWED_MIMES[mime_type]
    ts = timestamp or datetime.now(timezone.utc)
    yyyy = ts.strftime("%Y")
    mm = ts.strftime("%m")
    obs_id = str(observation_id)
    img_id = str(image_id)

    if is_original:
        return f"observations/{yyyy}/{mm}/{obs_id}/{img_id}/original.{ext}"

    if not derived_name or not pipeline_version:
        raise ValueError("derived_name and pipeline_version are required for derivative keys.")

    return f"observations/{yyyy}/{mm}/{obs_id}/{img_id}/derived/{pipeline_version}/{derived_name}.{ext}"


def validate_storage_key(key: str) -> Dict[str, str]:
    """Validates that a storage key conforms to canonical patterns.

    Raises ValueError on invalid format.
    """
    m_orig = OBSERVATION_ORIGINAL_PATTERN.match(key)
    if m_orig:
        res = m_orig.groupdict()
        res["kind"] = "original"
        return res

    m_der = OBSERVATION_DERIVED_PATTERN.match(key)
    if m_der:
        res = m_der.groupdict()
        res["kind"] = "derivative"
        return res

    if key.startswith("advisories/") or key.startswith("models/") or key.startswith("exports/"):
        return {"kind": "system", "path": key}

    raise ValueError(f"Invalid object storage key structure: {key}")


def validate_payload_limits(mime_type: str, byte_size: int) -> None:
    """Validates payload MIME and size bounds."""
    if mime_type not in ALLOWED_MIMES:
        raise ValueError(f"Invalid MIME type: {mime_type}. Allowed: {list(ALLOWED_MIMES.keys())}")
    if byte_size < MIN_IMAGE_BYTES:
        raise ValueError(f"File size {byte_size} bytes is below minimum {MIN_IMAGE_BYTES} bytes.")
    if byte_size > MAX_IMAGE_BYTES:
        raise ValueError(f"File size {byte_size} bytes exceeds maximum {MAX_IMAGE_BYTES} bytes.")


def validate_presigned_request(
    actor_role: str,
    actor_id: str,
    action: str,  # 'upload' or 'download'
    key: str,
    requested_ttl_seconds: int = DEFAULT_PRESIGNED_TTL_SECONDS,
    observation_owner_id: Optional[str] = None,
    assigned_geo_codes: Optional[List[str]] = None,
    observation_geo_code: Optional[str] = None,
) -> int:
    """Enforces authorization, HTTP action restrictions, and TTL limits.

    Returns the approved TTL in seconds.
    """
    # 1. TTL checks
    if requested_ttl_seconds <= 0:
        raise ValueError("TTL must be greater than zero.")
    if requested_ttl_seconds > MAX_PRESIGNED_TTL_SECONDS:
        raise ValueError(f"Requested TTL {requested_ttl_seconds}s exceeds maximum {MAX_PRESIGNED_TTL_SECONDS}s (Rule P1).")

    # 2. Key format
    key_meta = validate_storage_key(key)

    # 3. Action checks
    if action not in ("upload", "download"):
        raise ValueError(f"Action must be 'upload' or 'download', got: {action}")

    # Uploads are only permitted for original assets
    if action == "upload":
        if key_meta.get("kind") != "original":
            raise ValueError("Direct presigned upload is only permitted for original assets, not derivatives.")

        # Farmer can only upload to own observation
        if actor_role == "farmer":
            if not observation_owner_id or observation_owner_id != actor_id:
                raise PermissionError("Farmer can only request upload URLs for their own observations.")

        elif actor_role == "extension_worker":
            # Extension worker can upload on-behalf or for assigned area
            is_owner = observation_owner_id and observation_owner_id == actor_id
            in_area = assigned_geo_codes and observation_geo_code and (observation_geo_code in assigned_geo_codes)
            if not (is_owner or in_area):
                raise PermissionError("Extension worker can only upload for assigned areas or self-created observations.")

        elif actor_role in ("pathologist", "agronomist"):
            raise PermissionError(f"{actor_role} role is not permitted to upload raw field observations.")

    elif action == "download":
        if actor_role == "farmer":
            if not observation_owner_id or observation_owner_id != actor_id:
                raise PermissionError("Farmers may only access media for their own observations.")

        elif actor_role == "extension_worker":
            is_owner = observation_owner_id and observation_owner_id == actor_id
            in_area = assigned_geo_codes and observation_geo_code and (observation_geo_code in assigned_geo_codes)
            if not (is_owner or in_area):
                raise PermissionError("Extension worker cannot access media outside assigned area.")

        elif actor_role in ("pathologist", "agronomist", "admin"):
            # Authorized for verification / review workflow
            pass
        else:
            raise PermissionError(f"Unauthorized role: {actor_role}")

    return requested_ttl_seconds

