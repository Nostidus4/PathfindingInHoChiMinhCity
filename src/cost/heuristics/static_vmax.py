"""Heuristic static_vmax: h = haversine(node, goal) / v_max. Owner: P4.

v_max = tốc độ lớn nhất toàn mạng mọi thời điểm (SpeedBounds.v_max).
Admissible + consistent (cần length >= haversine), nhưng khá "lỏng".
"""

from __future__ import annotations

from src.cost.heuristics.base import BaseHeuristic
from src.models import NodeId


class StaticVmaxHeuristic(BaseHeuristic):
    name = "static_vmax"

    def __init__(self, graph, bounds) -> None:
        super().__init__(graph)
        self.bounds = bounds

    def __call__(self, node: NodeId, goal: NodeId, t: float) -> float:
        raise NotImplementedError("TODO(P4)")
