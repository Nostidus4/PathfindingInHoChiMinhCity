"""Bản đồ preview POI (output của WP1) bằng folium. Owner: P1.

Nhiệm vụ: vẽ mỗi POI một marker, tô màu theo quận, vẽ polygon quận,
xuất outputs/pois_preview.html để cả nhóm kiểm tra bằng mắt.
"""

from __future__ import annotations

from pathlib import Path

from src.config import REPO_ROOT
from src.models import POI


def render_poi_preview(
    pois: list[POI], out_path: Path = REPO_ROOT / "outputs" / "pois_preview.html"
) -> Path:
    """Xuất HTML preview, trả đường dẫn file."""
    raise NotImplementedError("TODO(P1)")
