"""Vẽ bản đồ route bằng folium, xuất HTML (T1). Owner: P6.

render_map(graph, pois, route): vẽ POI, vẽ route theo polyline THẬT
(RoadSegment.geometry, không nối thẳng 2 POI), popup ETA từng node, xuất HTML.
render_routes_map(graph, pois, routes): chồng nhiều route (time demo), mỗi route một màu
(tối đa 8, màu cố định theo thứ tự, không lặp màu).

Cạnh thiếu geometry -> vẽ đường thẳng NÉT ĐỨT giữa 2 POI để nhìn là biết.
ETA từng node lấy từ route.trace (bước "expand"); không có trace thì chỉ có ETA
ở start và goal. Module này không tính traffic.
"""

from __future__ import annotations

from collections.abc import Sequence
from html import escape
from pathlib import Path

import folium

from src.config import REPO_ROOT
from src.models import POI, LatLon, NodeId, RouteResult
from src.timeutil import format_duration, format_seconds

DEFAULT_OUT = REPO_ROOT / "outputs" / "route.html"

# Bảng màu categorical cố định (dataviz reference palette, light mode), theo thứ tự route.
ROUTE_COLORS: tuple[str, ...] = (
    "#2a78d6",
    "#eb6834",
    "#1baf7a",
    "#eda100",
    "#e87ba4",
    "#008300",
    "#4a3aa7",
    "#e34948",
)
POI_COLOR = "#52514e"
ROUTE_WEIGHT = 5


def node_arrival_times(route: RouteResult) -> dict[NodeId, float]:
    """Thời điểm đến từng node trên path (giây kể từ 00:00), lấy từ trace nếu có."""
    times: dict[NodeId, float] = {}
    on_path = set(route.path)
    for step in route.trace:
        if step.action == "expand" and step.node in on_path and step.node not in times:
            times[step.node] = step.t
    if route.path:
        times[route.path[0]] = route.departure_time_s
        times[route.path[-1]] = route.arrival_time_s
    return times


def _edge_points(graph, edge_id: str) -> tuple[list[LatLon], bool]:
    """Polyline của cạnh và cờ `has_geometry` (False -> fallback đường thẳng)."""
    seg = graph.get_edge(edge_id)
    if len(seg.geometry) >= 2:
        return [tuple(p) for p in seg.geometry], True
    a, b = graph.get_node(seg.source), graph.get_node(seg.target)
    return [(a.lat, a.lon), (b.lat, b.lon)], False


def _add_pois(fmap: folium.Map, pois: Sequence[POI]) -> None:
    layer = folium.FeatureGroup(name="POI")
    for p in pois:
        folium.CircleMarker(
            location=(p.lat, p.lon),
            radius=3,
            color=POI_COLOR,
            weight=1,
            fill=True,
            fill_opacity=0.6,
            tooltip=f"{escape(p.name)} ({escape(p.id)})",
            popup=folium.Popup(
                f"<b>{escape(p.name)}</b><br>ID: {escape(p.id)}<br>"
                f"{escape(p.district)} · {escape(p.kind)}",
                max_width=250,
            ),
        ).add_to(layer)
    layer.add_to(fmap)


def _add_route(fmap: folium.Map, graph, route: RouteResult, label: str, color: str) -> None:
    layer = folium.FeatureGroup(name=label)
    for eid in route.edges:
        points, has_geometry = _edge_points(graph, eid)
        folium.PolyLine(
            points,
            color=color,
            weight=ROUTE_WEIGHT,
            opacity=0.85,
            dash_array=None if has_geometry else "8 8",
            tooltip=label if has_geometry else f"{label} (cạnh thiếu geometry)",
        ).add_to(layer)

    times = node_arrival_times(route)
    last = len(route.path) - 1
    for i, nid in enumerate(route.path):
        p = graph.get_node(nid)
        role = "Xuất phát" if i == 0 else "Đích" if i == last else f"Điểm {i}"
        eta = f"<br>ETA: {format_seconds(times[nid])}" if nid in times else ""
        popup = f"<b>{role}: {escape(p.name)}</b><br>ID: {escape(nid)}{eta}"
        if i == last:
            popup += f"<br>Thời gian đi: {format_duration(route.travel_time_s)}"
        folium.CircleMarker(
            location=(p.lat, p.lon),
            radius=7 if i in (0, last) else 5,
            color="#ffffff",
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=1.0,
            tooltip=f"{role}: {escape(p.name)}",
            popup=folium.Popup(popup, max_width=250),
        ).add_to(layer)
    layer.add_to(fmap)


def render_routes_map(
    graph,
    pois: Sequence[POI],
    routes: Sequence[tuple[str, RouteResult]],
    out_path: Path = DEFAULT_OUT,
) -> Path:
    """Vẽ POI và nhiều route (label, RouteResult) chồng lên nhau, xuất HTML."""
    if not pois:
        raise ValueError("Không có POI để vẽ bản đồ")
    center = (sum(p.lat for p in pois) / len(pois), sum(p.lon for p in pois) / len(pois))
    fmap = folium.Map(location=center, zoom_start=14, tiles="OpenStreetMap")
    _add_pois(fmap, pois)

    drawn = [(label, r) for label, r in routes if r.found and r.path]
    if len(drawn) > len(ROUTE_COLORS):
        raise ValueError(
            f"Tối đa {len(ROUTE_COLORS)} route trên một bản đồ (nhận {len(drawn)}); "
            "gộp các route trùng đường trước khi vẽ"
        )
    for (label, route), color in zip(drawn, ROUTE_COLORS, strict=False):
        _add_route(fmap, graph, route, label, color)
    if drawn:
        bounds = [(graph.get_node(n).lat, graph.get_node(n).lon) for _, r in drawn for n in r.path]
        fmap.fit_bounds(bounds, padding=(30, 30))
    folium.LayerControl(collapsed=False).add_to(fmap)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(str(out_path))
    return out_path


def render_map(
    graph,
    pois: list[POI],
    route: RouteResult | None = None,
    out_path: Path = DEFAULT_OUT,
) -> Path:
    """Vẽ POI và (nếu có) một route, xuất HTML. Trả đường dẫn file."""
    routes = []
    if route is not None:
        label = route.heuristic_mode or "route"
        routes.append((f"{label} @ {format_seconds(route.departure_time_s)}", route))
    return render_routes_map(graph, pois, routes, out_path)
