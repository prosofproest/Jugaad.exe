"""Read-only GIS map layers (spec 06 §7–§8).

One route per layer, never a merged risk route. The route is mounted even when
no repository is configured so a client receives an explicit
``map_not_configured`` problem instead of empty geometry that could be mistaken
for "no disease".
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Path, Query

from app.core.errors import ApiError
from app.modules.identity.dependencies import get_current_context
from app.modules.identity.service import AuthContext
from app.modules.mapping.models import (
    BBox,
    LayerName,
    MapLayerResponse,
    MapQuery,
    MapUnavailable,
)
from app.modules.mapping.service import MapService

router = APIRouter(prefix="/map/layers", tags=["map"])

_service: MapService | None = None


def get_map_service() -> MapService | None:
    return _service


def set_map_service(service: MapService | None) -> None:
    """Test/DI hook. ``None`` means this deployment has no map repository."""

    global _service
    _service = service


def _parse_bbox(value: str | None) -> BBox | None:
    if value is None:
        return None
    try:
        return BBox.parse(value)
    except ValueError as error:
        raise ApiError(
            code="invalid_bbox",
            title="Invalid bounding box",
            status=400,
            detail=str(error),
        ) from error


@router.get("/{layer}", response_model=MapLayerResponse)
def get_layer(
    layer: LayerName = Path(...),
    crop: str | None = Query(default=None, min_length=1, max_length=80),
    target: str | None = Query(default=None, min_length=1, max_length=80),
    on_date: date | None = Query(default=None, alias="date"),
    bbox: str | None = Query(default=None, max_length=200),
    _context: AuthContext = Depends(get_current_context),
) -> MapLayerResponse:
    service = get_map_service()
    if service is None:
        raise ApiError(
            code="map_not_configured",
            title="Map not configured",
            status=503,
            detail=(
                "No persisted geometry, boundary version or suppression policy is "
                "configured for this deployment."
            ),
            retryable=False,
        )
    query = MapQuery(
        crop=crop,
        target=target,
        on_date=on_date,
        bbox=_parse_bbox(bbox),
    )
    try:
        return service.layer(layer, query)
    except MapUnavailable as error:
        status = 400 if error.code in {"scope_required", "invalid_geometry"} else 503
        raise ApiError(
            code=error.code,
            title="Map layer unavailable",
            status=status,
            detail=error.code.replace("_", " "),
            retryable=False,
        ) from error
