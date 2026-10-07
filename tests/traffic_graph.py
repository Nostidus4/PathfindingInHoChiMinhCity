"""Graph thử cho các test traffic (WP3): mọi tổ hợp loại đường x quận trong config.

Mỗi tổ hợp là một cặp node với cạnh hai chiều dài length_m, nên test phủ được cả
trường hợp mật độ cao nhất (primary ở Quận 1) lẫn thấp nhất, và cạnh dài (khó thoả FIFO hơn).
"""

from __future__ import annotations

from src.config import SimConfig
from src.graph.graph import Graph
from src.models import POI, RoadSegment


def make_traffic_graph(cfg: SimConfig, length_m: float = 3000.0) -> Graph:
    road_types = sorted(set(cfg.free_flow_kmh) | set(cfg.road_type_factor))
    districts = sorted(cfg.district_factor) + ["Ngoai vung"]
    pois: list[POI] = []
    edges: list[RoadSegment] = []
    for i, road_type in enumerate(road_types):
        for j, district in enumerate(districts):
            u, v = f"{road_type}-{j}-u", f"{road_type}-{j}-v"
            lat, lon = 10.76 + 0.01 * i, 106.68 + 0.01 * j
            pois += [POI(u, u, lat, lon, district), POI(v, v, lat + 0.001, lon, district)]
            for a, b in ((u, v), (v, u)):
                edges.append(RoadSegment(f"{a}->{b}", a, b, length_m, road_type, district))
    return Graph(pois, edges)
