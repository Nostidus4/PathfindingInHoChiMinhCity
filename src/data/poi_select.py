"""Chọn POI từ dữ liệu OSM. Owner: P1.

- select_intersections: nút giao thật (street_count >= 3) thuộc thành phần liên thông mạnh lớn nhất
  của mạng OSM, có ít nhất một đường chính và hai đường có tên (không tính hẻm), không sát ranh
  giới quận.
- snap_landmarks: chọn landmark nổi bật mỗi quận (wikidata, loại, diện tích) và snap vào node đường
  gần nhất.
- name_intersection: tên "Đường A x Đường B", ưu tiên đường cấp cao, bỏ qua hẻm.
- balance_by_district: chọn per_district POI mỗi quận, trải đều bằng farthest-point sampling.
"""

from __future__ import annotations

import random

from src.data.districts import assign_district, distance_to_border_m
from src.geo import haversine_m
from src.models import POI

# Loại đường tính là "đường chính" (không tính nhánh _link)
MAJOR_ROADS = frozenset({"trunk", "primary", "secondary", "tertiary"})

_ROAD_RANK = {
    "trunk": 0,
    "primary": 1,
    "secondary": 2,
    "tertiary": 3,
    "unclassified": 4,
    "residential": 5,
}


def _as_list(value) -> list:
    return list(value) if isinstance(value, list | tuple) else [value]


def _node_lat_lon(osm_graph, node_id):
    data = osm_graph.nodes[node_id]
    return float(data["y"]), float(data["x"])


def _incident_edges(osm_graph, node_id) -> list[dict]:
    """Dữ liệu các cạnh đi ra và đi vào node."""
    out_edges = [d for _, _, d in osm_graph.out_edges(node_id, data=True)]
    in_edges = [d for _, _, d in osm_graph.in_edges(node_id, data=True)]
    return out_edges + in_edges


def _is_alley(name: str) -> bool:
    """Tên hẻm, kể cả khi OSM ghi lẫn tiền tố như "Đường Hẻm 904 ..."."""
    return "hẻm" in name.casefold().split()


def _name_key(name: str) -> str:
    """Khoá so trùng tên đường: "Đường 3 Tháng 2" và "3 Tháng 2" là một."""
    return name.casefold().removeprefix("đường ").strip()


def _street_names(osm_graph, node_id) -> list[str]:
    """Tên các đường qua node (không trùng), đường cấp cao trước."""
    best: dict[str, tuple[int, int, str]] = {}
    for order, data in enumerate(_incident_edges(osm_graph, node_id)):
        rank = min(
            (
                _ROAD_RANK.get(str(h).removesuffix("_link"), 9)
                for h in _as_list(data.get("highway"))
            ),
            default=9,
        )
        for name in _as_list(data.get("name")):
            if not isinstance(name, str) or not name.strip():
                continue
            name = name.strip()
            key = _name_key(name)
            if key not in best or (rank, order) < best[key][:2]:
                best[key] = (rank, order, name)
    return [name for _, _, name in sorted(best.values())]


def main_component(osm_graph) -> set:
    """Thành phần liên thông mạnh lớn nhất: node đi tới và được tới từ mọi node khác."""
    import networkx as nx

    return max(nx.strongly_connected_components(osm_graph), key=len)


def select_intersections(
    osm_graph,
    min_degree: int = 3,
    require_major: bool = True,
    min_named_streets: int = 2,
    min_border_m: float = 20.0,
) -> list[POI]:
    """Chọn các nút giao trong 5 quận dùng được cho tìm đường.

    - Chỉ lấy node thuộc thành phần liên thông mạnh lớn nhất (đi tới và đi ra được).
    - min_degree so với street_count của osmnx (số con đường vật lý gặp nhau tại node),
      không dùng degree của MultiDiGraph vì đường hai chiều bị đếm hai lần.
    - require_major: phải có ít nhất một cạnh là đường chính (trunk/primary/secondary/tertiary).
    - min_named_streets: số đường có tên khác nhau tối thiểu, không tính hẻm.
    - min_border_m: bỏ nút giao nằm sát ranh giới quận (thường là đường ranh giới), vì polygon
      đã đơn giản hoá (sai số ~10 m) nên không chắc điểm thuộc quận nào.
    """

    main = main_component(osm_graph)
    pois: list[POI] = []

    for node_id, data in osm_graph.nodes(data=True):
        if node_id not in main:
            continue

        street_count = data.get("street_count")
        if street_count is None:
            street_count = len(
                set(osm_graph.predecessors(node_id)) | set(osm_graph.successors(node_id))
            )
        if int(street_count) < min_degree:
            continue

        if require_major and not any(
            str(h) in MAJOR_ROADS
            for e in _incident_edges(osm_graph, node_id)
            for h in _as_list(e.get("highway"))
        ):
            continue

        named = [n for n in _street_names(osm_graph, node_id) if not _is_alley(n)]
        if len(named) < min_named_streets:
            continue

        lat, lon = _node_lat_lon(osm_graph, node_id)
        district = assign_district(lat, lon)

        if district is None or distance_to_border_m(lat, lon, district) < min_border_m:
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


# Điểm ưu tiên theo loại landmark (tag OSM). historic=* (bất kỳ) được 3 điểm.
LANDMARK_SCORES: dict[tuple[str, str], int] = {
    ("amenity", "marketplace"): 6,
    ("shop", "mall"): 5,
    ("tourism", "museum"): 5,
    ("tourism", "attraction"): 4,
    ("leisure", "park"): 4,
    ("amenity", "university"): 3,
    ("amenity", "hospital"): 3,
    ("amenity", "place_of_worship"): 2,
    ("tourism", "gallery"): 2,
    ("amenity", "library"): 2,
    ("leisure", "garden"): 1,
    ("leisure", "sports_centre"): 1,
    ("amenity", "school"): 0,
}


def _text(value) -> str | None:
    """Giá trị tag dạng chuỗi (GeoDataFrame dùng NaN cho ô trống)."""
    return value.strip() if isinstance(value, str) and value.strip() else None


def landmark_category(tags) -> tuple[tuple[str, str], int] | None:
    """(loại, điểm) của landmark theo tag OSM; None nếu không thuộc loại nào."""
    best = None
    for (key, value), score in LANDMARK_SCORES.items():
        if _text(tags.get(key)) == value and (best is None or score > best[1]):
            best = ((key, value), score)
    historic = _text(tags.get("historic"))
    if historic and (best is None or best[1] < 3):
        best = (("historic", historic), 3)
    return best


def _is_latin(name: str) -> bool:
    """Tên chỉ gồm chữ Latin (kể cả tiếng Việt có dấu), loại tên viết bằng chữ khác."""
    import unicodedata

    return all("LATIN" in unicodedata.name(ch, "") for ch in name if ch.isalpha())


def _landmark_id(index) -> str:
    """("way", 123) -> "Lw123"; id ngắn, không dấu cách để gõ trên CLI."""
    if isinstance(index, tuple) and len(index) == 2:
        return f"L{str(index[0])[:1]}{index[1]}"
    return f"L{index}"


def snap_landmarks(
    landmarks,
    osm_graph,
    per_district: int = 4,
    max_snap_m: float = 200.0,
    min_border_m: float = 20.0,
    min_sep_m: float = 150.0,
) -> list[POI]:
    """Chọn tối đa per_district landmark mỗi quận và snap vào node đường gần nhất.

    - Xếp hạng: có wikidata trước, rồi điểm loại (LANDMARK_SCORES), rồi diện tích lớn hơn.
      Mỗi quận lấy tối đa một landmark mỗi loại để đa dạng (chợ, bảo tàng, công viên...).
    - Chỉ snap vào node thuộc thành phần liên thông mạnh lớn nhất, cách hình landmark không quá
      max_snap_m; node phải cùng quận với landmark và cách ranh giới quận >= min_border_m.
    - Toạ độ POI là toạ độ node đường (POI nằm đúng trên mạng đường); landmark sau cách các
      landmark đã chọn ít nhất min_sep_m.
    Trả list theo thứ tự xếp hạng; cần group data (shapely).
    """

    import math

    from shapely.geometry import Point
    from shapely.ops import nearest_points

    main = main_component(osm_graph)
    nodes = [(n, float(d["y"]), float(d["x"])) for n, d in osm_graph.nodes(data=True) if n in main]

    candidates = []
    for index, row in landmarks.iterrows():
        name = _text(row.get("name"))
        geometry = row.geometry
        category = landmark_category(row)
        if name is None or geometry is None or category is None or not _is_latin(name):
            continue
        centroid = geometry.centroid
        district = assign_district(centroid.y, centroid.x)
        if district is None:
            continue
        area_m2 = geometry.area * 111_000**2 * math.cos(math.radians(centroid.y))
        has_wikidata = _text(row.get("wikidata")) is not None
        key = (not has_wikidata, -category[1], -area_m2, _landmark_id(index))
        candidates.append((key, district, category[0], name, geometry, index))
    candidates.sort(key=lambda c: c[0])

    margin = max_snap_m / 111_000 * 1.5
    chosen: list[POI] = []
    used_categories: set[tuple[str, tuple[str, str]]] = set()
    for _, district, category, name, geometry, index in candidates:
        if sum(p.district == district for p in chosen) >= per_district:
            continue
        if (district, category) in used_categories:
            continue
        min_x, min_y, max_x, max_y = geometry.bounds
        best = None
        for node_id, lat, lon in nodes:
            if not (
                min_y - margin <= lat <= max_y + margin and min_x - margin <= lon <= max_x + margin
            ):
                continue
            target = nearest_points(geometry, Point(lon, lat))[0]
            dist = haversine_m(lat, lon, target.y, target.x)
            if best is None or dist < best[0]:
                best = (dist, node_id, lat, lon)
        if best is None or best[0] > max_snap_m:
            continue
        _, node_id, lat, lon = best
        if (
            assign_district(lat, lon) != district
            or distance_to_border_m(lat, lon, district) < min_border_m
        ):
            continue
        if any(haversine_m(lat, lon, p.lat, p.lon) < min_sep_m for p in chosen):
            continue
        chosen.append(POI(_landmark_id(index), name, lat, lon, district, "landmark"))
        used_categories.add((district, category))

    return chosen


def name_intersection(osm_graph, node_id) -> str:
    """Đặt tên giao lộ từ tên các đường qua node (cả chiều vào và ra).

    Ưu tiên đường cấp cao và đường không phải hẻm.
    """

    names = _street_names(osm_graph, node_id)
    names = [n for n in names if not _is_alley(n)] + [n for n in names if _is_alley(n)]

    if len(names) >= 2:
        return f"{names[0]} x {names[1]}"

    if len(names) == 1:
        return names[0]

    return f"Intersection {node_id}"


def balance_by_district(
    pois: list[POI],
    per_district: int = 20,
    seed: int = 42,
    min_sep_m: float = 30.0,
) -> list[POI]:
    """Chọn tối đa per_district POI mỗi quận, trải đều trong quận.

    Landmark (kind == "landmark") được chọn trước. Phần còn lại chọn bằng farthest-point
    sampling: mỗi bước lấy ứng viên xa các POI đã chọn nhất, nên POI phủ đều cả quận thay vì
    dồn cục như lấy ngẫu nhiên. seed chỉ quyết định điểm xuất phát (khi chưa có landmark).
    Dừng sớm nếu ứng viên xa nhất vẫn gần hơn min_sep_m.
    """

    rng = random.Random(seed)

    def dist(a: POI, b: POI) -> float:
        return haversine_m(a.lat, a.lon, b.lat, b.lon)

    # Landmark chọn trước, theo thứ tự đầu vào (người gọi xếp theo mức độ nổi tiếng)
    landmarks: list[POI] = []
    for poi in pois:
        if poi.kind != "landmark":
            continue
        if sum(p.district == poi.district for p in landmarks) >= per_district:
            continue
        if all(dist(poi, other) >= min_sep_m for other in landmarks):
            landmarks.append(poi)

    result: list[POI] = []
    for district in sorted({poi.district for poi in pois}):
        selected = [p for p in landmarks if p.district == district]
        # Khoảng cách tính với mọi POI đã chọn, kể cả ở quận khác (POI hai bên ranh giới quận)
        anchors = result + [p for p in landmarks if p.district != district] + selected
        rest = sorted(
            (p for p in pois if p.district == district and p.kind != "landmark"),
            key=lambda p: p.id,
        )
        gaps = [min((dist(p, a) for a in anchors), default=float("inf")) for p in rest]

        if not selected and per_district > 0:
            pool = [i for i, g in enumerate(gaps) if g >= min_sep_m]
            if pool:
                i = rng.choice(pool)
                chosen = rest.pop(i)
                gaps.pop(i)
                selected.append(chosen)
                gaps = [min(g, dist(p, chosen)) for g, p in zip(gaps, rest, strict=True)]

        while len(selected) < per_district and rest:
            i = max(range(len(rest)), key=gaps.__getitem__)
            if gaps[i] < min_sep_m:
                break
            chosen = rest.pop(i)
            gaps.pop(i)
            selected.append(chosen)
            gaps = [min(g, dist(p, chosen)) for g, p in zip(gaps, rest, strict=True)]

        result.extend(selected)

    return result
