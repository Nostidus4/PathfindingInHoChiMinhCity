"""Script WP1 (P1): OSM -> data/processed/pois.csv + outputs/pois_preview.html.

Chạy: uv sync --group data && uv run python scripts/build_pois.py
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter

from src.data.osm_fetch import fetch_landmarks, fetch_road_network
from src.data.poi_io import save_pois
from src.data.poi_select import balance_by_district, select_intersections, snap_landmarks
from src.data.poi_validate import validate_pois
from src.data.preview import render_poi_preview


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chọn POI cho 5 quận từ OSM")
    parser.add_argument("--per-district", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-sep-m", type=float, default=150.0, help="khoảng cách tối thiểu")
    parser.add_argument(
        "--landmarks-per-district", type=int, default=4, help="số landmark mỗi quận (0 = không lấy)"
    )
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    print("1. Loading OSM road network...")
    graph = fetch_road_network()
    print(f"   {graph.number_of_nodes()} node, {graph.number_of_edges()} cạnh")

    print("2. Selecting intersections...")
    candidates = select_intersections(graph)
    per_district = dict(sorted(Counter(p.district for p in candidates).items()))
    print(f"   {len(candidates)} ứng viên: {per_district}")

    landmarks = []
    if args.landmarks_per_district > 0:
        print("3. Selecting landmarks...")
        landmarks = snap_landmarks(
            fetch_landmarks(),
            graph,
            per_district=args.landmarks_per_district,
            min_sep_m=args.min_sep_m,
        )
        for poi in landmarks:
            print(f"   {poi.district}: {poi.name}")

    print("4. Balancing POIs by district...")
    pois = balance_by_district(
        landmarks + candidates,
        per_district=args.per_district,
        seed=args.seed,
        min_sep_m=args.min_sep_m,
    )

    print("5. Validating POIs...")
    errors = validate_pois(pois, min_sep_m=args.min_sep_m)

    if errors:
        print("POI validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("6. Saving POIs...")
    save_pois(pois)
    preview = render_poi_preview(pois)

    print()
    print(f"Done! Saved {len(pois)} POIs to data/processed/pois.csv")
    print(f"Theo quận: {dict(sorted(Counter(p.district for p in pois).items()))}")
    print(f"Theo loại: {dict(sorted(Counter(p.kind for p in pois).items()))}")
    print(f"Preview: {preview}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
