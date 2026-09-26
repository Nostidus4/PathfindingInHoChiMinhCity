"""Facade Pathfinder - điểm vào DUY NHẤT cho CLI, UI, experiments. Owner: P5.

    pf = Pathfinder(graph, provider, cfg)
    result = pf.route(start, goal, departure_time, heuristic_mode="dynamic_ub", trace=False)

Bên trong: tính SpeedBounds 1 lần, cache heuristic theo mode, tạo edge_cost
từ provider, gọi astar(). Validate input (node không tồn tại, mode sai) -> ValueError.
"""

from __future__ import annotations

from src.config import SimConfig
from src.models import CostMode, NodeId, RouteResult, TrafficProvider


class Pathfinder:
    def __init__(self, graph, provider: TrafficProvider, cfg: SimConfig) -> None:
        self.graph = graph
        self.provider = provider
        self.cfg = cfg
        # TODO(P5): self.bounds = compute_speed_bounds(...) ; self._heuristics = {}

    def route(
        self,
        start: NodeId,
        goal: NodeId,
        departure_time: float,
        heuristic_mode: str = "dynamic_ub",
        trace: bool = False,
        cost_mode: CostMode = CostMode.TIME,
    ) -> RouteResult:
        raise NotImplementedError("TODO(P5)")
