"""Script WP2 (P2): pois.csv + OSM -> data/processed/graph.json.

Chạy: uv sync --group data && uv run python scripts/build_graph.py --k 6
Các bước: load_pois -> fetch_road_network -> build_graph -> run_all_checks -> save_graph.
"""


def main() -> None:
    raise NotImplementedError("TODO(P2)")


if __name__ == "__main__":
    main()
