"""Class Graph: đồ thị có hướng giữa các POI. Owner: P2.

Interface (MockGraph trong mocks.py có cùng interface):
- get_neighbors(node) -> list[RoadSegment]   các cạnh đi ra
- get_node(node) -> POI
- get_edge(edge_id) -> RoadSegment
- nodes() -> list[POI], edges() -> list[RoadSegment]
Graph không biết gì về traffic; chỉ chứa cấu trúc tĩnh.
"""

from __future__ import annotations

from collections.abc import Iterable

from src.models import POI, EdgeId, NodeId, RoadSegment


class Graph:
    def __init__(self, pois: Iterable[POI], edges: Iterable[RoadSegment]) -> None:
        # TODO(P2): lưu dict node, dict edge, adjacency list đi ra
        raise NotImplementedError("TODO(P2)")

    def get_neighbors(self, node: NodeId) -> list[RoadSegment]:
        raise NotImplementedError("TODO(P2)")

    def get_node(self, node: NodeId) -> POI:
        raise NotImplementedError("TODO(P2)")

    def get_edge(self, edge_id: EdgeId) -> RoadSegment:
        raise NotImplementedError("TODO(P2)")

    def nodes(self) -> list[POI]:
        raise NotImplementedError("TODO(P2)")

    def edges(self) -> list[RoadSegment]:
        raise NotImplementedError("TODO(P2)")
