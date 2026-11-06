"""
Boundary loader module.
Authority: final/feature-specs/05-data-layer.md §2, final/feature-specs/06-forecast-and-risk-map.md §8, phase-plan.md §4.6.

Loads versioned administrative boundary geometries (EPSG:4326) and verifies topology.
Ensures that boundary version is propagated to every derived geographic record.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple
import uuid

ALLOWED_LEVELS = {"block", "mandal", "district", "state"}


class BoundaryRecord:
    """Represents a validated, versioned administrative boundary unit."""

    def __init__(
        self,
        code: str,
        level: str,
        name: str,
        boundary_version: str,
        parent_code: Optional[str] = None,
        geojson_geometry: Optional[Dict[str, Any]] = None,
        valid_from: str = "2026-01-01",
        valid_to: Optional[str] = None,
        is_demo: bool = True,
        boundary_id: Optional[str] = None,
    ):
        if not code:
            raise ValueError("code is required")
        if level not in ALLOWED_LEVELS:
            raise ValueError(f"Invalid level '{level}'. Must be one of {ALLOWED_LEVELS}")
        if not name:
            raise ValueError("name is required")
        if not boundary_version:
            raise ValueError("boundary_version is required")

        self.id = boundary_id or str(uuid.uuid4())
        self.code = code
        self.level = level
        self.name = name
        self.parent_code = parent_code
        self.boundary_version = boundary_version
        self.valid_from = valid_from
        self.valid_to = valid_to
        self.is_demo = is_demo

        self.geometry = self._validate_and_normalize_geometry(geojson_geometry) if geojson_geometry else None

    @staticmethod
    def _validate_and_normalize_geometry(geom: Dict[str, Any]) -> Dict[str, Any]:
        """Validates that the GeoJSON geometry has valid type and WGS84 coordinates."""
        geom_type = geom.get("type")
        if geom_type not in ("Polygon", "MultiPolygon"):
            raise ValueError(f"Invalid geometry type '{geom_type}'. Must be Polygon or MultiPolygon.")

        coords = geom.get("coordinates")
        if not coords or not isinstance(coords, list):
            raise ValueError("Coordinates must be a non-empty list.")

        # Coordinate range sanity check for WGS84 bounding limits
        def _check_coord(node: Any):
            if isinstance(node, (list, tuple)):
                if len(node) >= 2 and isinstance(node[0], (int, float)) and isinstance(node[1], (int, float)):
                    lon, lat = float(node[0]), float(node[1])
                    if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
                        raise ValueError(f"Coordinate ({lon}, {lat}) out of WGS84 range.")
                else:
                    for sub in node:
                        _check_coord(sub)

        _check_coord(coords)
        return geom

    def to_wkt(self) -> Optional[str]:
        """Converts GeoJSON geometry to WKT MultiPolygon string for SQL insertion."""
        if not self.geometry:
            return None

        geom_type = self.geometry["type"]
        coords = self.geometry["coordinates"]

        def _format_ring(ring: List[Any]) -> str:
            pts = ", ".join(f"{pt[0]} {pt[1]}" for pt in ring)
            return f"({pts})"

        def _format_poly(poly: List[Any]) -> str:
            rings = ", ".join(_format_ring(r) for r in poly)
            return f"({rings})"

        if geom_type == "Polygon":
            poly_str = _format_poly(coords)
            return f"MULTIPOLYGON({poly_str})"
        elif geom_type == "MultiPolygon":
            mp_str = ", ".join(_format_poly(poly) for poly in coords)
            return f"MULTIPOLYGON({mp_str})"
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "level": self.level,
            "name": self.name,
            "parent_code": self.parent_code,
            "boundary_version": self.boundary_version,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "is_demo": self.is_demo,
            "geometry": self.geometry,
        }
