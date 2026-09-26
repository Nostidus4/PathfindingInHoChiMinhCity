"""Time-dependent A*. Owner: P5.

astar(graph, start, goal, departure_time, edge_cost, heuristic, trace=None) -> RouteResult
- edge_cost(segment, t) -> giây ; heuristic(node, goal, t) -> giây (đều là callable).
- g(n) = thời điểm đến n - departure_time ; t khi đi cạnh = departure_time + g(u).
- Dùng heapq, xử lý tie-break ổn định, đếm expanded_nodes, đo runtime.
- Không có đường -> RouteResult(found=False, ...).
- Không biết gì về traffic hay UI.
"""

from __future__ import annotations

from collections.abc import Callable

from src.models import NodeId, RoadSegment, RouteResult
from src.search.trace import TraceRecorder

EdgeCostFn = Callable[[RoadSegment, float], float]
HeuristicFn = Callable[[NodeId, NodeId, float], float]


def astar(
    graph,
    start: NodeId,
    goal: NodeId,
    departure_time: float,
    edge_cost: EdgeCostFn,
    heuristic: HeuristicFn,
    trace: TraceRecorder | None = None,
    heuristic_mode: str = "",
) -> RouteResult:
    raise NotImplementedError("TODO(P5)")
