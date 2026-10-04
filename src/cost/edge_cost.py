"""Chi phí đi qua một cạnh. Owner: P4.

edge_cost(segment, t, provider) -> giây (mode TIME, mode chính).
Mode DISTANCE trả length_m, dùng làm baseline phụ.
search/astar.py chỉ nhận hàm này dạng callable, không biết traffic là gì.
"""

from __future__ import annotations

from collections.abc import Callable

from src.cost.speed_model import effective_speed
from src.models import CostMode, RoadSegment, TrafficProvider

EdgeCostFn = Callable[[RoadSegment, float], float]


def edge_cost(
    segment: RoadSegment, t: float, provider: TrafficProvider, mode: CostMode = CostMode.TIME
) -> float:
    """Trả cost của ``segment`` tại thời điểm vào cạnh ``t``.

    - ``CostMode.TIME``: ``length_m / effective_speed`` -> giây.
    - ``CostMode.DISTANCE``: trả trực tiếp ``length_m`` -> mét và không cần
      truy vấn traffic provider.
    """
    if segment.length_m < 0:
        raise ValueError("RoadSegment.length_m phải không âm")

    try:
        cost_mode = CostMode(mode)
    except ValueError as exc:
        raise ValueError(f"CostMode không hợp lệ: {mode!r}") from exc

    if cost_mode is CostMode.DISTANCE:
        return float(segment.length_m)

    state = provider.get_traffic(segment.id, t)
    speed_ms = effective_speed(state, segment)
    return float(segment.length_m) / speed_ms


def make_edge_cost(provider: TrafficProvider, mode: CostMode = CostMode.TIME) -> EdgeCostFn:
    """Đóng gói provider vào closure (segment, t) -> cost để truyền cho astar()."""
    return lambda segment, t: edge_cost(segment, t, provider, mode)
