"""Script WP2 (P2): pois.csv + OSM -> data/processed/graph.json.

Chạy: uv sync --group data && uv run python scripts/build_graph.py --k 6
Các bước: load_pois -> fetch_road_network -> build_graph -> run_all_checks -> save_graph.
Thêm --preview để xuất outputs/graph_preview.html (vẽ POI và cạnh lên bản đồ).
"""

from __future__ import annotations

import argparse
import logging
import statistics
import sys
from collections import Counter
from pathlib import Path

from src.config import REPO_ROOT
from src.data.poi_io import DEFAULT_POIS_PATH, load_pois
from src.geo import haversine_m
from src.graph.builder import build_graph_with_report
from src.graph.checks import run_all_checks
from src.graph.graph import Graph
from src.graph.io import DEFAULT_GRAPH_PATH, save_graph

PREVIEW_PATH = REPO_ROOT / "outputs" / "graph_preview.html"


def load_osm(osm_path: Path | None):
    """Đọc graphml nếu có đường dẫn, ngược lại dùng cache/tải của data.osm_fetch."""
    if osm_path is not None:
        import osmnx as ox

        return ox.load_graphml(osm_path)
    from src.data.osm_fetch import fetch_road_network

    return fetch_road_network()


def graph_stats(graph: Graph) -> dict[str, str]:
    """Các chỉ số cho bảng thống kê trong docs/graph_construction.md."""
    edges = graph.edges()
    n = len(graph.nodes())
    lengths = sorted(e.length_m for e in edges)
    ratios = []
    for e in edges:
        a, b = graph.get_node(e.source), graph.get_node(e.target)
        d = haversine_m(a.lat, a.lon, b.lat, b.lon)
        if d > 0:
            ratios.append(e.length_m / d)
    ids = {e.id for e in edges}
    oneway = sum(1 for e in edges if f"{e.target}->{e.source}" not in ids)
    per_district = Counter(p.district for p in graph.nodes())
    return {
        "Số node": str(n),
        "Số edge": str(len(edges)),
        "Degree trung bình (ra / vào)": f"{len(edges) / n:.2f}" if n else "-",
        "Số edge one-way": str(oneway),
        "Chiều dài edge (min / trung vị / max)": (
            f"{lengths[0]:.0f} / {statistics.median(lengths):.0f} / {lengths[-1]:.0f} m"
            if lengths
            else "-"
        ),
        "Tỉ lệ length / haversine trung bình": f"{statistics.mean(ratios):.2f}" if ratios else "-",
        "Số node theo quận": ", ".join(f"{k}: {v}" for k, v in sorted(per_district.items())),
    }


def render_graph_preview(graph: Graph, out_path: Path = PREVIEW_PATH) -> Path:
    """Vẽ POI và cạnh (polyline thật) bằng folium; cạnh one-way tô màu khác."""
    import folium

    nodes = graph.nodes()
    center = (
        sum(p.lat for p in nodes) / len(nodes),
        sum(p.lon for p in nodes) / len(nodes),
    )
    fmap = folium.Map(location=center, zoom_start=14)
    ids = {e.id for e in graph.edges()}
    for e in graph.edges():
        oneway = f"{e.target}->{e.source}" not in ids
        a, b = graph.get_node(e.source), graph.get_node(e.target)
        points = e.geometry or ((a.lat, a.lon), (b.lat, b.lon))  # thiếu polyline thì nối thẳng
        folium.PolyLine(
            [list(pt) for pt in points],
            color="#d62728" if oneway else "#1f77b4",
            weight=3 if oneway else 2,
            opacity=0.7,
            tooltip=f"{e.id} · {e.name or e.road_type} · {e.length_m:.0f} m",
        ).add_to(fmap)
    for p in nodes:
        folium.CircleMarker(
            (p.lat, p.lon),
            radius=4,
            color="#222",
            fill=True,
            fill_opacity=0.9,
            tooltip=f"{p.id} · {p.name} · {p.district}",
        ).add_to(fmap)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(str(out_path))
    return out_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dựng graph POI từ pois.csv và mạng đường OSM")
    parser.add_argument("--k", type=int, default=6, help="số POI gần nhất để thử nối (mặc định 6)")
    parser.add_argument("--pois", type=Path, default=DEFAULT_POIS_PATH)
    parser.add_argument("--osm", type=Path, default=None, help="file graphml (mặc định: cache P1)")
    parser.add_argument("--out", type=Path, default=DEFAULT_GRAPH_PATH)
    parser.add_argument("--preview", action="store_true", help="xuất outputs/graph_preview.html")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    # Console Windows mặc định cp1252, không in được tiếng Việt
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    pois = load_pois(args.pois)
    print(f"Đã đọc {len(pois)} POI từ {args.pois}")
    osm_graph = load_osm(args.osm)
    print(f"Mạng đường OSM: {osm_graph.number_of_nodes()} node, {osm_graph.number_of_edges()} cạnh")

    graph, report = build_graph_with_report(pois, osm_graph, k=args.k)
    print(
        f"k={report.k}: {report.candidate_pairs} cặp ứng viên, "
        f"{report.through_poi} chiều bị lọc vì xuyên POI, {report.no_path} chiều không có đường, "
        f"snap xa nhất {report.max_snap_m:.0f} m"
    )
    for msg in report.repairs:
        print(f"  sửa liên thông: {msg}")
    for msg in report.warnings:
        print(f"  cảnh báo: {msg}")

    print("\nThống kê graph:")
    for key, value in graph_stats(graph).items():
        print(f"  {key}: {value}")

    if args.preview:
        print(f"\nPreview: {render_graph_preview(graph)}")

    errors = run_all_checks(graph)
    if errors:
        print(f"\n{len(errors)} lỗi kiểm tra, KHÔNG ghi graph.json:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    save_graph(graph, args.out)
    print(f"\nĐã ghi {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
