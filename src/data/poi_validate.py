"""Kiểm tra chất lượng tập POI. Owner: P1.

Nhiệm vụ (trả danh sách lỗi, rỗng = hợp lệ):
- Tổng >= 100 POI, mỗi quận >= 20 POI.
- Không trùng id, không trùng toạ độ (quá gần < min_sep_m).
- Không POI nào nằm ngoài ranh giới 5 quận.
"""

from __future__ import annotations

from src.models import POI


def validate_pois(
    pois: list[POI], min_total: int = 100, min_per_district: int = 20, min_sep_m: float = 30.0
) -> list[str]:
    """Trả list thông báo lỗi; list rỗng nghĩa là đạt yêu cầu."""
    raise NotImplementedError("TODO(P1)")
