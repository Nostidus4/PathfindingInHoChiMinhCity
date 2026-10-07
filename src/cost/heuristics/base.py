"""Protocol Heuristic: __call__(node, goal, t) -> giây. Owner: P4.

Protocol gốc ở models.py; file này re-export và có lớp cơ sở dùng chung
(giữ graph để lấy toạ độ, hàm dist_m(node, goal) dùng geo.haversine_m).
"""

from __future__ import annotations

from src.geo import haversine_m
from src.models import Heuristic, NodeId

__all__ = ["BaseHeuristic", "Heuristic"]


class BaseHeuristic:
    name: str = "base"

    def __init__(self, graph) -> None:
        self.graph = graph

    def dist_m(self, node: NodeId, goal: NodeId) -> float:
        """Khoảng cách chim bay (m) giữa node và goal."""
        a, b = self.graph.get_node(node), self.graph.get_node(goal)
        return haversine_m(a.lat, a.lon, b.lat, b.lon)

    def __call__(self, node: NodeId, goal: NodeId, t: float) -> float:
        raise NotImplementedError
