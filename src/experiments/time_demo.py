"""Demo phụ thuộc thời gian: cùng A/B, đổi giờ xuất phát. Owner: P6.

Cho thấy cost và/hoặc route thay đổi theo giờ (ví dụ 05:00 vs 07:30 vs 17:30).
Output: bảng CSV + bản đồ các route chồng lên nhau.
"""

from __future__ import annotations

from collections.abc import Sequence

from src.models import NodeId


def time_dependence_demo(
    pathfinder, start: NodeId, goal: NodeId, times: Sequence[float], mode: str = "dynamic_ub"
) -> list[dict]:
    raise NotImplementedError("TODO(P6)")
