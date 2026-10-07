"""Profile mật độ rho(e, t) theo thời gian (WP3.2). Owner: P3.

    rho(e, t) = clamp(base * (1 + P(t)) * f_road(e) * f_district(e) * noise(e), 0, 1)

- P(t): tổng các đỉnh Gaussian (sáng, trưa, chiều) lấy từ [peaks]; mượt nên traffic
  không nhảy đột ngột (cần cho FIFO).
- f_road: hệ số theo loại đường ([road_type_factor]).
- f_district: hệ số theo quận ([district_factor]).
- noise(e): hệ số cố định theo edge, sinh từ (seed, edge_id) trong [1 - eps, 1 + eps].

rho được tính tại các mốc lưới 15 phút rồi nội suy tuyến tính giữa các mốc (TimeGrid).
Tham số lấy từ SimConfig (configs/default.toml).
"""

from __future__ import annotations

import math
import random

from src.config import SimConfig
from src.models import EdgeId, RoadSegment
from src.traffic.timeslots import TimeGrid


def peak_multiplier(t: float, cfg: SimConfig) -> float:
    """P(t) = tổng a * exp(-(t - c)^2 / (2 sigma^2)) với sigma = width / 2."""
    total = 0.0
    for peak in cfg.peaks.values():
        sigma = peak.width_s / 2.0
        if sigma <= 0:
            continue
        z = (t - peak.center_s) / sigma
        total += peak.amplitude * math.exp(-0.5 * z * z)
    return total


def daily_profile(t: float, cfg: SimConfig) -> float:
    """Tỉ lệ mật độ nền theo giờ trong ngày: base * (1 + P(t)), chưa nhân hệ số edge."""
    return cfg.base_density_ratio * (1.0 + peak_multiplier(t, cfg))


def road_type_factor(segment: RoadSegment, cfg: SimConfig) -> float:
    return cfg.road_type_factor_for(segment.road_type)


def area_factor(segment: RoadSegment, cfg: SimConfig) -> float:
    return cfg.district_factor_for(segment.district)


def edge_noise_factor(edge_id: EdgeId, seed: int, noise: float) -> float:
    """Hệ số nhiễu cố định của một edge trong [1 - noise, 1 + noise].

    Sinh từ chuỗi "seed:edge_id" nên không phụ thuộc thứ tự duyệt edge hay PYTHONHASHSEED:
    cùng seed -> cùng hệ số, thêm edge mới không làm đổi hệ số của edge cũ.
    """
    if noise <= 0:
        return 1.0
    rng = random.Random(f"{seed}:{edge_id}")
    return 1.0 + rng.uniform(-noise, noise)


def density_ratio_at(
    segment: RoadSegment, t: float, cfg: SimConfig, noise_factor: float = 1.0
) -> float:
    """rho(e, t) tính trực tiếp từ công thức (không nội suy), clamp về [0, 1]."""
    rho = daily_profile(t, cfg) * road_type_factor(segment, cfg) * area_factor(segment, cfg)
    return min(max(rho * noise_factor, 0.0), 1.0)


def density_profile(
    segment: RoadSegment, cfg: SimConfig, noise_factor: float = 1.0, grid: TimeGrid | None = None
) -> tuple[float, ...]:
    """Bảng rho(e, t) tại mọi mốc của lưới (mặc định lưới từ cfg)."""
    grid = grid or TimeGrid.from_config(cfg)
    return tuple(density_ratio_at(segment, t, cfg, noise_factor) for t in grid.points())


def density_ratio(
    segment: RoadSegment, t: float, cfg: SimConfig, noise_factor: float = 1.0
) -> float:
    """rho(e, t) trong [0, 1], nội suy giữa các mốc lưới 15 phút, clamp ngoài cửa sổ."""
    grid = TimeGrid.from_config(cfg)
    i, frac = grid.get_time_slot(t)
    lo = density_ratio_at(segment, grid.start_s + i * grid.step_s, cfg, noise_factor)
    if frac == 0.0:
        return lo
    hi = density_ratio_at(segment, grid.start_s + (i + 1) * grid.step_s, cfg, noise_factor)
    return lo + frac * (hi - lo)
