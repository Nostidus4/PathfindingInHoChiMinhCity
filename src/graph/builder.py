"""Dựng graph POI từ mạng đường OSM (thuật toán: docs/graph_construction.md §2). Owner: P2.

Cần `uv sync --group data` (osm_graph là networkx MultiDiGraph của osmnx).
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field

from src.geo import haversine_m
from src.graph.graph import Graph
from src.models import POI, LatLon, NodeId, RoadSegment

log = logging.getLogger(__name__)

# highway tag OSM -> khoá trong [greenshields.free_flow_kmh]
_ROAD_CLASS: dict[str, str] = {
    "motorway": "primary",
    "trunk": "primary",
    "primary": "primary",
    "secondary": "secondary",
    "tertiary": "tertiary",
    "residential": "residential",
    "living_street": "residential",
    "unclassified": "residential",
    "service": "residential",
}
_ROAD_RANK = {"primary": 0, "secondary": 1, "tertiary": 2, "residential": 3, "default": 4}

_SNAP_WARN_M = 100.0


@dataclass
class BuildReport:
    k: int
    candidate_pairs: int = 0
    no_path: int = 0
    through_poi: int = 0
    max_snap_m: float = 0.0
    repairs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class _Candidate:
    segment: RoadSegment
    through_poi: bool


def normalize_road_type(highway) -> str:
    """Tag highway (chuỗi hoặc list) -> loại đường cấp cao nhất trong _ROAD_CLASS."""
    tags = highway if isinstance(highway, list | tuple) else [highway]
    classes = [_ROAD_CLASS.get(str(t).removesuffix("_link"), "default") for t in tags if t]
    return min(classes, key=_ROAD_RANK.__getitem__, default="default")


def parse_lanes(lanes) -> int | None:
    """'2', '2;3', ['2', '3'] -> số làn lớn nhất; không đọc được -> None."""
    values = lanes if isinstance(lanes, list | tuple) else [lanes]
    nums = [int(n) for v in values if v is not None for n in re.findall(r"\d+", str(v))]
    nums = [n for n in nums if n > 0]
    return max(nums) if nums else None


def _first_name(name) -> str:
    if isinstance(name, list | tuple):
        name = next((n for n in name if n), "")
    return str(name) if name and not (isinstance(name, float) and math.isnan(name)) else ""


def snap_pois(
    pois: list[POI], osm_graph, allowed: set | None = None
) -> dict[NodeId, tuple[object, float]]:
    """POI id -> (node OSM gần nhất, khoảng cách mét); allowed giới hạn tập node được chọn."""
    coords = [
        (n, float(d["y"]), float(d["x"]))
        for n, d in osm_graph.nodes(data=True)
        if allowed is None or n in allowed
    ]
    if not coords:
        raise ValueError("Mạng đường OSM rỗng")
    result: dict[NodeId, tuple[object, float]] = {}
    for p in pois:
        cos_lat = math.cos(math.radians(p.lat))
        best = min(coords, key=lambda c: (c[1] - p.lat) ** 2 + ((c[2] - p.lon) * cos_lat) ** 2)
        result[p.id] = (best[0], haversine_m(p.lat, p.lon, best[1], best[2]))
    return result


def _k_nearest(pois: list[POI], k: int) -> dict[NodeId, list[NodeId]]:
    out: dict[NodeId, list[NodeId]] = {}
    for p in pois:
        others = sorted(
            (haversine_m(p.lat, p.lon, q.lat, q.lon), q.id) for q in pois if q.id != p.id
        )
        out[p.id] = [qid for _, qid in others[:k]]
    return out


def _edge_points(osm_graph, a, b, data: dict) -> list[LatLon]:
    """Polyline (lat, lon) của cạnh OSM a->b, đảo chiều nếu geometry lưu ngược."""
    na, nb = osm_graph.nodes[a], osm_graph.nodes[b]
    geom = data.get("geometry")
    if geom is None or not hasattr(geom, "coords"):
        return [(float(na["y"]), float(na["x"])), (float(nb["y"]), float(nb["x"]))]
    pts = [(float(lat), float(lon)) for lon, lat in geom.coords]
    start_a = haversine_m(pts[0][0], pts[0][1], float(na["y"]), float(na["x"]))
    end_a = haversine_m(pts[-1][0], pts[-1][1], float(na["y"]), float(na["x"]))
    return pts if start_a <= end_a else pts[::-1]


def _make_segment(
    osm_graph, path: list, u: POI, v: POI, snap_u: float, snap_v: float
) -> RoadSegment:
    points: list[LatLon] = [(u.lat, u.lon)]
    road_len: Counter[str] = Counter()
    name_len: Counter[str] = Counter()
    lanes_len: Counter[int] = Counter()
    total = 0.0
    for a, b in zip(path, path[1:], strict=False):
        # MultiDiGraph có thể có cạnh song song: lấy cạnh ngắn nhất
        data = min(osm_graph[a][b].values(), key=lambda d: float(d.get("length", math.inf)))
        pts = _edge_points(osm_graph, a, b, data)
        length = float(data.get("length", 0.0)) or sum(
            haversine_m(p[0], p[1], q[0], q[1]) for p, q in zip(pts, pts[1:], strict=False)
        )
        total += length
        for pt in pts:
            if pt != points[-1]:
                points.append(pt)
        road_len[normalize_road_type(data.get("highway"))] += length
        if name := _first_name(data.get("name")):
            name_len[name] += length
        if (lanes := parse_lanes(data.get("lanes"))) is not None:
            lanes_len[lanes] += length
    if (v.lat, v.lon) != points[-1]:
        points.append((v.lat, v.lon))

    length_m = total + snap_u + snap_v
    straight = haversine_m(u.lat, u.lon, v.lat, v.lon)
    if length_m < straight:  # giữ length_m >= haversine (điều kiện admissibility)
        log.warning("Cạnh %s->%s ngắn hơn haversine, nâng lên %.1f m", u.id, v.id, straight)
        length_m = straight
    return RoadSegment(
        id=f"{u.id}->{v.id}",
        source=u.id,
        target=v.id,
        length_m=length_m,
        road_type=road_len.most_common(1)[0][0] if road_len else "default",
        district=u.district,
        name=name_len.most_common(1)[0][0] if name_len else "",
        lanes=lanes_len.most_common(1)[0][0] if lanes_len else 1,
        geometry=tuple(points),
    )


def _scc_outside_largest(node_ids: list[NodeId], edges: dict[str, RoadSegment]) -> set[NodeId]:
    import networkx as nx

    g = nx.DiGraph()
    g.add_nodes_from(node_ids)
    g.add_edges_from((e.source, e.target) for e in edges.values())
    largest = max(nx.strongly_connected_components(g), key=len)
    return set(node_ids) - largest


def build_graph_with_report(
    pois: list[POI], osm_graph, k: int = 4, max_extra_k: int = 4
) -> tuple[Graph, BuildReport]:
    import networkx as nx

    if k < 1:
        raise ValueError("k phải >= 1")
    by_id = {p.id: p for p in pois}
    if len(by_id) != len(pois):
        raise ValueError("Trùng id POI")
    report = BuildReport(k=k)

    # Node ngoài thành phần liên thông mạnh lớn nhất không nối được hai chiều với POI khác
    main_component = max(nx.strongly_connected_components(osm_graph), key=len)
    nearest = snap_pois(pois, osm_graph)
    snap = snap_pois(pois, osm_graph, main_component)
    for pid, (node, dist) in snap.items():
        if node != nearest[pid][0]:
            report.repairs.append(
                f"{pid} nằm ngoài thành phần liên thông mạnh của mạng OSM, "
                f"snap sang node {node} cách {dist:.0f} m"
            )
    owners: dict[object, list[NodeId]] = {}
    for pid, (node, dist) in snap.items():
        owners.setdefault(node, []).append(pid)
        report.max_snap_m = max(report.max_snap_m, dist)
        if dist > _SNAP_WARN_M:
            report.warnings.append(f"{pid} snap xa {dist:.0f} m")
    for node, pids in owners.items():
        if len(pids) > 1:
            report.warnings.append(f"Các POI {', '.join(pids)} snap vào cùng node OSM {node}")

    cache: dict[tuple[NodeId, NodeId], _Candidate | None] = {}

    def evaluate(uid: NodeId, vid: NodeId) -> _Candidate | None:
        if (uid, vid) in cache:
            return cache[(uid, vid)]
        su, du = snap[uid]
        sv, dv = snap[vid]
        try:
            path = nx.shortest_path(osm_graph, su, sv, weight="length")
        except nx.NetworkXNoPath:
            report.no_path += 1
            cache[(uid, vid)] = None
            return None
        through = any(
            any(pid not in (uid, vid) for pid in owners.get(node, ())) for node in path[1:-1]
        )
        if through:
            report.through_poi += 1
        cand = _Candidate(_make_segment(osm_graph, path, by_id[uid], by_id[vid], du, dv), through)
        cache[(uid, vid)] = cand
        return cand

    def add_pairs(pairs: set[frozenset[NodeId]], edges: dict[str, RoadSegment]) -> None:
        for pair in pairs:
            a, b = sorted(pair)
            for uid, vid in ((a, b), (b, a)):
                cand = evaluate(uid, vid)
                if cand is not None and not cand.through_poi:
                    edges.setdefault(cand.segment.id, cand.segment)

    def pairs_for(ids, kk: int) -> set[frozenset[NodeId]]:
        nearest = _k_nearest(pois, kk)
        return {frozenset((u, v)) for u in ids for v in nearest[u]}

    edges: dict[str, RoadSegment] = {}
    all_pairs = pairs_for(by_id, k)
    report.candidate_pairs = len(all_pairs)
    add_pairs(all_pairs, edges)

    node_ids = list(by_id)
    for extra in range(2, max_extra_k + 1, 2):
        outside = _scc_outside_largest(node_ids, edges)
        if not outside:
            break
        before = len(edges)
        add_pairs(pairs_for(outside, k + extra), edges)
        report.repairs.append(
            f"k={k + extra} cho {len(outside)} node ({', '.join(sorted(outside))}): "
            f"+{len(edges) - before} cạnh"
        )

    outside = _scc_outside_largest(node_ids, edges)
    if outside:
        readded = [
            c.segment
            for c in cache.values()
            if c is not None
            and c.through_poi
            and (c.segment.source in outside or c.segment.target in outside)
        ]
        for seg in readded:
            edges.setdefault(seg.id, seg)
        report.repairs.append(f"Thêm lại {len(readded)} cạnh xuyên POI cho {len(outside)} node")
        outside = _scc_outside_largest(node_ids, edges)
    if outside:
        report.warnings.append(
            f"Vẫn chưa liên thông mạnh, cần xem lại các POI: {', '.join(sorted(outside))}"
        )

    for msg in report.repairs + report.warnings:
        log.info(msg)
    return Graph(pois, edges.values()), report


def build_graph(pois: list[POI], osm_graph, k: int = 4) -> Graph:
    return build_graph_with_report(pois, osm_graph, k)[0]
