"""Dijkstra time-dependent và ground truth. Owner: P5.

- dijkstra(...): earliest-arrival Dijkstra, cài ĐỘC LẬP (không gọi astar).
- earliest_arrival_times(...): một lần quét cho ra travel time tối ưu tới MỌI node.
- true_cost(graph, n, goal, t, edge_cost): chi phí tối ưu thật từ n tới goal khi
  xuất phát lúc t. validation/ dùng làm đáp án để kiểm admissibility.

!!! Vì sao KHÔNG viết `dijkstra = astar(h=0)`: validation/ dùng Dijkstra làm đáp
án để kiểm A*. Nếu oracle gọi lại chính engine đang được kiểm thì một lỗi trong
astar sẽ xuất hiện ở cả hai bên và test vẫn xanh. Hai cài đặt tách rời biến
`compare_routes`/`check_admissibility` thành phép kiểm chéo thật sự. Việc A* với
mode `zero` cho đúng kết quả Dijkstra được khẳng định bằng test
(tests/test_astar.py::test_zero_mode_matches_independent_dijkstra).
"""

from __future__ import annotations

import heapq
import itertools
import math
from time import perf_counter

from src.models import EdgeId, NodeId, RouteResult
from src.search.contracts import EdgeCostFn, check_query, checked_edge, node_ids, nonnegative

__all__ = ["dijkstra", "earliest_arrival_times", "true_cost"]

_Parent = tuple[NodeId, EdgeId, float]


def _settle(
    graph,
    source: NodeId,
    departure_time: float,
    edge_cost: EdgeCostFn,
    ids: set[NodeId],
    goal: NodeId | None = None,
) -> tuple[dict[NodeId, float], dict[NodeId, _Parent], int]:
    """Lõi label-setting. goal=None -> quét hết; goal != None -> dừng khi settle goal.

    Trả (g tối ưu theo node, parent theo node, số node đã settle).
    """
    counter = itertools.count()
    g: dict[NodeId, float] = {source: 0.0}
    parents: dict[NodeId, _Parent] = {}
    settled: set[NodeId] = set()
    queue: list[tuple[float, int, NodeId]] = [(0.0, next(counter), source)]
    expanded = 0

    while queue:
        dist, _, u = heapq.heappop(queue)
        if u in settled or dist != g[u]:
            continue
        settled.add(u)
        expanded += 1
        if u == goal:
            break
        t_u = departure_time + dist
        for segment in graph.get_neighbors(u):
            checked_edge(ids, segment, u)
            cost = nonnegative(
                edge_cost(segment, t_u), f"edge_cost({segment.id!r}, {t_u})", allow_infinity=True
            )
            if math.isinf(cost):
                continue
            new_g = dist + cost
            if not math.isfinite(new_g):
                raise ValueError("tổng chi phí bị tràn số")
            if segment.target in settled or new_g >= g.get(segment.target, math.inf):
                continue
            g[segment.target] = new_g
            parents[segment.target] = (u, segment.id, float(segment.length_m))
            heapq.heappush(queue, (new_g, next(counter), segment.target))

    return g, parents, expanded


def dijkstra(
    graph, start: NodeId, goal: NodeId, departure_time: float, edge_cost: EdgeCostFn
) -> RouteResult:
    """Đường nhanh nhất start -> goal; RouteResult(found=False) nếu không có đường."""
    began = perf_counter()
    ids = node_ids(graph)
    departure_time = check_query(ids, start, goal, departure_time)
    g, parents, expanded = _settle(graph, start, departure_time, edge_cost, ids, goal)
    runtime_ms = (perf_counter() - began) * 1000.0

    if goal not in g:
        return RouteResult(
            found=False,
            path=[],
            edges=[],
            departure_time_s=departure_time,
            arrival_time_s=departure_time,
            total_cost=math.inf,
            expanded_nodes=expanded,
            runtime_ms=runtime_ms,
            heuristic_mode="zero",
        )

    path: list[NodeId] = [goal]
    edges: list[EdgeId] = []
    distance_m = 0.0
    while path[-1] != start:
        previous, edge_id, length_m = parents[path[-1]]
        path.append(previous)
        edges.append(edge_id)
        distance_m += length_m
    path.reverse()
    edges.reverse()

    return RouteResult(
        found=True,
        path=path,
        edges=edges,
        departure_time_s=departure_time,
        arrival_time_s=departure_time + g[goal],
        total_cost=g[goal],
        expanded_nodes=expanded,
        total_distance_m=distance_m,
        runtime_ms=runtime_ms,
        heuristic_mode="zero",
    )


def earliest_arrival_times(
    graph, source: NodeId, departure_time: float, edge_cost: EdgeCostFn
) -> dict[NodeId, float]:
    """Travel time tối ưu (giây) từ source tới mọi node đi tới được, khi đi lúc t.

    Một lần quét thay cho N lần gọi true_cost(): check_admissibility dùng hàm này
    nên chỉ cần |nodes| x |times| lần Dijkstra thay vì |nodes| x |goals| x |times|.
    Node không đi tới được KHÔNG có trong dict trả về.
    """
    ids = node_ids(graph)
    if source not in ids:
        raise ValueError(f"source {source!r} không có trong graph")
    departure_time = nonnegative(departure_time, "departure_time")
    g, _, _ = _settle(graph, source, departure_time, edge_cost, ids)
    return g


def true_cost(graph, n: NodeId, goal: NodeId, t: float, edge_cost: EdgeCostFn) -> float:
    """Chi phí tối ưu (giây) từ n tới goal xuất phát lúc t; inf nếu không có đường."""
    res = dijkstra(graph, n, goal, t, edge_cost)
    return res.total_cost if res.found else float("inf")
