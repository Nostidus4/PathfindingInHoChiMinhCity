"""Hợp đồng chung (interfaces-v1) cho cả nhóm. Owner: P6 + P5.

File này định nghĩa các kiểu dữ liệu mà MỌI work package dùng chung:
POI, RoadSegment, TrafficState, CostMode, TraceStep, RouteResult
và các Protocol TrafficProvider, Heuristic.

!!! Đổi file này phải có PR và đủ owner review. Sau tag `interfaces-v1` thì đóng băng.

Đơn vị chốt một lần:
    - TrafficState: tốc độ km/h, mật độ veh/km, lưu lượng veh/h
    - Thời gian: giây (thời điểm = giây kể từ 00:00, xem timeutil.py)
    - Chiều dài: mét
Chỉ cost/speed_model.py được phép đổi đơn vị.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol, runtime_checkable

NodeId = str
EdgeId = str
LatLon = tuple[float, float]


@dataclass(frozen=True, slots=True)
class POI:
    """Một điểm quan tâm = một node của đồ thị (ngã tư hoặc landmark)."""

    id: NodeId
    name: str
    lat: float
    lon: float
    district: str
    kind: str = "intersection"  # "landmark" | "intersection" | "junction"


@dataclass(frozen=True, slots=True)
class RoadSegment:
    """Một cạnh có hướng giữa 2 POI (đường ngắn nhất trên mạng OSM giữa chúng)."""

    id: EdgeId
    source: NodeId
    target: NodeId
    length_m: float
    road_type: str = "default"  # highway tag OSM: primary, secondary, ...
    district: str = ""
    name: str = ""
    lanes: int = 1
    geometry: tuple[LatLon, ...] = ()  # polyline thật để vẽ bản đồ (T1)


@dataclass(frozen=True, slots=True)
class TrafficState:
    """Trạng thái giao thông của một cạnh tại một thời điểm."""

    density_veh_km: float
    speed_kmh: float
    flow_veh_h: float
    capacity_veh_h: float = float("inf")


class CostMode(StrEnum):
    """Chi phí cạnh: TIME (giây, mode chính) hoặc DISTANCE (mét, baseline phụ)."""

    TIME = "time"
    DISTANCE = "distance"


@dataclass(frozen=True, slots=True)
class TraceStep:
    """Một bước của A* dùng để in giải thích thuật toán (search/trace.py)."""

    step: int
    node: NodeId
    g: float  # chi phí từ start (giây)
    h: float  # heuristic tới goal (giây)
    t: float  # thời điểm đến node (giây kể từ 00:00)
    action: str = "expand"  # "expand" | "push" | "update" | "skip"
    open_size: int = 0
    note: str = ""

    @property
    def f(self) -> float:
        return self.g + self.h


@dataclass(slots=True)
class RouteResult:
    """Kết quả một lần tìm đường. found=False nghĩa là không có đường (no-path)."""

    found: bool
    path: list[NodeId]
    edges: list[EdgeId]
    departure_time_s: float
    arrival_time_s: float
    total_cost: float  # giây nếu CostMode.TIME, mét nếu CostMode.DISTANCE
    expanded_nodes: int
    total_distance_m: float = 0.0  # tổng chiều dài route (mét), luôn tính dù cost mode nào
    runtime_ms: float = 0.0
    heuristic_mode: str = ""
    cost_mode: CostMode = CostMode.TIME
    trace: list[TraceStep] = field(default_factory=list)

    @property
    def travel_time_s(self) -> float:
        return self.arrival_time_s - self.departure_time_s


@runtime_checkable
class TrafficProvider(Protocol):
    """Nguồn dữ liệu giao thông: trả trạng thái của cạnh edge_id tại thời điểm t (giây)."""

    def get_traffic(self, edge_id: EdgeId, t: float) -> TrafficState: ...


@runtime_checkable
class Heuristic(Protocol):
    """Heuristic là OBJECT (tạo 1 lần qua make_heuristic), gọi h(node, goal, t) -> giây."""

    def __call__(self, node: NodeId, goal: NodeId, t: float) -> float: ...
