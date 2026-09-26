"""Profile mật độ rho(e, t) theo thời gian. Owner: P3.

rho(e, t) = base * (1 + tổng các đỉnh giờ cao điểm(t)) * hệ số loại đường * hệ số quận,
tính trên lưới 15 phút rồi nội suy tuyến tính giữa các mốc.
Tham số lấy từ SimConfig (configs/default.toml).
"""

from __future__ import annotations

from src.config import SimConfig
from src.models import RoadSegment


def peak_multiplier(t: float, cfg: SimConfig) -> float:
    """Hệ số giờ cao điểm tại t (tổng các đỉnh Gaussian/tam giác)."""
    raise NotImplementedError("TODO(P3)")


def density_ratio(segment: RoadSegment, t: float, cfg: SimConfig) -> float:
    """rho(e, t) trong [0, 1], nội suy giữa các mốc lưới 15 phút."""
    raise NotImplementedError("TODO(P3)")
