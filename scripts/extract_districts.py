"""Script WP1 (P1): lấy ranh giới thật của 5 quận cũ từ OSM -> src/data/district_polygons.py.

Từ 01/07/2025 TP.HCM bỏ cấp quận; OSM vẫn giữ ranh giới cũ dưới dạng relation
`boundary=historic` (end_date 2025-06-30). Script tải các relation này qua Overpass,
đơn giản hoá polygon (mặc định sai số ~10 m) rồi ghi ra module Python thuần,
để districts.py dùng mà không cần shapely/osmnx khi chạy.

Chạy: uv sync --group data && uv run python scripts/extract_districts.py
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from src.config import REPO_ROOT

OUT_PATH = REPO_ROOT / "src" / "data" / "district_polygons.py"

# Tên quận trong code -> id relation OSM (boundary=historic)
DISTRICT_RELATIONS: dict[str, int] = {
    "Quan 1": 2587287,
    "Quan 3": 3819816,
    "Quan 5": 3820432,
    "Binh Thanh": 3797166,
    "Phu Nhuan": 3851694,
}

# Vùng tìm relation (bao rộng hơn 5 quận)
_SEARCH_BBOX = (106.60, 10.70, 106.80, 10.90)  # (west, south, east, north)

_HEADER = '''"""Ranh giới 5 quận cũ (lat, lon). FILE SINH TỰ ĐỘNG, không sửa tay.

Nguồn: OpenStreetMap (© OpenStreetMap contributors, ODbL), relation boundary=historic.
Sinh bởi: scripts/extract_districts.py, ngày {today}, sai số đơn giản hoá {tol_m:.0f} m.
"""

from __future__ import annotations

# Tên quận -> id relation OSM
DISTRICT_RELATIONS: dict[str, int] = {{
{relations}}}

DISTRICT_POLYGONS: dict[str, list[tuple[float, float]]] = {{
'''


def fetch_polygons(tol_m: float) -> dict[str, list[tuple[float, float]]]:
    """Tải relation của 5 quận, đơn giản hoá, trả {quận: [(lat, lon), ...]}.

    Điểm cuối (trùng điểm đầu) được bỏ, giống quy ước cũ của DISTRICT_POLYGONS.
    """
    import osmnx as ox

    gdf = ox.features_from_bbox(_SEARCH_BBOX, tags={"boundary": "historic"})
    tol_deg = tol_m / 111_000
    result: dict[str, list[tuple[float, float]]] = {}
    for district, rel_id in DISTRICT_RELATIONS.items():
        key = ("relation", rel_id)
        if key not in gdf.index:
            raise RuntimeError(f"Không tìm thấy relation {rel_id} ({district}) trên OSM")
        geom = gdf.loc[key, "geometry"]
        if geom.geom_type == "MultiPolygon":
            # Lấy phần lớn nhất (các mảnh nhỏ nếu có là bãi bồi, không có đường)
            geom = max(geom.geoms, key=lambda g: g.area)
        ring = geom.simplify(tol_deg, preserve_topology=True).exterior.coords
        result[district] = [(round(lat, 6), round(lon, 6)) for lon, lat in ring][:-1]
    return result


def render_module(polygons: dict[str, list[tuple[float, float]]], tol_m: float) -> str:
    relations = "".join(f'    "{d}": {rid},\n' for d, rid in DISTRICT_RELATIONS.items())
    lines = [_HEADER.format(today=date.today().isoformat(), tol_m=tol_m, relations=relations)]
    for district, ring in polygons.items():
        lines.append(f'    "{district}": [\n')
        lines.extend(f"        ({lat:.6f}, {lon:.6f}),\n" for lat, lon in ring)
        lines.append("    ],\n")
    lines.append("}\n")
    return "".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tải ranh giới 5 quận cũ từ OSM")
    parser.add_argument("--tol-m", type=float, default=10.0, help="sai số đơn giản hoá (m)")
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    polygons = fetch_polygons(args.tol_m)
    args.out.write_text(render_module(polygons, args.tol_m), encoding="utf-8", newline="\n")
    for district, ring in polygons.items():
        print(f"{district}: {len(ring)} đỉnh")
    print(f"Đã ghi {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
