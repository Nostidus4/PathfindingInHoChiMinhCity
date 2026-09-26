"""Kiểm admissibility: h(n, t) <= chi phí tối ưu thật (true_cost). Owner: P5.

Quét nhiều node x goal x mốc giờ, trả list vi phạm (node, goal, t, h, true).
"""

from __future__ import annotations

from collections.abc import Sequence

from src.models import Heuristic, NodeId


def check_admissibility(
    graph,
    heuristic: Heuristic,
    edge_cost,
    goals: Sequence[NodeId],
    times: Sequence[float],
    tol: float = 1e-6,
) -> list[tuple]:
    raise NotImplementedError("TODO(P5)")
