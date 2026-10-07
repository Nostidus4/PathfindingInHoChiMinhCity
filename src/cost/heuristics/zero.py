"""Heuristic zero: h = 0 luôn. A* với h=0 chính là Dijkstra. Owner: P4.

Luôn admissible và consistent; dùng làm baseline so sánh expanded nodes.
"""

from __future__ import annotations

from src.cost.heuristics.base import BaseHeuristic
from src.models import NodeId


class ZeroHeuristic(BaseHeuristic):
    name = "zero"

    def __call__(self, node: NodeId, goal: NodeId, t: float) -> float:
        return 0.0
