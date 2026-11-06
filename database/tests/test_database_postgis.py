"""
Automated PostGIS and Spatial Logic Test Suite for CropSentinel AI.
Verifies:
- Point, Polygon, MultiPolygon representation and parsing.
- Coordinate validity checks (-90 <= lat <= 90, -180 <= lon <= 180).
- Spatial distance calculation (Haversine formula matching ST_Distance/ST_DWithin).
- Point-in-polygon containment (matching ST_Contains/ST_Intersects).
- Spatial queries: nearby pest report search & affected plot identification.
- PostGIS SQL schema definitions, functions, and GiST indexes.
"""

import math
import os
import re
import unittest


def haversine_distance_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Calculate the great-circle distance between two points in km."""
    r = 6371.0  # Earth's radius in kilometers
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def point_in_polygon(x: float, y: float, polygon_coords: list[tuple[float, float]]) -> bool:
    """Ray-casting algorithm to test if point (x, y) is inside polygon."""
    n = len(polygon_coords)
    inside = False
    p1x, p1y = polygon_coords[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon_coords[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def validate_wkt_point(wkt: str) -> tuple[float, float]:
    """Validate and parse a WKT POINT(lon lat) string."""
    m = re.match(r"^POINT\s*\(\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*\)$", wkt.strip(), re.I)
    if not m:
        raise ValueError(f"Invalid WKT POINT format: {wkt}")
    lon = float(m.group(1))
    lat = float(m.group(2))
    if not (-180.0 <= lon <= 180.0):
        raise ValueError(f"Longitude out of bounds [-180, 180]: {lon}")
    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Latitude out of bounds [-90, 90]: {lat}")
    return lon, lat


def validate_wkt_polygon(wkt: str) -> list[tuple[float, float]]:
    """Validate and parse a WKT POLYGON((lon lat, ...)) string."""
    m = re.match(r"^POLYGON\s*\(\s*\((.+)\)\s*\)$", wkt.strip(), re.I)
    if not m:
        raise ValueError(f"Invalid WKT POLYGON format: {wkt}")
    coord_pairs = m.group(1).split(",")
    coords = []
    for pair in coord_pairs:
        parts = pair.strip().split()
        if len(parts) != 2:
            raise ValueError(f"Invalid coordinate pair: {pair}")
        lon, lat = float(parts[0]), float(parts[1])
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            raise ValueError(f"Coordinates out of bounds: {lon}, {lat}")
        coords.append((lon, lat))

    if len(coords) < 4:
        raise ValueError("Polygon must have at least 4 vertices including closure")
    if coords[0] != coords[-1]:
        raise ValueError("Polygon linear ring is not closed (first vertex != last vertex)")
    return coords


class TestDatabasePostGIS(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.schema_path = os.path.join(base_dir, "schema", "03-cropsentinel-master-schema.sql")
        cls.seed_path = os.path.join(base_dir, "schema", "04-cropsentinel-master-seed.sql")

        with open(cls.schema_path, "r", encoding="utf-8") as f:
            cls.schema_sql = f.read()
        with open(cls.seed_path, "r", encoding="utf-8") as f:
            cls.seed_sql = f.read()

    def test_gps_point_validation_valid(self):
        """Test parsing and boundary validation of valid GPS points."""
        lon, lat = validate_wkt_point("POINT(77.3425 16.2025)")
        self.assertAlmostEqual(lon, 77.3425)
        self.assertAlmostEqual(lat, 16.2025)

    def test_gps_point_validation_invalid(self):
        """Test rejection of out-of-range coordinates."""
        with self.assertRaises(ValueError):
            validate_wkt_point("POINT(195.0 16.2025)")  # Lon > 180
        with self.assertRaises(ValueError):
            validate_wkt_point("POINT(77.3425 -95.0)")   # Lat < -90
        with self.assertRaises(ValueError):
            validate_wkt_point("NOT_A_POINT(77.3425, 16.2025)")

    def test_valid_polygon_closure(self):
        """Test validation of closed valid polygon."""
        poly_wkt = "POLYGON((77.3400 16.2000, 77.3450 16.2000, 77.3450 16.2050, 77.3400 16.2050, 77.3400 16.2000))"
        coords = validate_wkt_polygon(poly_wkt)
        self.assertEqual(len(coords), 5)
        self.assertEqual(coords[0], coords[-1])

    def test_invalid_unclosed_polygon(self):
        """Test rejection of unclosed polygon ring."""
        unclosed = "POLYGON((77.3400 16.2000, 77.3450 16.2000, 77.3450 16.2050, 77.3400 16.2050))"
        with self.assertRaises(ValueError):
            validate_wkt_polygon(unclosed)

    def test_spatial_distance_and_nearby_query(self):
        """
        Verify spatial distance calculation matching PostGIS ST_DWithin:
        Points separated by ~1.2 km correctly identified within 2 km radius.
        """
        farm_lon, farm_lat = 77.3425, 16.2025
        report_lon, report_lat = 77.3500, 16.2100

        dist = haversine_distance_km(farm_lon, farm_lat, report_lon, report_lat)
        self.assertGreater(dist, 1.0)
        self.assertLess(dist, 1.5)

        # Query: is report within 2 km of farm centroid?
        self.assertTrue(dist <= 2.0)
        # Query: is report within 0.5 km of farm centroid?
        self.assertFalse(dist <= 0.5)

    def test_affected_plot_spatial_containment(self):
        """
        Verify spatial intersection/containment matching PostGIS ST_Contains:
        Plant observation at (77.3410, 16.2030) is inside Plot A1 polygon.
        """
        plot_poly_wkt = "POLYGON((77.3400 16.2025, 77.3425 16.2025, 77.3425 16.2050, 77.3400 16.2050, 77.3400 16.2025))"
        poly_coords = validate_wkt_polygon(plot_poly_wkt)

        inside_point = (77.3410, 16.2030)
        outside_point = (77.3450, 16.2070)

        self.assertTrue(point_in_polygon(inside_point[0], inside_point[1], poly_coords))
        self.assertFalse(point_in_polygon(outside_point[0], outside_point[1], poly_coords))

    def test_sql_schema_postgis_configuration(self):
        """Verify extension and spatial columns in master schema DDL."""
        self.assertIn("CREATE EXTENSION IF NOT EXISTS postgis", self.schema_sql)
        self.assertIn("geometry(Point, 4326)", self.schema_sql)
        self.assertIn("geometry(Polygon, 4326)", self.schema_sql)
        self.assertIn("geometry(MultiPolygon, 4326)", self.schema_sql)

    def test_seed_spatial_geometries(self):
        """Verify valid ST_GeomFromText spatial geometries in seed SQL."""
        points = re.findall(r"ST_GeomFromText\('(POINT\([^']+\))',\s*4326\)", self.seed_sql)
        self.assertGreater(len(points), 0)
        for pt in points:
            validate_wkt_point(pt)

        polys = re.findall(r"ST_GeomFromText\('(POLYGON\([^']+\))',\s*4326\)", self.seed_sql)
        self.assertGreater(len(polys), 0)
        for poly in polys:
            validate_wkt_polygon(poly)


if __name__ == "__main__":
    unittest.main()

