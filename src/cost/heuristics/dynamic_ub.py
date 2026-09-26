"""Heuristic dynamic_ub: h = haversine(node, goal) / v_ub(t). Owner: P4.

v_ub(t) là chặn trên tốc độ từ t trở đi (suffix max, không tăng), nên h vẫn
admissible nhưng chặt hơn static_vmax ngoài giờ thấp điểm.
Chứng minh admissible/consistent viết trong docs/heuristic_proof.md.
"""

from __future__ import annotations

from src.cost.heuristics.base import BaseHeuristic
from src.models import NodeId


class DynamicUBHeuristic(BaseHeuristic):
    name = "dynamic_ub"

    def __init__(self, graph, bounds) -> None:
        super().__init__(graph)
        self.bounds = bounds

    def __call__(self, node: NodeId, goal: NodeId, t: float) -> float:
        raise NotImplementedError("TODO(P4)")
