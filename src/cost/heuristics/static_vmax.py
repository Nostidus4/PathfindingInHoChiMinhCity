"""Heuristic static_vmax: h = haversine(node, goal) / v_max. Owner: P4.

v_max = tốc độ lớn nhất toàn mạng mọi thời điểm (SpeedBounds.v_max).
Admissible + consistent (cần length >= haversine), nhưng khá "lỏng".
"""

from __future__ import annotations

from src.cost.heuristics.base import BaseHeuristic
from src.cost.speed_model import kmh_to_ms
from src.models import NodeId


class StaticVmaxHeuristic(BaseHeuristic):
    name = "static_vmax"

    def __init__(self, graph, bounds) -> None:
        super().__init__(graph)
        if bounds is None:
            raise ValueError("static_vmax cần SpeedBounds")
        self.bounds = bounds

    def __call__(self, node: NodeId, goal: NodeId, t: float) -> float:
        del t  # static heuristic deliberately does not depend on time.
        speed_ms = kmh_to_ms(float(self.bounds.v_max_kmh))
        if speed_ms <= 0.0:
            raise ValueError("SpeedBounds.v_max_kmh phải > 0")
        return self.dist_m(node, goal) / speed_ms
