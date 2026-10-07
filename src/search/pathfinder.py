"""Facade Pathfinder - điểm vào DUY NHẤT cho CLI, UI, experiments. Owner: P5.

    pf = Pathfinder(graph, provider, cfg)
    result = pf.route(start, goal, departure_time, heuristic_mode="dynamic_ub", trace=False)

Bên trong: tính SpeedBounds 1 lần, cache heuristic theo mode, tạo edge_cost
từ provider, gọi astar(). Validate input (node không tồn tại, mode sai) -> ValueError.
"""

from __future__ import annotations

from src.config import SimConfig
from src.cost.edge_cost import make_edge_cost
from src.cost.heuristics import make_heuristic
from src.models import CostMode, Heuristic, NodeId, RouteResult, TrafficProvider
from src.search.astar import astar
from src.search.contracts import node_ids
from src.search.trace import TraceRecorder
from src.traffic.speed_bounds import compute_speed_bounds


class Pathfinder:
    def __init__(self, graph, provider: TrafficProvider, cfg: SimConfig) -> None:
        self.graph = graph
        self.provider = provider
        self.cfg = cfg
        # SpeedBounds quét mọi edge x mốc lưới nên chỉ tính MỘT lần cho cả đời
        # Pathfinder; 4 heuristic dùng chung object này.
        self.bounds = compute_speed_bounds(graph, provider, cfg)
        self.edge_cost = make_edge_cost(provider, CostMode.TIME)
        self._node_ids = node_ids(graph)
        self._heuristics: dict[str, Heuristic] = {}

    def heuristic(self, mode: str) -> Heuristic:
        """Heuristic object theo mode, tạo một lần rồi cache. ValueError nếu mode sai."""
        if mode not in self._heuristics:
            self._heuristics[mode] = make_heuristic(
                mode, self.graph, self.bounds, {"w": self.cfg.weight_w}
            )
        return self._heuristics[mode]

    def route(
        self,
        start: NodeId,
        goal: NodeId,
        departure_time: float,
        heuristic_mode: str = "dynamic_ub",
        trace: bool = False,
        cost_mode: CostMode = CostMode.TIME,
    ) -> RouteResult:
        """Tìm đường start -> goal. RouteResult(found=False) nếu không có đường."""
        for ten, node in (("start", start), ("goal", goal)):
            if node not in self._node_ids:
                raise ValueError(f"POI {node!r} không tồn tại trong graph ({ten})")
        try:
            mode = CostMode(cost_mode)
        except ValueError as exc:
            raise ValueError(f"CostMode không hợp lệ: {cost_mode!r}") from exc

        recorder = TraceRecorder() if trace else None
        if mode is CostMode.DISTANCE:
            result = self._route_by_distance(start, goal, departure_time, recorder)
        else:
            result = astar(
                self.graph,
                start,
                goal,
                departure_time,
                self.edge_cost,
                self.heuristic(heuristic_mode),
                recorder,
                heuristic_mode,
            )
        result.cost_mode = mode
        return result

    def _route_by_distance(
        self, start: NodeId, goal: NodeId, departure_time: float, recorder: TraceRecorder | None
    ) -> RouteResult:
        """Baseline phụ: đường NGẮN NHẤT theo mét, kèm ETA thật của đường đó.

        Heuristic của WP4 trả giây nên KHÔNG admissible với chi phí tính bằng
        mét; vì vậy mode này luôn dùng heuristic `zero` (= Dijkstra theo quãng
        đường). `total_cost` là mét, còn `arrival_time_s` được tính lại bằng cách
        đi lại đúng đường đó với chi phí thời gian, để so được với mode TIME.
        """
        result = astar(
            self.graph,
            start,
            goal,
            departure_time,
            make_edge_cost(self.provider, CostMode.DISTANCE),
            self.heuristic("zero"),
            recorder,
            "zero",
        )
        if result.found:
            t = departure_time
            for edge_id in result.edges:
                t += self.edge_cost(self.graph.get_edge(edge_id), t)
            result.arrival_time_s = t
        return result
