"""Kiểm tra tính đúng của đồ thị. Owner: P2.

Nhiệm vụ (trả list lỗi, rỗng = OK):
- Liên thông mạnh (mọi POI đi tới được mọi POI).
- Không có node cô lập.
- Mọi cạnh có length_m >= haversine(source, target) (điều kiện để heuristic admissible).
Viết thuần Python (không dùng networkx) để chạy được khi chưa cài group data.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable

from src.geo import haversine_m
from src.graph.graph import Graph
from src.models import NodeId

_MAX_LISTED = 10


def _reachable(start: NodeId, step: Callable[[NodeId], list[NodeId]]) -> set[NodeId]:
    """BFS từ start, step(node) trả danh sách node kề."""
    seen = {start}
    queue = deque([start])
    while queue:
        u = queue.popleft()
        for v in step(u):
            if v not in seen:
                seen.add(v)
                queue.append(v)
    return seen


def _short_list(ids: list[NodeId]) -> str:
    shown = ", ".join(ids[:_MAX_LISTED])
    return shown + (f", ... (+{len(ids) - _MAX_LISTED})" if len(ids) > _MAX_LISTED else "")


def check_strongly_connected(graph: Graph) -> list[str]:
    """Liên thông mạnh <=> từ một node bất kỳ, đi xuôi và đi ngược đều tới được mọi node."""
    ids = [p.id for p in graph.nodes()]
    if not ids:
        return ["Đồ thị rỗng"]
    root = ids[0]
    forward = _reachable(root, lambda u: [e.target for e in graph.get_neighbors(u)])
    backward = _reachable(root, lambda u: [e.source for e in graph.get_in_edges(u)])
    errors = []
    missed_fwd = sorted(n for n in ids if n not in forward)
    missed_bwd = sorted(n for n in ids if n not in backward)
    if missed_fwd:
        errors.append(
            f"Không đi được từ {root} tới {len(missed_fwd)} node: {_short_list(missed_fwd)}"
        )
    if missed_bwd:
        errors.append(f"{len(missed_bwd)} node không đi được tới {root}: {_short_list(missed_bwd)}")
    return errors


def check_isolated_nodes(graph: Graph) -> list[str]:
    """Node không có cạnh ra hoặc không có cạnh vào."""
    errors = []
    for p in graph.nodes():
        if not graph.get_neighbors(p.id):
            errors.append(f"Node {p.id} không có cạnh đi ra")
        if not graph.get_in_edges(p.id):
            errors.append(f"Node {p.id} không có cạnh đi vào")
    return errors


def check_length_vs_haversine(graph: Graph, tol_m: float = 1.0) -> list[str]:
    """Mọi cạnh phải có length_m >= khoảng cách chim bay giữa 2 đầu (sai số tol_m)."""
    errors = []
    for e in graph.edges():
        a, b = graph.get_node(e.source), graph.get_node(e.target)
        d = haversine_m(a.lat, a.lon, b.lat, b.lon)
        if e.length_m + tol_m < d:
            errors.append(f"Cạnh {e.id}: length_m={e.length_m:.1f} < haversine={d:.1f}")
    return errors


def run_all_checks(graph: Graph) -> list[str]:
    return (
        check_strongly_connected(graph)
        + check_isolated_nodes(graph)
        + check_length_vs_haversine(graph)
    )
