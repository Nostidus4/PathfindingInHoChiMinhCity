"""Đọc/ghi đồ thị ra data/processed/graph.json. Owner: P2.

- save_graph(graph, path), load_graph(path)
- load_default_graph(): đọc data/processed/graph.json (file đã commit),
  để P3-P6 không cần cài osmnx.
"""

from __future__ import annotations

from pathlib import Path

from src.config import REPO_ROOT
from src.graph.graph import Graph

DEFAULT_GRAPH_PATH = REPO_ROOT / "data" / "processed" / "graph.json"


def save_graph(graph: Graph, path: Path = DEFAULT_GRAPH_PATH) -> None:
    raise NotImplementedError("TODO(P2)")


def load_graph(path: Path) -> Graph:
    raise NotImplementedError("TODO(P2)")


def load_default_graph() -> Graph:
    """Đồ thị chuẩn của cả nhóm (data/processed/graph.json)."""
    return load_graph(DEFAULT_GRAPH_PATH)
