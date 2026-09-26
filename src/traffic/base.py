"""Interface TrafficProvider: get_traffic(edge_id, t) -> TrafficState. Owner: P3.

Protocol gốc nằm trong models.py (hợp đồng chung); file này re-export và
chứa lớp cơ sở tiện dụng cho các provider cụ thể.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models import EdgeId, TrafficProvider, TrafficState

__all__ = ["BaseTrafficProvider", "TrafficProvider"]


class BaseTrafficProvider(ABC):
    @abstractmethod
    def get_traffic(self, edge_id: EdgeId, t: float) -> TrafficState:
        """Trạng thái giao thông của cạnh edge_id tại thời điểm t (giây kể từ 00:00)."""
