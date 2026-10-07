"""Tìm ca A* cho kết quả tệ hơn Dijkstra (dùng cho dynamic_weighted). Owner: P5.

Chạy cả hai trên nhiều (start, goal, t), ghi lại ca cost_A* > cost_Dijkstra
để minh hoạ heuristic không admissible thì mất tối ưu.
"""

from __future__ import annotations

from collections.abc import Sequence

from src.models import NodeId


def find_counterexamples(
    pathfinder, scenarios: Sequence[tuple[NodeId, NodeId, float]], mode: str = "dynamic_weighted"
) -> list[dict]:
    raise NotImplementedError("TODO(P5)")
