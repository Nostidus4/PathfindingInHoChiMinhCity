"""Kiểm tra graph, trả list lỗi (rỗng = OK). Owner: P2.

Thuần Python (không networkx) để chạy được khi chưa cài group data.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable

from src.geo import haversine_m
from src.graph.graph import Graph
from src.models import NodeId

_MAX_LISTED = 10


def _reachable(start: NodeId, step: Callable[[NodeId], list[NodeId]]) -> set[NodeId]:
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
    """Từ một node bất kỳ, đi xuôi và đi ngược đều phải tới được mọi node."""
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
    errors = []
    for p in graph.nodes():
        if not graph.get_neighbors(p.id):
            errors.append(f"Node {p.id} không có cạnh đi ra")
        if not graph.get_in_edges(p.id):
            errors.append(f"Node {p.id} không có cạnh đi vào")
    return errors


def check_length_vs_haversine(graph: Graph, tol_m: float = 1e-6) -> list[str]:
    """Mọi cạnh phải có length_m >= haversine (tol_m chỉ cho sai số dấu phẩy động)."""
    errors = []
    for e in graph.edges():
        a, b = graph.get_node(e.source), graph.get_node(e.target)
        d = haversine_m(a.lat, a.lon, b.lat, b.lon)
        if e.length_m + tol_m < d:
            errors.append(f"Cạnh {e.id}: length_m={e.length_m:.3f} < haversine={d:.3f}")
    return errors


def run_all_checks(graph: Graph) -> list[str]:
    return (
        check_strongly_connected(graph)
        + check_isolated_nodes(graph)
        + check_length_vs_haversine(graph)
    )
