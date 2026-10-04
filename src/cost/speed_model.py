"""Tốc độ hiệu dụng của một cạnh. Owner: P4.

effective_speed(state, segment): dùng tốc độ traffic do provider cung cấp và
áp penalty khi flow vượt capacity, trả tốc độ theo m/s.

!!! ĐÂY LÀ NƠI DUY NHẤT ĐỔI ĐƠN VỊ (km/h -> m/s). Các module khác không tự đổi.
"""

from __future__ import annotations

import math

from src.models import RoadSegment, TrafficState

KMH_TO_MS = 1000.0 / 3600.0
# Tránh chia cho 0 trong edge_cost. Giá trị này chỉ dùng cho trạng thái lỗi/jam
# tuyệt đối; SyntheticProvider bình thường đã chặn tốc độ bằng min_speed_kmh.
MIN_EFFECTIVE_SPEED_MS = 1e-6


def kmh_to_ms(v_kmh: float) -> float:
    """Đổi km/h sang m/s.

    Hàm conversion nằm ở module này để giữ quy ước của project: không module
    cost/heuristics nào tự nhân/chia 3.6.
    """
    return v_kmh * KMH_TO_MS


def effective_speed(state: TrafficState, segment: RoadSegment) -> float:
    """Tính tốc độ hiệu dụng (m/s) trên ``segment`` tại một traffic state.

    ``TrafficState.speed_kmh`` là tốc độ traffic đã được provider (P3) tính từ
    density/profile. P4 không chạy lại Greenshields ở đây, nếu không cùng một
    ảnh hưởng của density sẽ bị tính hai lần.

    Nếu ``flow_veh_h`` vượt ``capacity_veh_h``, tốc độ được giảm theo tỉ lệ
    ``capacity / flow``. Khi flow <= capacity (hoặc capacity = +inf, như mock),
    tốc độ được giữ nguyên.

    ``segment`` hiện chưa làm thay đổi công thức vì capacity trong
    ``TrafficState`` được hiểu là capacity của chính edge đó. Tham số vẫn nằm
    trong API để cost model có thể mở rộng theo road type/lanes mà không đổi
    interface.
    """
    del segment  # API intentionally keeps the edge for future road-specific models.

    speed_kmh = max(float(state.speed_kmh), 0.0)
    flow = max(float(state.flow_veh_h), 0.0)
    capacity = float(state.capacity_veh_h)

    if math.isfinite(capacity):
        if capacity <= 0.0:
            speed_kmh = 0.0
        elif flow > capacity:
            speed_kmh *= capacity / flow

    return max(kmh_to_ms(speed_kmh), MIN_EFFECTIVE_SPEED_MS)
