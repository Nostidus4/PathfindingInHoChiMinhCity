"""Kiểm tra chất lượng tập POI. Owner: P1."""

from __future__ import annotations

import math
from collections import Counter

from src.data.districts import assign_district
from src.models import POI


def _distance_m(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Khoảng cách Haversine, đơn vị mét."""

    radius = 6_371_000

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * radius * math.asin(math.sqrt(a))


def validate_pois(
    pois: list[POI],
    min_total: int = 100,
    min_per_district: int = 20,
    min_sep_m: float = 30.0,
) -> list[str]:
    """Trả list lỗi; list rỗng nghĩa là dữ liệu hợp lệ."""

    errors: list[str] = []

    if len(pois) < min_total:
        errors.append(
            f"Chỉ có {len(pois)} POI, cần ít nhất {min_total}."
        )

    district_counts = Counter(poi.district for poi in pois)

    for district in (
        "Quan 1",
        "Quan 3",
        "Quan 5",
        "Binh Thanh",
        "Phu Nhuan",
    ):
        count = district_counts.get(district, 0)

        if count < min_per_district:
            errors.append(
                f"{district}: {count} POI, cần ít nhất {min_per_district}."
            )

    ids = [poi.id for poi in pois]

    if len(ids) != len(set(ids)):
        errors.append("Có POI bị trùng id.")

    for i in range(len(pois)):
        for j in range(i + 1, len(pois)):
            distance = _distance_m(
                pois[i].lat,
                pois[i].lon,
                pois[j].lat,
                pois[j].lon,
            )

            if distance < min_sep_m:
                errors.append(
                    f"POI quá gần nhau: {pois[i].id} và {pois[j].id} "
                    f"({distance:.1f} m)."
                )
                break

    for poi in pois:
        district = assign_district(poi.lat, poi.lon)

        if district is None:
            errors.append(
                f"POI {poi.id} nằm ngoài 5 quận: "
                f"({poi.lat}, {poi.lon})."
            )

    return errors