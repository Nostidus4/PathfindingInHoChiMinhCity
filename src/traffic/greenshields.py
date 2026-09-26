"""Mô hình Greenshields - các hàm THUẦN (không state). Owner: P3.

    v(k) = v_free * (1 - k / k_jam)
    q(k) = k * v(k)                 (luôn đảm bảo q = k * v)
    capacity = v_free * k_jam / 4   (tại k = k_jam / 2)
Đơn vị: km/h, veh/km, veh/h.
"""

from __future__ import annotations


def speed(density: float, v_free: float, k_jam: float, v_min: float = 0.0) -> float:
    """Tốc độ (km/h) theo mật độ, chặn dưới v_min."""
    raise NotImplementedError("TODO(P3)")


def flow(density: float, v_free: float, k_jam: float) -> float:
    """Lưu lượng q = k * v (veh/h)."""
    raise NotImplementedError("TODO(P3)")


def capacity(v_free: float, k_jam: float) -> float:
    """Lưu lượng cực đại (veh/h)."""
    raise NotImplementedError("TODO(P3)")


def density_from_ratio(ratio: float, k_jam: float) -> float:
    """Mật độ từ tỉ lệ rho = k / k_jam (clamp về [0, 1])."""
    raise NotImplementedError("TODO(P3)")
