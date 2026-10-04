"""FakePathfinder cho test WP6 (owner: P6), KHÔNG dùng trong src/.

Cùng interface với src.search.pathfinder.Pathfinder.route(...) để test CLI,
experiments, viz khi WP3/WP5 chưa xong. Là A* time-dependent đơn giản trên
graph + provider bất kỳ; tốc độ lấy thẳng từ TrafficState.speed_kmh.
Khi Pathfinder thật đã có, test vẫn dùng fake này để cô lập phần WP6.
"""

from __future__ import annotations

import heapq
import time

from src.cost.heuristics import HEURISTIC_MODES
from src.geo import haversine_m
from src.models import CostMode, NodeId, RouteResult, TraceStep


class FakePathfinder:
    def __init__(self, graph, provider, v_max_kmh: float = 36.0, weight: float = 1.5) -> None:
        self.graph = graph
        self.provider = provider
        self.v_max_ms = v_max_kmh / 3.6
        self.weight = weight
        self.calls: list[tuple[NodeId, NodeId, float, str]] = []

    def _h(self, mode: str, node: NodeId, goal: NodeId) -> float:
        if mode == "zero":
            return 0.0
        a, b = self.graph.get_node(node), self.graph.get_node(goal)
        h = haversine_m(a.lat, a.lon, b.lat, b.lon) / self.v_max_ms
        return self.weight * h if mode == "dynamic_weighted" else h

    def _cost(self, seg, t: float) -> float:
        return seg.length_m / (self.provider.get_traffic(seg.id, t).speed_kmh / 3.6)

    def route(
        self,
        start: NodeId,
        goal: NodeId,
        departure_time: float,
        heuristic_mode: str = "dynamic_ub",
        trace: bool = False,
        cost_mode: CostMode = CostMode.TIME,
    ) -> RouteResult:
        ids = {p.id for p in self.graph.nodes()}
        for n in (start, goal):
            if n not in ids:
                raise ValueError(f"Node không tồn tại: {n!r}")
        if heuristic_mode not in HEURISTIC_MODES:
            raise ValueError(f"Heuristic không hợp lệ: {heuristic_mode!r}")
        self.calls.append((start, goal, departure_time, heuristic_mode))

        t0 = time.perf_counter()
        g = {start: 0.0}
        parent: dict[NodeId, tuple[NodeId, str]] = {}
        closed: set[NodeId] = set()
        heap = [(self._h(heuristic_mode, start, goal), 0, start)]
        counter = 1
        steps: list[TraceStep] = []
        while heap:
            _, _, u = heapq.heappop(heap)
            if u in closed:
                continue
            closed.add(u)
            if trace:
                steps.append(
                    TraceStep(
                        len(steps),
                        u,
                        g[u],
                        self._h(heuristic_mode, u, goal),
                        departure_time + g[u],
                        open_size=len(heap),
                    )
                )
            if u == goal:
                break
            for seg in self.graph.get_neighbors(u):
                ng = g[u] + self._cost(seg, departure_time + g[u])
                if seg.target not in closed and ng < g.get(seg.target, float("inf")):
                    g[seg.target] = ng
                    parent[seg.target] = (u, seg.id)
                    f = ng + self._h(heuristic_mode, seg.target, goal)
                    heapq.heappush(heap, (f, counter, seg.target))
                    counter += 1
        runtime_ms = (time.perf_counter() - t0) * 1000

        if goal not in closed:
            return RouteResult(
                False,
                [],
                [],
                departure_time,
                departure_time,
                float("inf"),
                len(closed),
                runtime_ms=runtime_ms,
                heuristic_mode=heuristic_mode,
                trace=steps,
            )
        path, edges = [goal], []
        while path[-1] != start:
            prev, eid = parent[path[-1]]
            path.append(prev)
            edges.append(eid)
        path.reverse()
        edges.reverse()
        return RouteResult(
            True,
            path,
            edges,
            departure_time,
            departure_time + g[goal],
            g[goal],
            len(closed),
            total_distance_m=sum(self.graph.get_edge(e).length_m for e in edges),
            runtime_ms=runtime_ms,
            heuristic_mode=heuristic_mode,
            trace=steps,
        )
