"""Chi phí đi qua một cạnh. Owner: P4.

edge_cost(segment, t, provider) -> giây (mode TIME, mode chính).
Mode DISTANCE trả length_m, dùng làm baseline phụ.
search/astar.py chỉ nhận hàm này dạng callable, không biết traffic là gì.
"""

from __future__ import annotations

from collections.abc import Callable

from src.models import CostMode, RoadSegment, TrafficProvider

EdgeCostFn = Callable[[RoadSegment, float], float]


def edge_cost(
    segment: RoadSegment, t: float, provider: TrafficProvider, mode: CostMode = CostMode.TIME
) -> float:
    """Thời gian (giây) đi hết segment nếu vào cạnh lúc t; hoặc mét nếu mode DISTANCE."""
    raise NotImplementedError("TODO(P4)")


def make_edge_cost(provider: TrafficProvider, mode: CostMode = CostMode.TIME) -> EdgeCostFn:
    """Đóng gói provider vào closure (segment, t) -> cost để truyền cho astar()."""
    return lambda segment, t: edge_cost(segment, t, provider, mode)
