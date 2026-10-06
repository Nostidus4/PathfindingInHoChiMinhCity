"""Chọn POI từ dữ liệu OSM. Owner: P1."""

from __future__ import annotations

import math
import random

from src.data.districts import assign_district
from src.models import POI


def _distance_m(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Khoảng cách Haversine, đơn vị mét."""

    radius = 6_371_000

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * radius * math.asin(math.sqrt(a))


def _node_lat_lon(osm_graph, node_id):
    data = osm_graph.nodes[node_id]
    return float(data["y"]), float(data["x"])


def select_intersections(
    osm_graph,
    min_degree: int = 3,
) -> list[POI]:
    """Chọn các nút giao có degree >= min_degree trong 5 quận."""

    pois: list[POI] = []

    for node_id in osm_graph.nodes:
        degree = osm_graph.degree(node_id)

        if degree < min_degree:
            continue

        lat, lon = _node_lat_lon(osm_graph, node_id)
        district = assign_district(lat, lon)

        if district is None:
            continue

        pois.append(
            POI(
                id=str(node_id),
                name=name_intersection(osm_graph, node_id),
                lat=lat,
                lon=lon,
                district=district,
                kind="intersection",
            )
        )

    return pois


def snap_landmarks(landmarks, osm_graph) -> list[POI]:
    """Snap landmark vào node đường gần nhất."""

    import osmnx as ox

    pois: list[POI] = []

    for index, row in landmarks.iterrows():
        geometry = row.geometry

        if geometry is None:
            continue

        point = geometry.centroid
        lon = float(point.x)
        lat = float(point.y)

        district = assign_district(lat, lon)

        if district is None:
            continue

        node = ox.distance.nearest_nodes(
            osm_graph,
            X=lon,
            Y=lat,
        )

        node_lat, node_lon = _node_lat_lon(osm_graph, node)

        name = row.get("name")

        if not isinstance(name, str) or not name.strip():
            name = f"Landmark {index}"

        pois.append(
            POI(
                id=f"landmark_{index}_{node}",
                name=name.strip(),
                lat=node_lat,
                lon=node_lon,
                district=district,
                kind="landmark",
            )
        )

    return pois


def name_intersection(osm_graph, node_id) -> str:
    """Đặt tên giao lộ dựa trên tên các đường đi qua node."""

    street_names: list[str] = []

    for _, _, data in osm_graph.edges(node_id, data=True):
        name = data.get("name")

        if isinstance(name, list):
            names = name
        else:
            names = [name]

        for street in names:
            if isinstance(street, str) and street.strip():
                street = street.strip()

                if street not in street_names:
                    street_names.append(street)

    if len(street_names) >= 2:
        return f"{street_names[0]} x {street_names[1]}"

    if len(street_names) == 1:
        return street_names[0]

    return f"Intersection {node_id}"


def balance_by_district(
    pois: list[POI],
    per_district: int = 20,
    seed: int = 42,
) -> list[POI]:
    """Lấy mẫu cân bằng theo quận, loại POI quá gần nhau."""

    rng = random.Random(seed)

    result: list[POI] = []

    districts = sorted({poi.district for poi in pois})

    for district in districts:
        district_pois = [
            poi for poi in pois
            if poi.district == district
        ]

        rng.shuffle(district_pois)

        selected: list[POI] = []

        for poi in district_pois:
            if all(
                _distance_m(
                    poi.lat,
                    poi.lon,
                    other.lat,
                    other.lon,
                ) >= 30.0
                for other in selected
            ):
                selected.append(poi)

            if len(selected) >= per_district:
                break

        result.extend(selected)

    return result