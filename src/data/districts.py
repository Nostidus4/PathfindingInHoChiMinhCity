"""Ranh giới 5 quận cũ và gán quận cho một tọa độ. Owner: P1."""

from __future__ import annotations


DISTRICTS: tuple[str, ...] = (
    "Quan 1",
    "Quan 3",
    "Quan 5",
    "Binh Thanh",
    "Phu Nhuan",
)


DISTRICT_POLYGONS: dict[str, list[tuple[float, float]]] = {
    "Quan 1": [
        (10.7890, 106.6870),
        (10.7890, 106.7140),
        (10.7650, 106.7140),
        (10.7650, 106.6870),
    ],
    "Quan 3": [
        (10.7950, 106.6700),
        (10.7950, 106.6900),
        (10.7650, 106.6900),
        (10.7650, 106.6700),
    ],
    "Quan 5": [
        (10.7700, 106.6500),
        (10.7700, 106.6750),
        (10.7450, 106.6750),
        (10.7450, 106.6500),
    ],
    "Binh Thanh": [
        (10.8250, 106.6900),
        (10.8250, 106.7350),
        (10.7850, 106.7350),
        (10.7850, 106.6900),
    ],
    "Phu Nhuan": [
        (10.8250, 106.6500),
        (10.8250, 106.6900),
        (10.7850, 106.6900),
        (10.7850, 106.6500),
    ],
}


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
            intersection_lat = (
                (lat_j - lat_i) * (lon - lon_i) / (lon_j - lon_i)
                + lat_i
            )

            if lat < intersection_lat:
                inside = not inside

        j = i

    return inside


def assign_district(lat: float, lon: float) -> str | None:
    """Trả tên quận chứa điểm, hoặc None nếu ngoài phạm vi."""

    for district in DISTRICTS:
        if point_in_polygon(lat, lon, DISTRICT_POLYGONS[district]):
            return district

    return None