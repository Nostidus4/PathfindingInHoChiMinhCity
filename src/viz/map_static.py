"""Vẽ bản đồ route bằng folium, xuất HTML (T1). Owner: P6.

render_map(graph, pois, route): vẽ POI, vẽ route theo polyline THẬT
(RoadSegment.geometry, không nối thẳng 2 POI), popup ETA từng node, xuất HTML.
"""

from __future__ import annotations

from pathlib import Path

from src.config import REPO_ROOT
from src.models import POI, RouteResult


def render_map(
    graph,
    pois: list[POI],
    route: RouteResult | None = None,
    out_path: Path = REPO_ROOT / "outputs" / "route.html",
) -> Path:
    raise NotImplementedError("TODO(P6)")
