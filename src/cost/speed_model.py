"""Tốc độ hiệu dụng của một cạnh. Owner: P4.

effective_speed(state, segment): kết hợp density và flow, giới hạn bởi capacity,
trả tốc độ theo m/s.

!!! ĐÂY LÀ NƠI DUY NHẤT ĐỔI ĐƠN VỊ (km/h -> m/s). Các module khác không tự đổi.
"""

from __future__ import annotations

from src.models import RoadSegment, TrafficState

KMH_TO_MS = 1000.0 / 3600.0


def kmh_to_ms(v_kmh: float) -> float:
    return v_kmh * KMH_TO_MS


def effective_speed(state: TrafficState, segment: RoadSegment) -> float:
    """Tốc độ hiệu dụng (m/s) trên segment khi giao thông ở trạng thái state."""
    raise NotImplementedError("TODO(P4)")
