"""Server-side image validation, quality metrics and local storage.

This is the development implementation of the media pipeline in
``final/feature-specs/02-reporting-and-capture.md``. It decodes the bytes with
Pillow, rejects anything that is not a real JPEG/PNG/WebP, measures a small set
of quality metrics and stores the original under ``settings.media_root``.

The metric extractor here is deliberately simple and versioned as
``demo-quality-0.1``. It is a real measurement of the uploaded pixels, not a
model, and it must be replaced by the versioned preprocessing recipe before a
pilot. ``plant_presence`` is a green-pixel heuristic, not a plant detector.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat, UnidentifiedImageError

from app.core.config import Settings
from app.modules.assessments.policy import QualityThresholds
from app.modules.assessments.quality import ImageMetrics, QualityOutcome, evaluate_quality

ALLOWED_CONTENT_TYPES: dict[str, tuple[str, str]] = {
    "image/jpeg": ("JPEG", "jpg"),
    "image/png": ("PNG", "png"),
    "image/webp": ("WEBP", "webp"),
}

# Demo thresholds. They are intentionally permissive: the point is to exercise
# the abstention path, not to claim a validated operating point (D8 is open).
DEMO_QUALITY_THRESHOLDS = QualityThresholds(
    version="demo-quality-0.1",
    min_width=256,
    min_height=256,
    min_laplacian_variance=8.0,
    min_mean_luma=20.0,
    max_mean_luma=240.0,
    max_clipped_fraction=0.5,
    min_plant_presence=0.005,
)

_METRIC_MAX_SIDE = 512


class MediaValidationError(Exception):
    """A client-safe validation failure with a stable machine code."""

    def __init__(self, code: str, message: str, *, status: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


@dataclass(frozen=True)
class InspectedImage:
    width: int
    height: int
    content_hash: str
    metrics: ImageMetrics
    quality: QualityOutcome


def _green_fraction(image: Image.Image) -> float:
    """Fraction of sampled pixels that look green (HSV heuristic)."""

    sample = image.copy()
    sample.thumbnail((_METRIC_MAX_SIDE, _METRIC_MAX_SIDE))
    hsv = sample.convert("HSV")
    total = 0
    green = 0
    for hue, saturation, value in hsv.getdata():
        total += 1
        if 55 <= hue <= 180 and saturation >= 50 and value >= 40:
            green += 1
    return green / total if total else 0.0


def inspect_image(data: bytes, content_type: str) -> InspectedImage:
    """Validate bytes and measure quality metrics.

    Raises ``MediaValidationError`` for an unsupported type, corrupt bytes or an
    image whose declared type does not match its decoded format.
    """

    expected = ALLOWED_CONTENT_TYPES.get(content_type)
    if expected is None:
        raise MediaValidationError(
            "unsupported_media_type",
            "Only JPEG, PNG and WebP images are accepted.",
            status=415,
        )
    expected_format, _ = expected

    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise MediaValidationError("invalid_image", "The file is not a readable image.") from error

    try:
        with Image.open(io.BytesIO(data)) as opened:
            if (opened.format or "").upper() != expected_format:
                raise MediaValidationError(
                    "invalid_image",
                    "The file contents do not match the declared image type.",
                )
            image = opened.convert("RGB")
    except MediaValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise MediaValidationError("invalid_image", "The file is not a readable image.") from error

    width, height = image.size
    if width < 1 or height < 1:
        raise MediaValidationError("invalid_image", "The image has no pixels.")

    sample = image.copy()
    sample.thumbnail((_METRIC_MAX_SIDE, _METRIC_MAX_SIDE))
    gray = sample.convert("L")
    stat = ImageStat.Stat(gray)
    mean_luma = float(stat.mean[0])

    histogram = gray.histogram()
    total = sum(histogram) or 1
    clipped = (histogram[0] + histogram[1] + histogram[254] + histogram[255]) / total

    edges = gray.filter(
        ImageFilter.Kernel((3, 3), (0, 1, 0, 1, -4, 1, 0, 1, 0), scale=1, offset=128)
    )
    laplacian_variance = float(ImageStat.Stat(edges).var[0])

    metrics = ImageMetrics(
        width=width,
        height=height,
        laplacian_variance=laplacian_variance,
        mean_luma=mean_luma,
        clipped_fraction=min(1.0, max(0.0, clipped)),
        plant_presence=min(1.0, max(0.0, _green_fraction(image))),
    )
    quality = evaluate_quality(metrics, DEMO_QUALITY_THRESHOLDS)

    return InspectedImage(
        width=width,
        height=height,
        content_hash=hashlib.sha256(data).hexdigest(),
        metrics=metrics,
        quality=quality,
    )


def extension_for(content_type: str) -> str:
    return ALLOWED_CONTENT_TYPES[content_type][1]


def store_image(
    settings: Settings, owner_id: str, upload_id: str, content_type: str, data: bytes
) -> str:
    """Write the original and return a path relative to ``media_root``."""

    relative = f"{owner_id}/{upload_id}.{extension_for(content_type)}"
    destination = Path(settings.media_root) / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return relative


def resolve_stored_path(settings: Settings, storage_path: str) -> Path:
    """Resolve a stored path, refusing traversal outside ``media_root``."""

    root = Path(settings.media_root).resolve()
    candidate = (root / storage_path).resolve()
    if root not in candidate.parents and candidate != root:
        raise MediaValidationError("upload_not_found", "Upload not found.", status=404)
    return candidate
