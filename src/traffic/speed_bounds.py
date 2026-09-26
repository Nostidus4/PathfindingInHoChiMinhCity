"""Tính trước SpeedBounds cho heuristic. Owner: P3 (P4 dùng).

- v_max: tốc độ lớn nhất trên mọi edge x mọi thời điểm (km/h).
- v_ub(t): chặn trên phụ thuộc thời gian = suffix max theo thời gian
  (max tốc độ trên [t, hết cửa sổ]) rồi nội suy. Tính chất bắt buộc:
    * KHÔNG TĂNG theo t
    * >= tốc độ thật của mọi edge tại mọi thời điểm >= t
- v_mean(t): tốc độ trung bình tại t (cho dynamic_weighted).
P4 dùng object này thay vì gọi get_traffic hàng nghìn lần.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.config import SimConfig
from src.models import TrafficProvider


@dataclass(frozen=True)
class SpeedBounds:
    grid_start_s: float
    grid_step_s: int
    v_max_kmh: float
    v_ub_kmh: tuple[float, ...]  # suffix max trên lưới, không tăng
    v_mean_kmh: tuple[float, ...]

    def v_ub(self, t: float) -> float:
        """Chặn trên tốc độ từ thời điểm t trở đi (km/h)."""
        raise NotImplementedError("TODO(P3)")

    def v_mean(self, t: float) -> float:
        """Tốc độ trung bình tại t (km/h)."""
        raise NotImplementedError("TODO(P3)")


def compute_speed_bounds(graph, provider: TrafficProvider, cfg: SimConfig) -> SpeedBounds:
    """Quét mọi edge x mốc lưới, tính v_max, v_ub (suffix max), v_mean."""
    raise NotImplementedError("TODO(P3)")
