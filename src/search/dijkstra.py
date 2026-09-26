"""Dijkstra (= A* với h = 0) và ground truth. Owner: P5.

- dijkstra(...): gọi astar với heuristic trả 0.
- true_cost(graph, n, goal, t, edge_cost): chi phí tối ưu thật từ n tới goal khi
  xuất phát lúc t. validation/ dùng làm đáp án để kiểm admissibility.
"""

from __future__ import annotations

from src.models import NodeId, RouteResult
from src.search.astar import EdgeCostFn, astar


def dijkstra(
    graph, start: NodeId, goal: NodeId, departure_time: float, edge_cost: EdgeCostFn
) -> RouteResult:
    return astar(
        graph, start, goal, departure_time, edge_cost, lambda n, g, t: 0.0, heuristic_mode="zero"
    )


def true_cost(graph, n: NodeId, goal: NodeId, t: float, edge_cost: EdgeCostFn) -> float:
    """Chi phí tối ưu (giây) từ n tới goal xuất phát lúc t; inf nếu không có đường."""
    res = dijkstra(graph, n, goal, t, edge_cost)
    return res.total_cost if res.found else float("inf")
