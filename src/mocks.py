"""Dữ liệu giả (mock) để cả nhóm làm SONG SONG từ ngày đầu, chưa cần OSM.

- MockGraph: đồ thị 7 node (A..G), cùng interface với graph.Graph
  (get_neighbors, get_node, get_edge, nodes, edges).
- MockTrafficProvider: tốc độ hằng (mặc định 36 km/h = 10 m/s), có thể bật
  "giờ cao điểm" để test time-dependence.
- MOCK_OPTIMA: đáp án tối ưu biết trước để test A*/Dijkstra.

Mọi toạ độ được đặt sao cho haversine <= length_m của cạnh (heuristic admissible).

        G --(oneway)--> A --1000-- B --500-- D --600-- F
                        |        / |         |        /
                       400    300  900     1200    700
                        |    /     |         |    /
                        C ---------+-- 1000 -- E
    (C-D 1200, C-E 1000, B-E 900; G chỉ có cạnh một chiều G->A nên A->G là no-path)
"""

from __future__ import annotations

from src.models import POI, EdgeId, NodeId, RoadSegment, TrafficState
from src.timeutil import parse_hhmm

MOCK_POIS: tuple[POI, ...] = (
    POI("A", "Mock A", 10.7700, 106.7000, "Quan 1"),
    POI("B", "Mock B", 10.7730, 106.7025, "Quan 1"),
    POI("C", "Mock C", 10.7730, 106.7000, "Quan 1"),
    POI("D", "Mock D", 10.7770, 106.7025, "Quan 3"),
    POI("E", "Mock E", 10.7760, 106.7045, "Quan 3"),
    POI("F", "Mock F", 10.7770, 106.7070, "Quan 3"),
    POI("G", "Mock G", 10.7680, 106.6980, "Quan 1"),
)

# (u, v, length_m, road_type, hai_chiều?)
_EDGE_SPECS: tuple[tuple[str, str, float, str, bool], ...] = (
    ("A", "B", 1000.0, "primary", True),
    ("A", "C", 400.0, "secondary", True),
    ("C", "B", 300.0, "residential", True),
    ("B", "D", 500.0, "secondary", True),
    ("C", "D", 1200.0, "primary", True),
    ("D", "F", 600.0, "secondary", True),
    ("C", "E", 1000.0, "primary", True),
    ("E", "F", 700.0, "residential", True),
    ("B", "E", 900.0, "tertiary", True),
    ("G", "A", 400.0, "residential", False),
)

# (start, goal) -> (path, tổng chiều dài m, thời gian s ở tốc độ 10 m/s)
MOCK_OPTIMA: dict[tuple[NodeId, NodeId], tuple[list[NodeId], float, float]] = {
    ("A", "F"): (["A", "C", "B", "D", "F"], 1800.0, 180.0),
    ("F", "A"): (["F", "D", "B", "C", "A"], 1800.0, 180.0),
    ("C", "F"): (["C", "B", "D", "F"], 1400.0, 140.0),
}
MOCK_NO_PATH: tuple[NodeId, NodeId] = ("A", "G")


def _build_edges() -> tuple[RoadSegment, ...]:
    edges: list[RoadSegment] = []
    for u, v, length, road_type, both in _EDGE_SPECS:
        edges.append(RoadSegment(f"{u}->{v}", u, v, length, road_type))
        if both:
            edges.append(RoadSegment(f"{v}->{u}", v, u, length, road_type))
    return tuple(edges)


class MockGraph:
    """Đồ thị mock, cùng interface với src.graph.Graph."""

    def __init__(self) -> None:
        self._nodes = {p.id: p for p in MOCK_POIS}
        self._edges = {e.id: e for e in _build_edges()}
        self._out: dict[NodeId, list[RoadSegment]] = {n: [] for n in self._nodes}
        for e in self._edges.values():
            self._out[e.source].append(e)

    def get_neighbors(self, node: NodeId) -> list[RoadSegment]:
        """Các cạnh đi ra từ node."""
        return list(self._out.get(node, []))

    def get_node(self, node: NodeId) -> POI:
        return self._nodes[node]

    def get_edge(self, edge_id: EdgeId) -> RoadSegment:
        return self._edges[edge_id]

    def nodes(self) -> list[POI]:
        return list(self._nodes.values())

    def edges(self) -> list[RoadSegment]:
        return list(self._edges.values())


class MockTrafficProvider:
    """Tốc độ hằng speed_kmh; nếu rush_factor < 1 thì trong [rush_start, rush_end)
    tốc độ bị nhân với rush_factor (để test chi phí phụ thuộc giờ xuất phát)."""

    def __init__(
        self,
        speed_kmh: float = 36.0,
        rush_factor: float = 1.0,
        rush_start: str = "07:00",
        rush_end: str = "09:00",
        density_veh_km: float = 20.0,
    ) -> None:
        self.speed_kmh = speed_kmh
        self.rush_factor = rush_factor
        self.rush_start = parse_hhmm(rush_start)
        self.rush_end = parse_hhmm(rush_end)
        self.density_veh_km = density_veh_km

    def get_traffic(self, edge_id: EdgeId, t: float) -> TrafficState:
        v = self.speed_kmh
        if self.rush_start <= t % 86400 < self.rush_end:
            v *= self.rush_factor
        k = self.density_veh_km
        return TrafficState(density_veh_km=k, speed_kmh=v, flow_veh_h=k * v)
