"""Time-dependent A*. Owner: P5.

astar(graph, start, goal, departure_time, edge_cost, heuristic, trace=None) -> RouteResult
- edge_cost(segment, t) -> giây ; heuristic(node, goal, t) -> giây (đều là callable).
- g(n) = thời điểm đến n - departure_time ; t khi đi cạnh = departure_time + g(u).
- Dùng heapq, xử lý tie-break ổn định, đếm expanded_nodes, đo runtime.
- Không có đường -> RouteResult(found=False, ...).
- Không biết gì về traffic hay UI.

Điều kiện để kết quả TỐI ƯU (xem docs/algorithm_walkthrough.md §1):
- FIFO: `t + c(e, t)` không giảm theo t (kiểm bằng validation/fifo.py). Không có
  hành động đứng chờ, nên một earliest-arrival label mỗi node là đủ.
- Chi phí cạnh không âm; `+inf` = cạnh bị chặn.
- Heuristic admissible và h(goal, t) = 0.

Heuristic chỉ admissible mà KHÔNG consistent vẫn cho kết quả tối ưu nhờ
*reopening*: node đã expand được mở lại khi tìm được g nhỏ hơn. Heuristic không
admissible (`dynamic_weighted`) vẫn chạy được để làm đối chứng, nhưng mất bảo
đảm tối ưu — đó chính là thứ validation/counterexamples.py đo.
"""

from __future__ import annotations

import heapq
import itertools
import math
from dataclasses import dataclass
from time import perf_counter

from src.models import NodeId, RoadSegment, RouteResult, TraceStep
from src.search.contracts import (
    EdgeCostFn,
    HeuristicFn,
    check_query,
    checked_edge,
    node_ids,
    nonnegative,
)
from src.search.trace import TraceRecorder

__all__ = ["EdgeCostFn", "HeuristicFn", "astar"]


@dataclass(frozen=True, slots=True)
class _Label:
    """Một nhãn (node, g) bất biến.

    Nhãn bất biến + parent trỏ tới nhãn (không phải node) là lý do dựng lại
    đường đi luôn đúng kể cả khi node bị reopen: nhãn cũ không bị ghi đè nên
    chuỗi parent của nhãn tới goal vẫn là chuỗi đã sinh ra nó.
    """

    node: NodeId
    g: float
    h: float
    parent: _Label | None = None
    segment: RoadSegment | None = None


def _reconstruct(label: _Label) -> tuple[list[NodeId], list[RoadSegment]]:
    """Đi ngược chuỗi parent -> (path, các segment thực sự được chọn)."""
    nodes: list[NodeId] = []
    segments: list[RoadSegment] = []
    while label is not None:
        nodes.append(label.node)
        if label.segment is not None:
            segments.append(label.segment)
        label = label.parent
    nodes.reverse()
    segments.reverse()
    return nodes, segments


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
    """Tìm đường nhanh nhất từ start tới goal khi xuất phát lúc departure_time.

    `expanded_nodes` đếm số lần pop một nhãn còn hiệu lực (gồm cả goal); node bị
    reopen được đếm lại. Heap sắp theo (f, h, số thứ tự) nên không bao giờ so
    sánh NodeId và kết quả tái lập được.
    """
    began = perf_counter()
    ids = node_ids(graph)
    departure_time = check_query(ids, start, goal, departure_time)

    def h_at(node: NodeId, t: float) -> float:
        value = nonnegative(heuristic(node, goal, t), f"heuristic({node!r}, {goal!r}, {t})")
        if node == goal and value != 0.0:
            raise ValueError(f"heuristic(goal, goal, t) phải bằng 0, nhận được {value!r}")
        return value

    n_steps = 0

    def record(action: str, label: _Label, open_size: int, note: str = "") -> None:
        nonlocal n_steps
        if trace is None:
            return
        trace.record(
            TraceStep(
                step=n_steps,
                node=label.node,
                g=label.g,
                h=label.h,
                t=departure_time + label.g,
                action=action,
                open_size=open_size,
                note=note,
            )
        )
        n_steps += 1

    serial = itertools.count()
    first = _Label(start, 0.0, h_at(start, departure_time))
    heap: list[tuple[float, float, int, _Label]] = [(first.h, first.h, next(serial), first)]
    best: dict[NodeId, _Label] = {start: first}
    closed: set[NodeId] = set()
    expanded = 0

    def finish(found: bool, label: _Label | None) -> RouteResult:
        runtime_ms = (perf_counter() - began) * 1000.0
        steps = list(trace.steps) if trace is not None else []
        if not found or label is None:
            return RouteResult(
                found=False,
                path=[],
                edges=[],
                departure_time_s=departure_time,
                arrival_time_s=departure_time,
                total_cost=math.inf,
                expanded_nodes=expanded,
                runtime_ms=runtime_ms,
                heuristic_mode=heuristic_mode,
                trace=steps,
            )
        path, segments = _reconstruct(label)
        return RouteResult(
            found=True,
            path=path,
            edges=[s.id for s in segments],
            departure_time_s=departure_time,
            arrival_time_s=departure_time + label.g,
            total_cost=label.g,
            expanded_nodes=expanded,
            total_distance_m=sum(float(s.length_m) for s in segments),
            runtime_ms=runtime_ms,
            heuristic_mode=heuristic_mode,
            trace=steps,
        )

    while heap:
        _, _, _, current = heapq.heappop(heap)
        # Nhãn cũ: đã bị một nhãn tốt hơn thay thế, hoặc node đã expand xong.
        if best.get(current.node) is not current or current.node in closed:
            record("skip", current, len(heap), "nhãn cũ, đã có nhãn tốt hơn")
            continue
        closed.add(current.node)
        expanded += 1
        record("expand", current, len(heap))

        if current.node == goal:
            return finish(True, current)

        t_u = departure_time + current.g
        for segment in graph.get_neighbors(current.node):
            checked_edge(ids, segment, current.node)
            cost = nonnegative(
                edge_cost(segment, t_u), f"edge_cost({segment.id!r}, {t_u})", allow_infinity=True
            )
            if math.isinf(cost):
                continue  # cạnh bị chặn tại thời điểm này
            candidate = current.g + cost
            if not math.isfinite(candidate):
                raise ValueError("tổng chi phí bị tràn số")
            old = best.get(segment.target)
            if old is not None and candidate >= old.g:
                continue
            h = h_at(segment.target, departure_time + candidate)
            label = _Label(segment.target, candidate, h, current, segment)
            reopened = segment.target in closed
            closed.discard(segment.target)
            best[segment.target] = label
            heapq.heappush(heap, (candidate + label.h, label.h, next(serial), label))
            record(
                "push" if old is None else "update",
                label,
                len(heap),
                "reopen" if reopened else "",
            )

    return finish(False, None)
