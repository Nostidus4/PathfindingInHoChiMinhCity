"""Ranh giới 5 quận cũ và gán quận cho một tọa độ. Owner: P1.

Polygon là ranh giới thật lấy từ OSM (relation boundary=historic, xem
src/data/district_polygons.py và scripts/extract_districts.py), không vẽ tay.
Gán quận bằng ray casting thuần Python, không cần shapely.
"""

from __future__ import annotations

import math

from src.data.district_polygons import DISTRICT_POLYGONS

DISTRICTS: tuple[str, ...] = (
    "Quan 1",
    "Quan 3",
    "Quan 5",
    "Binh Thanh",
    "Phu Nhuan",
)

__all__ = [
    "DISTRICTS",
    "DISTRICT_POLYGONS",
    "assign_district",
    "bounding_box",
    "distance_to_border_m",
    "point_in_polygon",
]


def _bbox(polygon: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    lats = [p[0] for p in polygon]
    lons = [p[1] for p in polygon]
    return min(lats), min(lons), max(lats), max(lons)


# Khung bao của từng quận để loại nhanh điểm ở xa trước khi ray casting
_BBOXES = {d: _bbox(poly) for d, poly in DISTRICT_POLYGONS.items()}


def point_in_polygon(
    lat: float,
    lon: float,
    polygon: list[tuple[float, float]],
) -> bool:
    """Ray casting: kiểm tra điểm có nằm trong polygon hay không."""

    inside = False
    j = len(polygon) - 1

    for i in range(len(polygon)):
        lat_i, lon_i = polygon[i]
        lat_j, lon_j = polygon[j]

        if (lon_i > lon) != (lon_j > lon):
            intersection_lat = (lat_j - lat_i) * (lon - lon_i) / (lon_j - lon_i) + lat_i

            if lat < intersection_lat:
                inside = not inside

        j = i

    return inside


def assign_district(lat: float, lon: float) -> str | None:
    """Trả tên quận chứa điểm, hoặc None nếu ngoài phạm vi."""

    for district in DISTRICTS:
        south, west, north, east = _BBOXES[district]
        if not (south <= lat <= north and west <= lon <= east):
            continue
        if point_in_polygon(lat, lon, DISTRICT_POLYGONS[district]):
            return district

    return None


def distance_to_border_m(lat: float, lon: float, district: str) -> float:
    """Khoảng cách (mét) từ điểm tới ranh giới gần nhất của quận (xấp xỉ phẳng cục bộ)."""

    polygon = DISTRICT_POLYGONS[district]
    kx = 111_320 * math.cos(math.radians(lat))
    ky = 110_540
    best = math.inf
    for (a_lat, a_lon), (b_lat, b_lon) in zip(polygon, polygon[1:] + polygon[:1], strict=True):
        ax, ay = (a_lon - lon) * kx, (a_lat - lat) * ky
        dx, dy = (b_lon - a_lon) * kx, (b_lat - a_lat) * ky
        seg2 = dx * dx + dy * dy
        t = 0.0 if seg2 == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / seg2))
        best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best


def bounding_box(margin_m: float = 0.0) -> tuple[float, float, float, float]:
    """Khung bao cả 5 quận, nới thêm margin_m mét mỗi phía.

    Trả (west, south, east, north), đúng thứ tự tham số bbox của osmnx 2.x.
    """

    south = min(b[0] for b in _BBOXES.values())
    west = min(b[1] for b in _BBOXES.values())
    north = max(b[2] for b in _BBOXES.values())
    east = max(b[3] for b in _BBOXES.values())
    dlat = margin_m / 111_000
    dlon = margin_m / (111_000 * math.cos(math.radians((south + north) / 2)))
    return west - dlon, south - dlat, east + dlon, north + dlat
