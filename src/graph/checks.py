"""Kiểm tra tính đúng của đồ thị. Owner: P2.

Nhiệm vụ (trả list lỗi, rỗng = OK):
- Liên thông mạnh (mọi POI đi tới được mọi POI).
- Không có node cô lập.
- Mọi cạnh có length_m >= haversine(source, target) (điều kiện để heuristic admissible).
"""

from __future__ import annotations

from src.graph.graph import Graph


def check_strongly_connected(graph: Graph) -> list[str]:
    raise NotImplementedError("TODO(P2)")


def check_isolated_nodes(graph: Graph) -> list[str]:
    raise NotImplementedError("TODO(P2)")


def check_length_vs_haversine(graph: Graph, tol_m: float = 1.0) -> list[str]:
    raise NotImplementedError("TODO(P2)")


def run_all_checks(graph: Graph) -> list[str]:
    return (
        check_strongly_connected(graph)
        + check_isolated_nodes(graph)
        + check_length_vs_haversine(graph)
    )
