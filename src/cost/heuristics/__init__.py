"""4 heuristic đã chốt: zero, static_vmax, dynamic_ub, dynamic_weighted.

Heuristic là OBJECT: tạo một lần bằng registry.make_heuristic(...), tính trước
SpeedBounds bên trong, sau đó gọi h(node, goal, t) -> giây, chạy nhanh.
"""

from src.cost.heuristics.registry import HEURISTIC_MODES, make_heuristic

__all__ = ["HEURISTIC_MODES", "make_heuristic"]
