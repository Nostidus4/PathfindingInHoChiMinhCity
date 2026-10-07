"""Kiểm tính hợp lệ của TrafficState trên mọi edge x thời điểm (WP3.5). Owner: P3.

check_traffic_states trả danh sách vi phạm kèm edge_id và thời điểm cụ thể để dễ debug:
    - density >= 0, density <= k_jam (nếu truyền k_jam)
    - speed > 0
    - flow >= 0
    - flow ~ density * speed (quan hệ Greenshields)
    - flow <= capacity (để speed_model không phải phạt capacity)
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from src.models import TrafficProvider


def check_traffic_states(
    graph,
    provider: TrafficProvider,
    times: Sequence[float],
    k_jam: float | None = None,
    rel_tol: float = 1e-9,
) -> list[tuple[str, float, str]]:
    """Trả list (edge_id, t, mô tả lỗi). List rỗng nghĩa là mọi trạng thái hợp lệ."""
    problems: list[tuple[str, float, str]] = []
    for e in graph.edges():
        for t in times:
            s = provider.get_traffic(e.id, t)
            values = (s.density_veh_km, s.speed_kmh, s.flow_veh_h)
            if not all(math.isfinite(v) for v in values):
                problems.append((e.id, t, f"giá trị không hữu hạn: {s}"))
                continue
            if s.density_veh_km < 0:
                problems.append((e.id, t, f"density < 0: {s.density_veh_km}"))
            if k_jam is not None and s.density_veh_km > k_jam * (1 + rel_tol):
                problems.append((e.id, t, f"density > k_jam: {s.density_veh_km}"))
            if s.speed_kmh <= 0:
                problems.append((e.id, t, f"speed <= 0: {s.speed_kmh}"))
            if s.flow_veh_h < 0:
                problems.append((e.id, t, f"flow < 0: {s.flow_veh_h}"))
            expected = s.density_veh_km * s.speed_kmh
            if not math.isclose(s.flow_veh_h, expected, rel_tol=rel_tol, abs_tol=1e-9):
                problems.append((e.id, t, f"flow {s.flow_veh_h} != k*v {expected}"))
            if s.flow_veh_h > s.capacity_veh_h * (1 + rel_tol):
                problems.append((e.id, t, f"flow > capacity: {s.flow_veh_h}"))
    return problems
