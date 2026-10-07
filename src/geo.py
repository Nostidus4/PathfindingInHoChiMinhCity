"""Hàm địa lý thuần Python (KHÔNG dùng shapely để core không phụ thuộc thư viện nặng).

Dùng cho: heuristic (khoảng cách chim bay), graph/checks.py (length >= haversine),
data/ (snap POI, lọc trùng).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

EARTH_RADIUS_M = 6_371_008.8


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Khoảng cách đường tròn lớn giữa 2 điểm (mét)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def polyline_length_m(points: Sequence[tuple[float, float]]) -> float:
    """Tổng chiều dài polyline [(lat, lon), ...] (mét)."""
    return sum(
        haversine_m(a[0], a[1], b[0], b[1]) for a, b in zip(points, points[1:], strict=False)
    )
