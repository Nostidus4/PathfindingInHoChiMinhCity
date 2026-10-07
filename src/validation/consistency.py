"""Kiểm consistency: h(u, t) <= c(u, v, t) + h(v, t + c). Owner: P5.

Quét mọi edge x lưới thời gian (GRID_STEP), trả list vi phạm.
"""

from __future__ import annotations

from collections.abc import Sequence

from src.models import Heuristic, NodeId


def check_consistency(
    graph,
    heuristic: Heuristic,
    edge_cost,
    goals: Sequence[NodeId],
    times: Sequence[float],
    tol: float = 1e-6,
) -> list[tuple]:
    raise NotImplementedError("TODO(P5)")
