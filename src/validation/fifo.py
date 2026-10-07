"""Kiểm FIFO: t + c(e, t) không giảm theo t trên mọi edge. Owner: P3.

FIFO (xuất phát muộn hơn không bao giờ đến sớm hơn) là điều kiện để
time-dependent A*/Dijkstra cho kết quả đúng.

Chỉ cần so các cặp thời điểm LIỀN KỀ (sau khi sắp xếp): nếu mọi cặp liền kề đều có
arrival không giảm thì cả dãy không giảm. Tương đương: độ dốc
(c(t2) - c(t1)) / (t2 - t1) >= -1 trên mọi đoạn. Lưới thời gian càng mịn thì kiểm càng
chặt (giữa hai mốc 15 phút c(e, t) có thể cong).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise


def _sorted_times(times: Sequence[float]) -> list[float]:
    return sorted({float(t) for t in times})


def check_fifo(graph, edge_cost, times: Sequence[float], tol: float = 1e-6) -> list[tuple]:
    """Trả list (edge_id, t1, t2) vi phạm: t1 < t2 nhưng t1 + c(t1) > t2 + c(t2)."""
    ts = _sorted_times(times)
    violations: list[tuple] = []
    if len(ts) < 2:
        return violations
    for e in graph.edges():
        prev_t, prev_arrival = ts[0], ts[0] + edge_cost(e, ts[0])
        for t in ts[1:]:
            arrival = t + edge_cost(e, t)
            if prev_arrival > arrival + tol:
                violations.append((e.id, prev_t, t))
            prev_t, prev_arrival = t, arrival
    return violations


@dataclass(frozen=True, slots=True)
class FifoReport:
    """Tổng kết kiểm FIFO cho báo cáo (docs/traffic_model.md §5)."""

    n_edges: int
    n_checks: int  # số cặp (t1, t2) liền kề đã so trên mọi edge
    violations: tuple[tuple, ...]
    min_slope: float  # dc/dt nhỏ nhất (âm nhất); FIFO <=> min_slope >= -1
    worst_edge: str
    worst_t: float  # đầu đoạn có độ dốc nhỏ nhất
    max_slope: float  # dc/dt lớn nhất (cost tăng nhanh nhất khi vào giờ cao điểm)

    @property
    def ok(self) -> bool:
        return not self.violations


def fifo_report(graph, edge_cost, times: Sequence[float], tol: float = 1e-6) -> FifoReport:
    """Giống check_fifo nhưng kèm thống kê độ dốc của c(e, t)."""
    ts = _sorted_times(times)
    violations: list[tuple] = []
    n_edges = n_checks = 0
    min_slope, max_slope = float("inf"), float("-inf")
    worst_edge, worst_t = "", ts[0] if ts else 0.0
    for e in graph.edges():
        n_edges += 1
        points = [(t, edge_cost(e, t)) for t in ts]
        for (t1, c1), (t2, c2) in pairwise(points):
            n_checks += 1
            slope = (c2 - c1) / (t2 - t1)
            if slope < min_slope:
                min_slope, worst_edge, worst_t = slope, e.id, t1
            max_slope = max(max_slope, slope)
            if t1 + c1 > t2 + c2 + tol:
                violations.append((e.id, t1, t2))
    return FifoReport(
        n_edges=n_edges,
        n_checks=n_checks,
        violations=tuple(violations),
        min_slope=min_slope if n_checks else 0.0,
        worst_edge=worst_edge,
        worst_t=worst_t,
        max_slope=max_slope if n_checks else 0.0,
    )
