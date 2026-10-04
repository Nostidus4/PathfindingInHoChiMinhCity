"""Sinh bộ kịch bản (start, goal, time). Owner: P6 (P1 chọn các cặp A/B).

- random_scenarios(graph, n, times, seed): ngẫu nhiên có seed.
- curated_scenarios(graph, times): CURATED_PAIRS x times, bỏ cặp có node không tồn tại.
- default_demo_pair(graph): cặp cho time demo (cặp curated đầu tiên, hoặc 2 POI xa nhau nhất
  mà có đường đi từ start tới goal).
- CURATED_PAIRS: các cặp A/B có ý nghĩa (P1 chọn, ví dụ Chợ Bến Thành -> Landmark 81).
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from itertools import permutations

from src.geo import haversine_m
from src.models import NodeId
from src.timeutil import parse_hhmm

Scenario = tuple[NodeId, NodeId, float]

# TODO(P1): điền các cặp (start_id, goal_id) có ý nghĩa
CURATED_PAIRS: list[tuple[NodeId, NodeId]] = []

DEFAULT_N_SCENARIOS = 120  # >= 100 cặp theo scope mục 4.1
DEFAULT_TIMES: tuple[float, ...] = tuple(
    parse_hhmm(t) for t in ("05:00", "07:30", "12:00", "17:30", "21:00")
)


def random_scenarios(graph, n: int, times: Sequence[float], seed: int = 42) -> list[Scenario]:
    """n kịch bản (start, goal, time) khác nhau, start != goal, tái lập được theo seed.

    Lấy mẫu không lặp trên toàn bộ tổ hợp, nên n lớn hơn số tổ hợp thì trả về tất cả.
    """
    if n < 0:
        raise ValueError("n phải >= 0")
    if not times:
        raise ValueError("Cần ít nhất một mốc giờ xuất phát")
    ids = sorted(p.id for p in graph.nodes())
    combos = [(s, g, float(t)) for s, g in permutations(ids, 2) for t in times]
    return random.Random(seed).sample(combos, min(n, len(combos)))


def curated_scenarios(graph, times: Sequence[float]) -> list[Scenario]:
    """CURATED_PAIRS x times, chỉ giữ cặp mà cả 2 node có trong graph."""
    ids = {p.id for p in graph.nodes()}
    return [(s, g, float(t)) for s, g in CURATED_PAIRS if s in ids and g in ids for t in times]


def _reachable(graph, start: NodeId) -> set[NodeId]:
    """Các node đi tới được từ start (BFS theo cạnh có hướng)."""
    seen, stack = {start}, [start]
    while stack:
        for seg in graph.get_neighbors(stack.pop()):
            if seg.target not in seen:
                seen.add(seg.target)
                stack.append(seg.target)
    return seen


def default_demo_pair(graph) -> tuple[NodeId, NodeId]:
    """Cặp A/B cho time demo: cặp curated hợp lệ đầu tiên, nếu không có thì 2 POI xa nhau nhất
    (haversine) mà goal đi tới được từ start."""
    nodes = sorted(graph.nodes(), key=lambda p: p.id)
    ids = {p.id for p in nodes}
    for s, g in CURATED_PAIRS:
        if s in ids and g in ids:
            return s, g
    reach = {p.id: _reachable(graph, p.id) for p in nodes}
    pairs = [(a, b) for a, b in permutations(nodes, 2) if b.id in reach[a.id]]
    if not pairs:
        raise ValueError("Graph không có cặp POI nào có đường đi")
    a, b = max(pairs, key=lambda ab: haversine_m(ab[0].lat, ab[0].lon, ab[1].lat, ab[1].lon))
    return a.id, b.id
