"""Heuristic dynamic_weighted: h = w * haversine(node, goal) / v_mean(t). Owner: P4.

KHÔNG đảm bảo admissible (w > 1, dùng v_mean thay vì chặn trên) -> nhanh hơn
nhưng có thể cho đường không tối ưu. validation/counterexamples.py tìm ca tệ hơn Dijkstra.
"""

from __future__ import annotations

from src.cost.heuristics.base import BaseHeuristic
from src.models import NodeId


class DynamicWeightedHeuristic(BaseHeuristic):
    name = "dynamic_weighted"

    def __init__(self, graph, bounds, w: float = 1.5) -> None:
        super().__init__(graph)
        self.bounds = bounds
        self.w = w

    def __call__(self, node: NodeId, goal: NodeId, t: float) -> float:
        raise NotImplementedError("TODO(P4)")
