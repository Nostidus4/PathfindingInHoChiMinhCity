"""SyntheticProvider: sinh giao thông giả lập, có seed để test tái lập. Owner: P3.

Nhiệm vụ:
- __init__(graph, cfg, seed): tính trước bảng TrafficState cho mọi edge x mốc lưới,
  thêm nhiễu ngẫu nhiên theo seed (cùng seed -> cùng kết quả).
- get_traffic(edge_id, t): nội suy giữa 2 mốc lưới gần nhất.
- Phải thoả FIFO (kiểm bằng validation/fifo.py).
"""

from __future__ import annotations

from src.config import SimConfig
from src.models import EdgeId, TrafficState
from src.traffic.base import BaseTrafficProvider


class SyntheticProvider(BaseTrafficProvider):
    def __init__(self, graph, cfg: SimConfig, seed: int | None = None) -> None:
        raise NotImplementedError("TODO(P3)")

    def get_traffic(self, edge_id: EdgeId, t: float) -> TrafficState:
        raise NotImplementedError("TODO(P3)")
