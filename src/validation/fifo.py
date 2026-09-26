"""Kiểm FIFO: t + c(e, t) không giảm theo t trên mọi edge. Owner: P3.

FIFO (xuất phát muộn hơn không bao giờ đến sớm hơn) là điều kiện để
time-dependent A*/Dijkstra cho kết quả đúng.
"""

from __future__ import annotations

from collections.abc import Sequence


def check_fifo(graph, edge_cost, times: Sequence[float], tol: float = 1e-6) -> list[tuple]:
    """Trả list (edge_id, t1, t2) vi phạm: t1 < t2 nhưng t1 + c(t1) > t2 + c(t2)."""
    raise NotImplementedError("TODO(P3)")
