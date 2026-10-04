"""SyntheticProvider: sinh giao thông giả lập theo Greenshields, có seed để tái lập. Owner: P3.

- __init__(graph, cfg, seed): tính trước bảng rho(e, t) cho mọi edge x mốc lưới
  (profiles.density_profile), nhân hệ số nhiễu cố định theo edge (cùng seed -> cùng kết quả).
- get_traffic(edge_id, t): nội suy rho giữa 2 mốc lưới gần nhất (clamp ngoài cửa sổ),
  rồi đổi sang (k, v, q) bằng Greenshields => luôn có q = k * v và q <= capacity.
- Profile mượt nên thoả FIFO (kiểm bằng validation/fifo.py, tests/test_fifo.py).
"""

from __future__ import annotations

from dataclasses import dataclass

from src.config import SimConfig
from src.models import EdgeId, TrafficState
from src.traffic import greenshields
from src.traffic.base import BaseTrafficProvider
from src.traffic.profiles import density_profile, edge_noise_factor
from src.traffic.timeslots import TimeGrid, interpolate_on_grid


@dataclass(frozen=True, slots=True)
class _EdgeProfile:
    v_free_kmh: float
    noise_factor: float
    rho: tuple[float, ...]  # rho tại từng mốc lưới


class SyntheticProvider(BaseTrafficProvider):
    def __init__(self, graph, cfg: SimConfig, seed: int | None = None) -> None:
        self.cfg = cfg
        self.seed = cfg.seed if seed is None else seed
        self.grid = TimeGrid.from_config(cfg)
        self._profiles: dict[EdgeId, _EdgeProfile] = {}
        for e in graph.edges():
            noise = edge_noise_factor(e.id, self.seed, cfg.edge_noise)
            self._profiles[e.id] = _EdgeProfile(
                v_free_kmh=cfg.free_flow_for(e.road_type),
                noise_factor=noise,
                rho=density_profile(e, cfg, noise, self.grid),
            )

    def _profile(self, edge_id: EdgeId) -> _EdgeProfile:
        try:
            return self._profiles[edge_id]
        except KeyError:
            raise KeyError(f"Edge {edge_id!r} không có trong graph của SyntheticProvider") from None

    def get_density_ratio(self, edge_id: EdgeId, t: float) -> float:
        """rho(e, t) trong [0, 1] (đã gồm nhiễu của edge), nội suy trên lưới 15 phút."""
        p = self._profile(edge_id)
        return interpolate_on_grid(p.rho, self.grid.start_s, self.grid.step_s, t)

    def get_traffic(self, edge_id: EdgeId, t: float) -> TrafficState:
        p = self._profile(edge_id)
        rho = interpolate_on_grid(p.rho, self.grid.start_s, self.grid.step_s, t)
        return greenshields.state_from_ratio(
            rho, p.v_free_kmh, self.cfg.k_jam_veh_km, self.cfg.min_speed_kmh
        )

    def speed_table(self) -> dict[EdgeId, tuple[float, ...]]:
        """traffic_speed_table: tốc độ (km/h) của từng edge tại từng mốc lưới."""
        k_jam, v_min = self.cfg.k_jam_veh_km, self.cfg.min_speed_kmh
        return {
            edge_id: tuple(
                greenshields.speed(
                    greenshields.density_from_ratio(r, k_jam), p.v_free_kmh, k_jam, v_min
                )
                for r in p.rho
            )
            for edge_id, p in self._profiles.items()
        }
