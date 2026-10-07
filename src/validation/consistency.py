"""Kiểm consistency: h(u, t) <= c(u, v, t) + h(v, t + c). Owner: P5.

Quét mọi edge x lưới thời gian (GRID_STEP), trả list vi phạm.

Kiểm cả điều kiện biên h(goal, t) = 0: thiếu nó thì h có thể "consistent" trên
mọi cạnh mà A* vẫn dừng sai ở goal.

Chú ý h(v, ...) được tính tại t + c, tức THỜI ĐIỂM ĐẾN v, đúng như A* gọi nó
(xem search/astar.py). Dùng h(v, t) sẽ kiểm một bất đẳng thức khác, không liên
quan tới tính đúng của engine.

Giống admissibility: đây là bằng chứng lấy mẫu trên lưới thời gian rời rạc,
giữa hai mốc 15 phút c(e, t) vẫn có thể cong.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from src.models import Heuristic, NodeId
from src.search.contracts import node_ids, nonnegative

# Nhãn thay cho edge_id ở các vi phạm điều kiện biên h(goal, t) = 0.
GOAL_CHECK = "h(goal,t)"


def check_consistency(
    graph,
    heuristic: Heuristic,
    edge_cost,
    goals: Sequence[NodeId],
    times: Sequence[float],
    tol: float = 1e-6,
) -> list[tuple]:
    """Trả list (edge_id, goal, t, h_u, c, h_v) với h_u > c + h_v + tol.

    Vi phạm điều kiện biên có dạng (GOAL_CHECK, goal, t, h_goal, 0.0, 0.0).
    Cạnh bị chặn (+inf) tại t được bỏ qua: A* cũng không đi qua nó lúc đó.
    """
    ids = node_ids(graph)
    goals = list(goals)
    times = [nonnegative(t, "time") for t in times]
    if not goals or not times:
        raise ValueError("check_consistency cần ít nhất một goal và một mốc thời gian")
    for goal in goals:
        if goal not in ids:
            raise ValueError(f"goal {goal!r} không có trong graph")
    tol = nonnegative(tol, "tol")

    edges = list(graph.edges())
    violations: list[tuple] = []
    for goal in goals:
        for t in times:
            h_goal = nonnegative(heuristic(goal, goal, t), f"heuristic({goal!r}, {goal!r}, {t})")
            if h_goal > tol:
                violations.append((GOAL_CHECK, goal, t, h_goal, 0.0, 0.0))
            for segment in edges:
                c = nonnegative(
                    edge_cost(segment, t), f"edge_cost({segment.id!r}, {t})", allow_infinity=True
                )
                if math.isinf(c):
                    continue
                h_u = nonnegative(heuristic(segment.source, goal, t), "heuristic")
                h_v = nonnegative(heuristic(segment.target, goal, t + c), "heuristic")
                if h_u > c + h_v + tol:
                    violations.append((segment.id, goal, t, h_u, c, h_v))
    return violations
