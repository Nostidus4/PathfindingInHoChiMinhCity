"""Kiểm admissibility: h(n, t) <= chi phí tối ưu thật (true_cost). Owner: P5.

Quét nhiều node x goal x mốc giờ, trả list vi phạm (node, goal, t, h, true).

!!! Đây là BẰNG CHỨNG LẤY MẪU, không phải chứng minh. List rỗng chỉ có nghĩa
"không tìm thấy vi phạm trên các mẫu đã quét", không khẳng định admissible với
mọi thời điểm liên tục. Chứng minh toán nằm ở docs/heuristic_proof.md.

Cặp (node, goal) KHÔNG đi tới được bị bỏ qua: chi phí thật là +inf nên mọi h hữu
hạn đều admissible, đưa vào chỉ làm loãng số liệu. Nếu không có cặp nào đi tới
được thì hàm báo ValueError thay vì trả list rỗng — "đạt với 0 mẫu" là kết luận sai.
"""

from __future__ import annotations

from collections.abc import Sequence

from src.models import Heuristic, NodeId
from src.search.contracts import node_ids, nonnegative
from src.search.dijkstra import earliest_arrival_times


def check_admissibility(
    graph,
    heuristic: Heuristic,
    edge_cost,
    goals: Sequence[NodeId],
    times: Sequence[float],
    tol: float = 1e-6,
) -> list[tuple]:
    """Trả list (node, goal, t, h, true) với h > true + tol.

    Chỉ cần |nodes| x |times| lần Dijkstra: mỗi lần quét cho ra chi phí tối ưu
    tới MỌI goal cùng lúc (earliest_arrival_times), không phải một lần mỗi goal.
    """
    ids = node_ids(graph)
    goals = list(goals)
    times = [nonnegative(t, "time") for t in times]
    if not goals or not times:
        raise ValueError("check_admissibility cần ít nhất một goal và một mốc thời gian")
    for goal in goals:
        if goal not in ids:
            raise ValueError(f"goal {goal!r} không có trong graph")
    tol = nonnegative(tol, "tol")

    nodes = sorted(ids)
    violations: list[tuple] = []
    checked = 0
    for t in times:
        for node in nodes:
            reachable = earliest_arrival_times(graph, node, t, edge_cost)
            for goal in goals:
                true = reachable.get(goal)
                if true is None:
                    continue  # không có đường -> true = +inf -> mọi h đều hợp lệ
                h = nonnegative(heuristic(node, goal, t), f"heuristic({node!r}, {goal!r}, {t})")
                checked += 1
                if h > true + tol:
                    violations.append((node, goal, t, h, true))
    if checked == 0:
        raise ValueError(
            "Không có cặp (node, goal) nào đi tới được trên các mốc đã quét: "
            "kiểm tra lại graph (liên thông) hoặc danh sách goals"
        )
    return violations
