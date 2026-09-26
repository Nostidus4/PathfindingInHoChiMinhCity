"""Sinh bộ kịch bản (start, goal, time). Owner: P6 (P1 chọn các cặp A/B).

- random_scenarios(graph, n, times, seed): ngẫu nhiên có seed.
- CURATED_PAIRS: các cặp A/B có ý nghĩa (P1 chọn, ví dụ Chợ Bến Thành -> Landmark 81).
"""

from __future__ import annotations

from collections.abc import Sequence

from src.models import NodeId

Scenario = tuple[NodeId, NodeId, float]

# TODO(P1): điền các cặp (start_id, goal_id) có ý nghĩa
CURATED_PAIRS: list[tuple[NodeId, NodeId]] = []


def random_scenarios(graph, n: int, times: Sequence[float], seed: int = 42) -> list[Scenario]:
    raise NotImplementedError("TODO(P6)")
