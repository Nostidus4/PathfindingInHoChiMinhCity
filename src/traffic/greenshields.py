"""Mô hình Greenshields - các hàm THUẦN (không state). Owner: P3.

    k = k_jam * rho                 (rho = k / k_jam trong [0, 1])
    v(k) = v_free * (1 - k / k_jam) (chặn dưới v_min để thời gian đi không vô hạn)
    q(k) = k * v(k)                 (luôn đảm bảo q = k * v, kể cả khi bị chặn v_min)
    capacity = v_free * k_jam / 4   (tại k = k_jam / 2)
Đơn vị: km/h, veh/km, veh/h.
"""

from __future__ import annotations

from src.models import TrafficState


def _check_params(v_free: float, k_jam: float) -> None:
    if v_free <= 0:
        raise ValueError(f"v_free phải > 0, nhận {v_free}")
    if k_jam <= 0:
        raise ValueError(f"k_jam phải > 0, nhận {k_jam}")


def speed(density: float, v_free: float, k_jam: float, v_min: float = 0.0) -> float:
    """Tốc độ (km/h) theo mật độ, chặn dưới v_min. Mật độ ngoài [0, k_jam] bị clamp."""
    _check_params(v_free, k_jam)
    ratio = min(max(density / k_jam, 0.0), 1.0)
    return max(v_min, v_free * (1.0 - ratio))


def flow(density: float, v_free: float, k_jam: float, v_min: float = 0.0) -> float:
    """Lưu lượng q = k * v (veh/h)."""
    return max(density, 0.0) * speed(density, v_free, k_jam, v_min)


def capacity(v_free: float, k_jam: float) -> float:
    """Lưu lượng cực đại (veh/h)."""
    _check_params(v_free, k_jam)
    return v_free * k_jam / 4.0


def density_from_ratio(ratio: float, k_jam: float) -> float:
    """Mật độ từ tỉ lệ rho = k / k_jam (clamp về [0, 1])."""
    if k_jam <= 0:
        raise ValueError(f"k_jam phải > 0, nhận {k_jam}")
    return k_jam * min(max(ratio, 0.0), 1.0)


def state_from_ratio(ratio: float, v_free: float, k_jam: float, v_min: float = 0.0) -> TrafficState:
    """TrafficState nhất quán (k, v, q, capacity) từ tỉ lệ mật độ rho."""
    k = density_from_ratio(ratio, k_jam)
    v = speed(k, v_free, k_jam, v_min)
    return TrafficState(
        density_veh_km=k,
        speed_kmh=v,
        flow_veh_h=k * v,
        capacity_veh_h=capacity(v_free, k_jam),
    )
