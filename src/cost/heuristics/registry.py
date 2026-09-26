"""Nhà máy heuristic: make_heuristic(mode, graph, bounds, params). Owner: P4.

HEURISTIC_MODES là danh sách mode hợp lệ (CLI, UI, experiments dùng danh sách này).
"""

from __future__ import annotations

from typing import Any

from src.cost.heuristics.dynamic_ub import DynamicUBHeuristic
from src.cost.heuristics.dynamic_weighted import DynamicWeightedHeuristic
from src.cost.heuristics.static_vmax import StaticVmaxHeuristic
from src.cost.heuristics.zero import ZeroHeuristic
from src.models import Heuristic

HEURISTIC_MODES: tuple[str, ...] = ("zero", "static_vmax", "dynamic_ub", "dynamic_weighted")


def make_heuristic(
    mode: str, graph, bounds=None, params: dict[str, Any] | None = None
) -> Heuristic:
    """Tạo heuristic object theo tên mode. Báo ValueError nếu mode không hợp lệ."""
    params = params or {}
    if mode == "zero":
        return ZeroHeuristic(graph)
    if mode == "static_vmax":
        return StaticVmaxHeuristic(graph, bounds)
    if mode == "dynamic_ub":
        return DynamicUBHeuristic(graph, bounds)
    if mode == "dynamic_weighted":
        return DynamicWeightedHeuristic(graph, bounds, w=params.get("w", 1.5))
    raise ValueError(f"Heuristic không hợp lệ: {mode!r}. Chọn một trong {HEURISTIC_MODES}")
