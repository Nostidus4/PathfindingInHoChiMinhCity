"""Tìm ca A* cho kết quả tệ hơn Dijkstra (dùng cho dynamic_weighted). Owner: P5.

Chạy cả hai trên nhiều (start, goal, t), ghi lại ca cost_A* > cost_Dijkstra
để minh hoạ heuristic không admissible thì mất tối ưu.

Đáp án tối ưu lấy bằng `pathfinder.route(..., heuristic_mode="zero")`: A* với
h = 0 chính là Dijkstra. Việc nó trùng với cài đặt Dijkstra ĐỘC LẬP ở
search/dijkstra.py được khẳng định một lần bằng
tests/test_astar.py::test_zero_mode_matches_independent_dijkstra, nên ở đây chỉ
cần một interface duy nhất (pathfinder) thay vì nhận thêm graph + edge_cost.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from src.models import NodeId

# Chênh lệch tương đối phải vượt ngưỡng này mới tính là vi phạm, để sai số dấu
# phẩy động của hai thứ tự cộng khác nhau không bị báo thành phản ví dụ.
REL_TOL = 1e-9


def find_counterexamples(
    pathfinder, scenarios: Sequence[tuple[NodeId, NodeId, float]], mode: str = "dynamic_weighted"
) -> list[dict]:
    """Trả list dict mô tả các ca mà `mode` cho cost lớn hơn tối ưu.

    Mỗi dict luôn có astar_cost > optimal_cost. Cặp không có đường đi được bỏ
    qua (không kết luận được gì). Ca `mode` không tìm được đường dù tồn tại
    đường được ghi với astar_cost = inf.
    """
    out: list[dict] = []
    for start, goal, departure in scenarios:
        optimal = pathfinder.route(start, goal, departure, heuristic_mode="zero")
        if not optimal.found:
            continue
        candidate = pathfinder.route(start, goal, departure, heuristic_mode=mode)
        cost = candidate.total_cost if candidate.found else math.inf
        excess = cost - optimal.total_cost
        if excess <= REL_TOL * max(1.0, abs(optimal.total_cost)):
            continue
        out.append(
            {
                "start": start,
                "goal": goal,
                "departure": departure,
                "mode": mode,
                "astar_cost": cost,
                "optimal_cost": optimal.total_cost,
                "excess_s": excess,
                "excess_pct": 100.0 * excess / optimal.total_cost
                if optimal.total_cost > 0
                else math.inf,
                "astar_path": list(candidate.path),
                "optimal_path": list(optimal.path),
                "astar_expanded": candidate.expanded_nodes,
                "optimal_expanded": optimal.expanded_nodes,
            }
        )
    return out
