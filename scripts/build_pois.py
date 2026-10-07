"""Script WP1 (P1): OSM -> data/processed/pois.csv + outputs/pois_preview.html.

Chạy: uv sync --group data && uv run python scripts/build_pois.py
Các bước: fetch_road_network -> select_intersections + snap_landmarks
-> balance_by_district -> validate_pois -> save_pois -> render_poi_preview.
"""


def main() -> None:
    raise NotImplementedError("TODO(P1)")


if __name__ == "__main__":
    main()
