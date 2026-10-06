"""Script WP1 (P1): OSM -> data/processed/pois.csv."""

from src.data.osm_fetch import fetch_road_network
from src.data.poi_io import save_pois
from src.data.poi_select import balance_by_district, select_intersections
from src.data.poi_validate import validate_pois


def main() -> None:
    print("1. Loading OSM road network...")
    graph = fetch_road_network()

    print("2. Selecting intersections...")
    pois = select_intersections(graph)

    print("3. Balancing POIs by district...")
    pois = balance_by_district(pois, per_district=30)

    print("4. Validating POIs...")
    errors = validate_pois(pois)

    if errors:
        print("POI validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("5. Saving POIs...")
    save_pois(pois)

    print()
    print(f"Done! Saved {len(pois)} POIs to data/processed/pois.csv")


if __name__ == "__main__":
    main()