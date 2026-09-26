"""Tải mạng đường và landmark từ OpenStreetMap bằng osmnx, cache vào data/raw/. Owner: P1.

Nhiệm vụ:
- fetch_road_network(): tải graph đường đi xe (network_type="drive") phủ 5 quận,
  lưu data/raw/hcmc_drive.graphml; nếu file đã có thì đọc cache, không tải lại.
- fetch_landmarks(): tải landmark (chợ, bệnh viện, trường, công viên...) lưu data/raw/.
- Cần `uv sync --group data`. Import osmnx BÊN TRONG hàm.
"""

from __future__ import annotations

from pathlib import Path

from src.config import REPO_ROOT

RAW_DIR = REPO_ROOT / "data" / "raw"


def fetch_road_network(cache_path: Path = RAW_DIR / "hcmc_drive.graphml", force: bool = False):
    """Trả networkx.MultiDiGraph của osmnx (có cache)."""
    raise NotImplementedError("TODO(P1)")


def fetch_landmarks(cache_path: Path = RAW_DIR / "landmarks.geojson", force: bool = False):
    """Trả GeoDataFrame các landmark (có cache)."""
    raise NotImplementedError("TODO(P1)")
