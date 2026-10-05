"""SimConfig: đọc tham số mô phỏng từ configs/default.toml.

Chứa: cửa sổ mô phỏng, tham số Greenshields, đỉnh giờ cao điểm, hệ số loại đường,
hệ số quận, nhiễu theo edge, trọng số w của dynamic_weighted, seed. Mọi module lấy tham số từ đây,
KHÔNG hard-code số trong code.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from src.timeutil import GRID_STEP, parse_hhmm

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "default.toml"


@dataclass(frozen=True, slots=True)
class PeakConfig:
    center_s: float
    width_s: float
    amplitude: float


@dataclass(frozen=True, slots=True)
class SimConfig:
    seed: int = 42
    window_start_s: float = parse_hhmm("05:00")
    window_end_s: float = parse_hhmm("23:00")
    grid_step_s: int = GRID_STEP
    k_jam_veh_km: float = 150.0
    min_speed_kmh: float = 5.0
    free_flow_kmh: dict[str, float] = field(default_factory=lambda: {"default": 30.0})
    peaks: dict[str, PeakConfig] = field(default_factory=dict)
    base_density_ratio: float = 0.2
    road_type_factor: dict[str, float] = field(default_factory=lambda: {"default": 1.0})
    district_factor: dict[str, float] = field(default_factory=dict)
    edge_noise: float = 0.0
    default_heuristic: str = "dynamic_ub"
    weight_w: float = 1.5

    def free_flow_for(self, road_type: str) -> float:
        """Tốc độ tự do (km/h) theo loại đường, fallback về 'default'."""
        return self.free_flow_kmh.get(road_type, self.free_flow_kmh.get("default", 30.0))

    def road_type_factor_for(self, road_type: str) -> float:
        """Hệ số nhân mật độ theo loại đường, fallback về 'default' (hoặc 1.0)."""
        return self.road_type_factor.get(road_type, self.road_type_factor.get("default", 1.0))

    def district_factor_for(self, district: str) -> float:
        """Hệ số nhân mật độ theo quận, quận không có trong bảng dùng 1.0."""
        return self.district_factor.get(district, 1.0)

    @property
    def v_max_kmh(self) -> float:
        """Tốc độ lớn nhất có thể trong mô phỏng (dùng cho static_vmax)."""
        return max(self.free_flow_kmh.values())

    @classmethod
    def load(cls, path: str | Path = DEFAULT_CONFIG_PATH) -> SimConfig:
        """Đọc file TOML và tạo SimConfig."""
        with open(path, "rb") as f:
            raw = tomllib.load(f)
        sim = raw.get("simulation", {})
        gs = raw.get("greenshields", {})
        pk = dict(raw.get("peaks", {}))
        base_ratio = pk.pop("base_density_ratio", 0.2)
        peaks = {
            name: PeakConfig(
                center_s=parse_hhmm(p["center"]),
                width_s=float(p["width_min"]) * 60,
                amplitude=float(p["amplitude"]),
            )
            for name, p in pk.items()
        }
        heu = raw.get("heuristic", {})
        return cls(
            seed=int(raw.get("seed", 42)),
            window_start_s=parse_hhmm(sim.get("window_start", "05:00")),
            window_end_s=parse_hhmm(sim.get("window_end", "23:00")),
            grid_step_s=int(sim.get("grid_step_s", GRID_STEP)),
            k_jam_veh_km=float(gs.get("k_jam_veh_km", 150.0)),
            min_speed_kmh=float(gs.get("min_speed_kmh", 5.0)),
            free_flow_kmh={k: float(v) for k, v in gs.get("free_flow_kmh", {}).items()}
            or {"default": 30.0},
            peaks=peaks,
            base_density_ratio=float(base_ratio),
            road_type_factor={k: float(v) for k, v in raw.get("road_type_factor", {}).items()}
            or {"default": 1.0},
            district_factor={k: float(v) for k, v in raw.get("district_factor", {}).items()},
            edge_noise=float(sim.get("edge_noise", 0.0)),
            default_heuristic=heu.get("default_mode", "dynamic_ub"),
            weight_w=float(heu.get("weight_w", 1.5)),
        )
