"""Đọc/ghi graph ra data/processed/graph.json. Owner: P2.

Schema: docs/graph_construction.md §4.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from pathlib import Path

from src.config import REPO_ROOT
from src.graph.graph import Graph
from src.models import POI, RoadSegment

DEFAULT_GRAPH_PATH = REPO_ROOT / "data" / "processed" / "graph.json"
SCHEMA_VERSION = 1

_COORD_DIGITS = 7
_LENGTH_DIGITS = 2


def _node_to_dict(p: POI) -> dict:
    d = asdict(p)
    d["lat"] = round(p.lat, _COORD_DIGITS)
    d["lon"] = round(p.lon, _COORD_DIGITS)
    return d


def _edge_to_dict(e: RoadSegment) -> dict:
    d = asdict(e)
    # Làm tròn LÊN để length_m đã lưu vẫn >= haversine
    scale = 10**_LENGTH_DIGITS
    d["length_m"] = math.ceil(round(e.length_m * scale, 6)) / scale
    d["geometry"] = [
        [round(lat, _COORD_DIGITS), round(lon, _COORD_DIGITS)] for lat, lon in e.geometry
    ]
    return d


def save_graph(graph: Graph, path: Path = DEFAULT_GRAPH_PATH) -> None:
    data = {
        "version": SCHEMA_VERSION,
        "nodes": [_node_to_dict(p) for p in sorted(graph.nodes(), key=lambda p: p.id)],
        "edges": [_edge_to_dict(e) for e in sorted(graph.edges(), key=lambda e: e.id)],
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


def load_graph(path: Path) -> Graph:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy {path}. Chạy: uv run python scripts/build_graph.py"
        )
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    version = data.get("version")
    if version != SCHEMA_VERSION:
        raise ValueError(f"graph.json version {version!r}, cần {SCHEMA_VERSION}")
    pois = [POI(**d) for d in data["nodes"]]
    edges = [
        RoadSegment(**{**d, "geometry": tuple((lat, lon) for lat, lon in d.get("geometry", []))})
        for d in data["edges"]
    ]
    return Graph(pois, edges)


def load_default_graph() -> Graph:
    return load_graph(DEFAULT_GRAPH_PATH)
