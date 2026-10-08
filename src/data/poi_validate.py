"""Kiểm tra chất lượng tập POI. Owner: P1.

Trả danh sách lỗi, rỗng = hợp lệ:
- Tổng >= min_total POI, mỗi quận >= min_per_district POI.
- Không trùng id, không có hai POI gần nhau hơn min_sep_m.
- Toạ độ hợp lệ, POI nằm trong 5 quận và nhãn district khớp với polygon của quận đó.
- kind thuộc landmark / intersection / junction, có tên.
"""

from __future__ import annotations

import math
from collections import Counter

from src.data.districts import DISTRICTS, assign_district
from src.geo import haversine_m
from src.models import POI

VALID_KINDS = frozenset({"landmark", "intersection", "junction"})


def validate_pois(
    pois: list[POI],
    min_total: int = 100,
    min_per_district: int = 20,
    min_sep_m: float = 30.0,
) -> list[str]:
    """Trả list lỗi; list rỗng nghĩa là dữ liệu hợp lệ."""

    errors: list[str] = []

    if len(pois) < min_total:
        errors.append(f"Chỉ có {len(pois)} POI, cần ít nhất {min_total}.")

    district_counts = Counter(poi.district for poi in pois)

    for district in DISTRICTS:
        count = district_counts.get(district, 0)

        if count < min_per_district:
            errors.append(f"{district}: {count} POI, cần ít nhất {min_per_district}.")

    unknown = sorted(set(district_counts) - set(DISTRICTS))
    if unknown:
        errors.append(f"Tên quận không hợp lệ: {', '.join(unknown)}.")

    duplicated = sorted(i for i, n in Counter(poi.id for poi in pois).items() if n > 1)
    if duplicated:
        errors.append(f"Có POI bị trùng id: {', '.join(duplicated)}.")

    for i in range(len(pois)):
        for j in range(i + 1, len(pois)):
            distance = haversine_m(pois[i].lat, pois[i].lon, pois[j].lat, pois[j].lon)

            if distance < min_sep_m:
                errors.append(f"POI quá gần nhau: {pois[i].id} và {pois[j].id} ({distance:.1f} m).")
                break

    for poi in pois:
        if not (math.isfinite(poi.lat) and math.isfinite(poi.lon)):
            errors.append(f"POI {poi.id} có toạ độ không hợp lệ: ({poi.lat}, {poi.lon}).")
            continue

        district = assign_district(poi.lat, poi.lon)

        if district is None:
            errors.append(f"POI {poi.id} nằm ngoài 5 quận: ({poi.lat}, {poi.lon}).")
        elif district != poi.district:
            errors.append(f"POI {poi.id} ghi quận {poi.district!r} nhưng nằm trong {district!r}.")

        if poi.kind not in VALID_KINDS:
            errors.append(f"POI {poi.id} có kind không hợp lệ: {poi.kind!r}.")

        if not poi.name.strip():
            errors.append(f"POI {poi.id} không có tên.")

    return errors
