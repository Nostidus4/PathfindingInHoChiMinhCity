"""Tính trước SpeedBounds cho heuristic (WP3.4 aggregate). Owner: P3 (P4 dùng).

- v_max: tốc độ lớn nhất trên mọi edge x mọi thời điểm (km/h).
- v_ub(t): chặn trên phụ thuộc thời gian = suffix max theo thời gian
  (max tốc độ trên [t, hết cửa sổ]) rồi nội suy. Tính chất bắt buộc:
    * KHÔNG TĂNG theo t
    * >= tốc độ thật của mọi edge tại mọi thời điểm >= t
- v_mean(t): tốc độ trung bình tại t (cho dynamic_weighted).
- network_max_speed(t): max tốc độ trên mạng tại đúng thời điểm t (không suffix),
  dùng cho báo cáo / so sánh độ chặt của v_ub.
P4 dùng object này thay vì gọi get_traffic hàng nghìn lần.

Vì sao v_ub nội suy vẫn là chặn trên giữa hai mốc: với SyntheticProvider, tốc độ mỗi edge
trong một ô lưới là max(v_min, hàm tuyến tính theo t), tức là hàm lồi, nên nằm dưới dây cung
nối hai mốc; dây cung đó lại nằm dưới nội suy của suffix max (xem docs/traffic_model.md §6).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from src.config import SimConfig
from src.models import RoadSegment, TrafficProvider, TrafficState
from src.traffic.timeslots import TimeGrid, interpolate_on_grid

SpeedFn = Callable[[TrafficState, RoadSegment], float]


@dataclass(frozen=True)
class SpeedBounds:
    grid_start_s: float
    grid_step_s: int
    v_max_kmh: float
    v_ub_kmh: tuple[float, ...]  # suffix max trên lưới, không tăng
    v_mean_kmh: tuple[float, ...]
    v_now_max_kmh: tuple[float, ...] = ()  # max toàn mạng tại từng mốc (network_max_speed)

    def v_ub(self, t: float) -> float:
        """Chặn trên tốc độ từ thời điểm t trở đi (km/h)."""
        return interpolate_on_grid(self.v_ub_kmh, self.grid_start_s, self.grid_step_s, t)

    def v_mean(self, t: float) -> float:
        """Tốc độ trung bình tại t (km/h)."""
        return interpolate_on_grid(self.v_mean_kmh, self.grid_start_s, self.grid_step_s, t)

    def network_max_speed(self, t: float) -> float:
        """Tốc độ lớn nhất trên mạng tại t (km/h), không lấy suffix max."""
        return interpolate_on_grid(self.v_now_max_kmh, self.grid_start_s, self.grid_step_s, t)

    def grid_times(self) -> list[float]:
        """Các mốc thời gian (giây) ứng với từng phần tử của bảng."""
        return [self.grid_start_s + i * self.grid_step_s for i in range(len(self.v_ub_kmh))]


def _state_speed(state: TrafficState, segment: RoadSegment) -> float:
    return state.speed_kmh


def compute_speed_bounds(
    graph, provider: TrafficProvider, cfg: SimConfig, speed_fn: SpeedFn | None = None
) -> SpeedBounds:
    """Quét mọi edge x mốc lưới, tính v_max, v_ub (suffix max), v_mean.

    speed_fn(state, segment) -> km/h cho phép dùng tốc độ hiệu dụng khác state.speed_kmh.
    Mặc định dùng state.speed_kmh; với SyntheticProvider điều này trùng với v_eff của
    cost/speed_model.py vì Greenshields luôn cho flow <= capacity (không bị phạt).
    """
    speed_of = speed_fn or _state_speed
    edges = list(graph.edges())
    if not edges:
        raise ValueError("Graph không có edge nào để tính SpeedBounds")
    grid = TimeGrid.from_config(cfg)

    now_max: list[float] = []
    mean: list[float] = []
    for t in grid.points():
        speeds = [float(speed_of(provider.get_traffic(e.id, t), e)) for e in edges]
        now_max.append(max(speeds))
        mean.append(sum(speeds) / len(speeds))

    suffix = now_max[:]
    for i in range(len(suffix) - 2, -1, -1):
        suffix[i] = max(suffix[i], suffix[i + 1])

    return SpeedBounds(
        grid_start_s=grid.start_s,
        grid_step_s=grid.step_s,
        v_max_kmh=suffix[0],
        v_ub_kmh=tuple(suffix),
        v_mean_kmh=tuple(mean),
        v_now_max_kmh=tuple(now_max),
    )
