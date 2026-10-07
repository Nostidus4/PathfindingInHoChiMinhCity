"""Kiểm tra đầu vào dùng chung cho search/ và validation/. Owner: P5.

Engine A*/Dijkstra nhận `edge_cost` và `heuristic` từ bên ngoài, nên phải tự
phòng vệ: một provider trả NaN, số âm hay sai endpoint sẽ làm thuật toán cho
kết quả sai *mà không báo lỗi*. Các hàm ở đây biến lỗi dữ liệu thành ValueError
ngay tại chỗ phát sinh để WP3/WP4 sửa được provider.

Quy ước đơn vị (xem models.py): thời gian = giây, thời điểm = giây kể từ 00:00,
chiều dài = mét. `+inf` là giá trị hợp lệ DUY NHẤT của edge_cost, nghĩa là
"cạnh bị chặn tại thời điểm này".
"""

from __future__ import annotations

import math
from collections.abc import Callable

from src.models import NodeId, RoadSegment

EdgeCostFn = Callable[[RoadSegment, float], float]
HeuristicFn = Callable[[NodeId, NodeId, float], float]


def nonnegative(value: float, name: str, *, allow_infinity: bool = False) -> float:
    """Trả float(value) nếu hợp lệ, ngược lại ValueError.

    NaN luôn bị loại: NaN lặng lẽ phá vỡ mọi so sánh trong heap. `+inf` chỉ được
    chấp nhận khi allow_infinity=True (dùng cho edge_cost của cạnh bị chặn).
    """
    v = float(value)
    if math.isnan(v) or v < 0.0 or (not allow_infinity and math.isinf(v)):
        yeu_cau = "không phải NaN" if allow_infinity else "hữu hạn"
        raise ValueError(f"{name} phải không âm và {yeu_cau}, nhận được {value!r}")
    return v


def node_ids(graph) -> set[NodeId]:
    """Tập ID node của graph. `graph.nodes()` trả POI nên phải lấy `.id`."""
    return {p.id for p in graph.nodes()}


def check_query(ids: set[NodeId], start: NodeId, goal: NodeId, departure_time: float) -> float:
    """Kiểm start/goal có trong graph và departure_time hợp lệ. Trả departure_time."""
    for ten, node in (("start", start), ("goal", goal)):
        if node not in ids:
            raise ValueError(f"{ten} {node!r} không có trong graph")
    return nonnegative(departure_time, "departure_time")


def checked_edge(ids: set[NodeId], segment: RoadSegment, current: NodeId) -> None:
    """Kiểm get_neighbors() thật sự trả cạnh ĐI RA từ current và endpoint tồn tại.

    Bắt được hai lỗi hay gặp khi nối graph thật: graph trả cả cạnh đi vào (làm
    A* đi ngược chiều) và graph trả cạnh tới node không nằm trong nodes().
    """
    if segment.source != current:
        raise ValueError(
            f"get_neighbors({current!r}) trả cạnh {segment.id!r} có source={segment.source!r}: "
            "chỉ được trả cạnh đi ra"
        )
    if segment.target not in ids:
        raise ValueError(
            f"Cạnh {segment.id!r} trỏ tới node {segment.target!r} không có trong graph"
        )
    nonnegative(segment.length_m, f"RoadSegment({segment.id!r}).length_m")
