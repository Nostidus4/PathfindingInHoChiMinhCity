"""Heuristic dynamic_weighted: h = w * haversine(node, goal) / v_mean(t). Owner: P4.

KHÔNG đảm bảo admissible (w > 1, dùng v_mean thay vì chặn trên) -> nhanh hơn
nhưng có thể cho đường không tối ưu. validation/counterexamples.py tìm ca
tệ hơn Dijkstra.
"""

from __future__ import annotations

from src.cost.heuristics.base import BaseHeuristic
from src.cost.speed_model import kmh_to_ms
from src.models import NodeId


class DynamicWeightedHeuristic(BaseHeuristic):
    name = "dynamic_weighted"

    def __init__(self, graph, bounds, w: float = 1.5) -> None:
        super().__init__(graph)
        if bounds is None:
            raise ValueError("dynamic_weighted cần SpeedBounds")
        if w <= 1.0:
            raise ValueError("dynamic_weighted cần w > 1 để làm heuristic đối chứng")
        self.bounds = bounds
        self.w = float(w)

    def __call__(self, node: NodeId, goal: NodeId, t: float) -> float:
        speed_ms = kmh_to_ms(float(self.bounds.v_mean(t)))
        if speed_ms <= 0.0:
            raise ValueError("SpeedBounds.v_mean(t) phải > 0")
        return self.w * self.dist_m(node, goal) / speed_ms
