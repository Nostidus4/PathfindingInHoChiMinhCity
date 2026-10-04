"""Heuristic dynamic_ub: h = haversine(node, goal) / v_ub(t). Owner: P4.

v_ub(t) là chặn trên tốc độ từ t trở đi (suffix max, không tăng), nên h vẫn
admissible và consistent khi các giả thiết trong docs/heuristic_proof.md đúng.
"""

from __future__ import annotations

from src.cost.heuristics.base import BaseHeuristic
from src.cost.speed_model import kmh_to_ms
from src.models import NodeId


class DynamicUBHeuristic(BaseHeuristic):
    name = "dynamic_ub"

    def __init__(self, graph, bounds) -> None:
        super().__init__(graph)
        if bounds is None:
            raise ValueError("dynamic_ub cần SpeedBounds")
        self.bounds = bounds

    def __call__(self, node: NodeId, goal: NodeId, t: float) -> float:
        speed_ms = kmh_to_ms(float(self.bounds.v_ub(t)))
        if speed_ms <= 0.0:
            raise ValueError("SpeedBounds.v_ub(t) phải > 0")
        return self.dist_m(node, goal) / speed_ms
