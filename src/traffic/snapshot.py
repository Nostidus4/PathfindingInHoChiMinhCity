"""RealSnapshotProvider: đọc dữ liệu real-time đã đóng băng (OPTIONAL). Owner: P3.

Đọc file trong data/snapshots/ (do scripts/survey_realtime.py tạo),
map về edge_id và trả TrafficState. Ngoài vùng có dữ liệu thì fallback về provider khác.
"""

from __future__ import annotations

from pathlib import Path

from src.models import EdgeId, TrafficProvider, TrafficState
from src.traffic.base import BaseTrafficProvider


class RealSnapshotProvider(BaseTrafficProvider):
    def __init__(self, snapshot_path: Path, fallback: TrafficProvider | None = None) -> None:
        raise NotImplementedError("TODO(P3)")

    def get_traffic(self, edge_id: EdgeId, t: float) -> TrafficState:
        raise NotImplementedError("TODO(P3)")
