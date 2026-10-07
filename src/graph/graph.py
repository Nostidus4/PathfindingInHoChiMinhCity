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
        self._nodes: dict[NodeId, POI] = {}
        for p in pois:
            if p.id in self._nodes:
                raise ValueError(f"Trùng id node: {p.id!r}")
            self._nodes[p.id] = p

        self._edges: dict[EdgeId, RoadSegment] = {}
        self._out: dict[NodeId, list[RoadSegment]] = {n: [] for n in self._nodes}
        self._in: dict[NodeId, list[RoadSegment]] = {n: [] for n in self._nodes}
        for e in edges:
            if e.id in self._edges:
                raise ValueError(f"Trùng id cạnh: {e.id!r}")
            if e.source not in self._nodes or e.target not in self._nodes:
                raise ValueError(f"Cạnh {e.id!r} nối tới node không tồn tại")
            self._edges[e.id] = e
            self._out[e.source].append(e)
            self._in[e.target].append(e)

    def __len__(self) -> int:
        return len(self._nodes)

    def __contains__(self, node: object) -> bool:
        return node in self._nodes

    def get_neighbors(self, node: NodeId) -> list[RoadSegment]:
        """Các cạnh đi ra từ node."""
        return list(self._out.get(node, []))

    def get_in_edges(self, node: NodeId) -> list[RoadSegment]:
        """Các cạnh đi vào node (dùng cho kiểm tra liên thông)."""
        return list(self._in.get(node, []))

    def get_node(self, node: NodeId) -> POI:
        return self._nodes[node]

    def get_edge(self, edge_id: EdgeId) -> RoadSegment:
        return self._edges[edge_id]

    def nodes(self) -> list[POI]:
        return list(self._nodes.values())

    def edges(self) -> list[RoadSegment]:
        return list(self._edges.values())
