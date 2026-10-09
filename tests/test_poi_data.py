"""Owner: P1.

Cần test: pois.csv: >= 100 POI, >= 20 POI mỗi quận, không trùng, không ngoài ranh giới;
load/save round-trip.
"""

from collections import Counter

import pytest

from src.data.districts import (
    DISTRICT_POLYGONS,
    DISTRICTS,
    assign_district,
    bounding_box,
    distance_to_border_m,
    point_in_polygon,
)
from src.data.poi_io import DEFAULT_POIS_PATH, load_pois, save_pois
from src.data.poi_select import balance_by_district
from src.data.poi_validate import validate_pois
from src.geo import haversine_m
from src.models import POI

# --- ranh giới quận ---

SQUARE = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]
# Hình chữ L (lõm): bỏ góc trên phải của hình vuông 2x2
L_SHAPE = [(0.0, 0.0), (0.0, 2.0), (1.0, 2.0), (1.0, 1.0), (2.0, 1.0), (2.0, 0.0)]


def test_point_in_polygon_convex():
    assert point_in_polygon(0.5, 0.5, SQUARE)
    assert not point_in_polygon(1.5, 0.5, SQUARE)
    assert not point_in_polygon(-0.1, 0.5, SQUARE)


def test_point_in_polygon_concave():
    assert point_in_polygon(0.5, 1.5, L_SHAPE)
    assert point_in_polygon(1.5, 0.5, L_SHAPE)
    assert not point_in_polygon(1.5, 1.5, L_SHAPE)


@pytest.mark.parametrize(
    ("place", "lat", "lon", "expected"),
    [
        ("Chợ Bến Thành", 10.7725, 106.6980, "Quan 1"),
        ("Hồ Con Rùa", 10.7826, 106.6959, "Quan 3"),
        ("Chợ An Đông", 10.7578, 106.6712, "Quan 5"),
        ("Landmark 81", 10.7951, 106.7218, "Binh Thanh"),
        ("Trung tâm Phú Nhuận", 10.7990, 106.6800, "Phu Nhuan"),
        ("Sân bay Tân Sơn Nhất (Tân Bình)", 10.8185, 106.6588, None),
        ("Thảo Điền (bên kia sông)", 10.8032, 106.7365, None),
        ("Đầm Sen (Quận 11)", 10.7680, 106.6370, None),
        ("Bến Vân Đồn x Nguyễn Trường Tộ (Quận 4)", 10.76749, 106.70389, None),
    ],
)
def test_assign_district_known_places(place, lat, lon, expected):
    assert assign_district(lat, lon) == expected, place


def test_polygons_are_real_boundaries():
    assert set(DISTRICT_POLYGONS) == set(DISTRICTS)
    for district, polygon in DISTRICT_POLYGONS.items():
        # Ranh giới thật có nhiều đỉnh, không phải hình chữ nhật vẽ tay
        assert len(polygon) >= 20, district
        assert polygon[0] != polygon[-1], district


def test_distance_to_border():
    assert distance_to_border_m(10.7725, 106.6980, "Quan 1") > 500  # Chợ Bến Thành
    lat, lon = DISTRICT_POLYGONS["Quan 3"][0]
    assert distance_to_border_m(lat, lon, "Quan 3") < 1.0


def test_bounding_box_margin():
    west, south, east, north = bounding_box()
    for polygon in DISTRICT_POLYGONS.values():
        for lat, lon in polygon:
            assert south <= lat <= north and west <= lon <= east
    w1, s1, e1, n1 = bounding_box(1000)
    assert haversine_m(south, west, s1, west) == pytest.approx(1000, rel=0.02)
    assert w1 < west and e1 > east and n1 > north


# --- validate_pois ---


def _poi(pid, lat, lon, district, kind="intersection", name=None):
    return POI(pid, name if name is not None else f"POI {pid}", lat, lon, district, kind)


BEN_THANH = (10.7725, 106.6980)  # Quận 1
HO_CON_RUA = (10.7826, 106.6959)  # Quận 3


def _valid_set() -> list[POI]:
    return [_poi("a", *BEN_THANH, "Quan 1"), _poi("b", *HO_CON_RUA, "Quan 3")]


def _errors(pois):
    return validate_pois(pois, min_total=1, min_per_district=0)


def test_validate_accepts_valid_set():
    assert _errors(_valid_set()) == []


def test_validate_rejects_wrong_label():
    pois = [_poi("a", *BEN_THANH, "Quan 3")]
    assert any("nằm trong 'Quan 1'" in e for e in _errors(pois))


def test_validate_rejects_outside():
    pois = [_poi("a", 10.8185, 106.6588, "Phu Nhuan")]  # Tân Sơn Nhất
    assert any("ngoài 5 quận" in e for e in _errors(pois))


def test_validate_rejects_close_duplicate_and_bad_fields():
    pois = [
        *_valid_set(),
        _poi("a", 10.7726, 106.6980, "Quan 1"),  # trùng id, cách "a" ~11 m
        _poi("c", 10.7740, 106.6990, "Quan 1", kind="shop", name=" "),
    ]
    errors = _errors(pois)
    assert any("trùng id" in e for e in errors)
    assert any("quá gần" in e for e in errors)
    assert any("kind không hợp lệ" in e for e in errors)
    assert any("không có tên" in e for e in errors)


def test_validate_counts():
    errors = validate_pois(_valid_set(), min_total=100, min_per_district=20)
    assert any("Chỉ có 2 POI" in e for e in errors)
    assert sum("cần ít nhất 20" in e for e in errors) == len(DISTRICTS)
    assert any("Tên quận không hợp lệ" in e for e in validate_pois([_poi("x", 0, 0, "Quan 9")]))


# --- balance_by_district ---


def _line(district, n, lat0, lon0, step_deg=0.001, prefix="p"):
    """n POI thẳng hàng theo kinh độ, cách nhau ~110 m."""
    return [_poi(f"{prefix}{i:02d}", lat0, lon0 + i * step_deg, district) for i in range(n)]


def test_balance_spreads_points():
    pois = _line("Quan 5", 11, 10.7560, 106.6650)
    step = haversine_m(pois[0].lat, pois[0].lon, pois[1].lat, pois[1].lon)
    for seed in range(11):
        chosen = balance_by_district(pois, per_district=3, seed=seed)
        assert len(chosen) == 3
        # Điểm thứ hai là điểm xa điểm xuất phát nhất, luôn là một đầu mút
        assert {"p00", "p10"} & {p.id for p in chosen}
        # Tối ưu cho 3 điểm trên đoạn 10 bước là cách nhau 5 bước; farthest-point sampling
        # bảo đảm ít nhất một nửa (2,5 bước), tức >= 3 bước vì điểm nằm trên lưới
        gap = min(haversine_m(a.lat, a.lon, b.lat, b.lon) for a in chosen for b in chosen if a != b)
        assert gap >= 3 * step * 0.99


def test_balance_is_deterministic():
    pois = _line("Quan 5", 11, 10.7560, 106.6650) + _line(
        "Quan 1", 8, 10.7725, 106.6950, prefix="q"
    )
    first = balance_by_district(pois, per_district=4, seed=7)
    assert first == balance_by_district(pois, per_district=4, seed=7)
    assert Counter(p.district for p in first) == {"Quan 1": 4, "Quan 5": 4}


def test_balance_min_separation_across_districts():
    a = _poi("a", 10.7700, 106.6900, "Quan 1")
    near = _poi("b1", 10.7700, 106.6903, "Quan 3")  # cách a ~33 m nhưng khác quận
    far = _poi("b2", 10.7750, 106.6900, "Quan 3")
    for seed in range(5):
        chosen = balance_by_district([a, near, far], per_district=1, seed=seed, min_sep_m=100)
        assert {p.id for p in chosen} == {"a", "b2"}


def test_balance_landmarks_first():
    pois = [
        *_line("Quan 1", 6, 10.7725, 106.6950),
        _poi("L", 10.7730, 106.6975, "Quan 1", "landmark"),
    ]
    chosen = balance_by_district(pois, per_district=2, seed=0, min_sep_m=50)
    assert "L" in {p.id for p in chosen}
    assert len(chosen) == 2


def test_balance_stops_when_too_dense():
    pois = _line("Quan 1", 5, 10.7725, 106.6950, step_deg=0.0001)  # cách nhau ~11 m
    assert len(balance_by_district(pois, per_district=5, min_sep_m=30)) < 5


# --- select_intersections / name_intersection trên mạng đường giả lập ---


def _toy_osm():
    """Mạng đường nhỏ quanh chợ Bến Thành (Quận 1, cách ranh giới > 500 m).

       N --Hẻm-- E ---> D (một chiều: D chỉ vào được, không ra được)
       |         |  ^
    Pasteur   Lê Lợi|Lê Thánh Tôn
       |         |
       W -Lê Lợi- C -Lê Lợi- E ...      (xem _EDGES)
    """
    nx = pytest.importorskip("networkx")
    g = nx.MultiDiGraph()
    nodes = {
        0: (10.7725, 106.6980, 4),  # C: Lê Lợi (secondary) x Pasteur (tertiary)
        1: (10.7730, 106.6980, 3),  # N: chỉ có Pasteur + hẻm
        2: (10.7720, 106.6980, 3),  # S: Pasteur x Nguyễn Du
        3: (10.7725, 106.6985, 3),  # E: Lê Lợi, Lê Thánh Tôn, Lý Tự Trọng, hẻm
        4: (10.7725, 106.6975, 2),  # W: street_count = 2
        5: (10.7715, 106.6985, 3),  # R: chỉ có đường residential
        6: (10.7735, 106.6985, 3),  # D: ngoài thành phần liên thông mạnh
    }
    for n, (lat, lon, count) in nodes.items():
        g.add_node(n, y=lat, x=lon, street_count=count)

    def road(u, v, name, highway, oneway=False):
        g.add_edge(u, v, name=name, highway=highway, length=50.0)
        if not oneway:
            g.add_edge(v, u, name=name, highway=highway, length=50.0)

    road(0, 1, "Pasteur", "tertiary")
    road(0, 2, "Pasteur", "tertiary")
    road(0, 3, "Lê Lợi", "secondary")
    road(0, 4, "Lê Lợi", "secondary")
    road(1, 3, "Hẻm 12 Pasteur", "residential")
    road(2, 5, "Nguyễn Du", "residential")
    road(5, 3, "Lý Tự Trọng", "residential")
    road(1, 6, "Pasteur", "tertiary", oneway=True)
    road(3, 6, "Lê Thánh Tôn", "tertiary", oneway=True)
    return g


def test_select_intersections_filters():
    from src.data.poi_select import select_intersections

    pois = {p.id: p for p in select_intersections(_toy_osm())}
    # N: một tên + hẻm; W: street_count 2; R: không có đường chính; D: không đi ra được
    assert set(pois) == {"0", "2", "3"}
    assert pois["0"].name == "Lê Lợi x Pasteur"
    assert pois["2"].name == "Pasteur x Nguyễn Du"
    assert pois["3"].name == "Lê Lợi x Lê Thánh Tôn"  # tên lấy cả cạnh đi ra (Lê Thánh Tôn)
    assert all(p.district == "Quan 1" and p.kind == "intersection" for p in pois.values())


def test_select_intersections_options():
    from src.data.poi_select import select_intersections

    ids = {p.id for p in select_intersections(_toy_osm(), require_major=False)}
    assert "5" in ids  # R được chọn khi không bắt buộc đường chính
    assert select_intersections(_toy_osm(), min_border_m=10_000) == []


def test_name_intersection_cases():
    from src.data.poi_select import name_intersection

    g = _toy_osm()
    assert name_intersection(g, 1) == "Pasteur x Hẻm 12 Pasteur"  # hẻm xếp sau
    assert name_intersection(g, 6) == "Pasteur x Lê Thánh Tôn"  # chỉ có cạnh đi vào
    g.add_node(99, y=10.7725, x=106.6990)
    g.add_edge(99, 0, name="Đường 3 Tháng 2", highway="primary")
    g.add_edge(0, 99, name="3 Tháng 2", highway="primary")
    assert name_intersection(g, 99) == "Đường 3 Tháng 2"  # hai cách viết là một đường
    g.add_node(100, y=10.7725, x=106.6991)
    assert name_intersection(g, 100) == "Intersection 100"


# --- landmark ---


@pytest.mark.parametrize(
    ("tags", "expected"),
    [
        ({"amenity": "marketplace"}, (("amenity", "marketplace"), 6)),
        ({"historic": "memorial"}, (("historic", "memorial"), 3)),
        ({"tourism": "museum", "historic": "yes"}, (("tourism", "museum"), 5)),
        ({"amenity": "school", "historic": "monument"}, (("historic", "monument"), 3)),
        ({"amenity": "cafe"}, None),
        ({"amenity": float("nan")}, None),  # ô trống của GeoDataFrame
    ],
)
def test_landmark_category(tags, expected):
    from src.data.poi_select import landmark_category

    assert landmark_category(tags) == expected


def test_landmark_name_and_id_helpers():
    from src.data.poi_select import _is_latin, _landmark_id

    assert _is_latin("Chợ Bến Thành") and _is_latin("Trường Đại học Sài Gòn – cơ sở chính")
    assert not _is_latin("គុយទាវ Hong Phat")
    assert _landmark_id(("way", 123)) == "Lw123"
    assert _landmark_id(("relation", 5)) == "Lr5"
    assert _landmark_id(7) == "L7"


def _toy_landmarks():
    pd = pytest.importorskip("pandas")
    geometry = pytest.importorskip("shapely.geometry")
    point, polygon = geometry.Point, geometry.Polygon
    d = 0.0001
    rows = {
        ("node", 1): {
            "name": "Chợ Thử",
            "amenity": "marketplace",
            "geometry": point(106.69852, 10.77252),
        },
        ("node", 2): {
            "name": "Chợ Wikidata",
            "amenity": "marketplace",
            "wikidata": "Q1",
            "geometry": point(106.6980, 10.7720),  # trùng node S (2)
        },
        ("way", 3): {
            "name": "Bảo tàng Thử",
            "tourism": "museum",
            # Ô vuông quanh node D (6) nằm ngoài thành phần liên thông mạnh
            "geometry": polygon(
                [
                    (106.6985 - d, 10.7735 - d),
                    (106.6985 + d, 10.7735 - d),
                    (106.6985 + d, 10.7735 + d),
                ]
            ),
        },
        ("node", 4): {
            "name": "គុយទាវ",
            "tourism": "attraction",
            "geometry": point(106.6975, 10.7725),
        },
        ("node", 5): {
            "name": "Xa quá",
            "tourism": "attraction",
            "geometry": point(106.7020, 10.7770),
        },
        ("node", 6): {"name": None, "amenity": "hospital", "geometry": point(106.6981, 10.7726)},
    }
    index = pd.MultiIndex.from_tuples(list(rows), names=["element", "id"])
    return pd.DataFrame(list(rows.values()), index=index)


def test_snap_landmarks_ranking_and_snapping():
    from src.data.poi_select import snap_landmarks

    osm = _toy_osm()
    pois = snap_landmarks(_toy_landmarks(), osm, min_sep_m=10)
    # Chợ có wikidata đứng đầu; chợ thứ hai bị bỏ vì trùng loại; tên chữ Khmer, landmark quá xa
    # đường và landmark không tên đều bị loại
    assert [p.id for p in pois] == ["Ln2", "Lw3"]
    assert all(p.kind == "landmark" and p.district == "Quan 1" for p in pois)
    market, museum = pois
    assert (market.lat, market.lon) == (10.7720, 106.6980)
    # Bảo tàng nằm cạnh node D (cụt) nên được snap sang node N trong thành phần liên thông mạnh
    assert (museum.lat, museum.lon) == (10.7730, 106.6980)
    assert [p.id for p in snap_landmarks(_toy_landmarks(), osm, per_district=1, min_sep_m=10)] == [
        "Ln2"
    ]
    # Hai landmark cách nhau ~110 m: với min_sep_m mặc định 150 m chỉ giữ cái xếp hạng cao hơn
    assert [p.id for p in snap_landmarks(_toy_landmarks(), osm)] == ["Ln2"]


class _NodesStub:
    """Đủ dùng cho osm_fetch._covers: chỉ cần graph.nodes(data=True)."""

    def __init__(self, coords):
        self._coords = coords

    def nodes(self, data=False):
        return [(i, {"x": lon, "y": lat}) for i, (lat, lon) in enumerate(self._coords)]


def test_cache_coverage_check():
    from src.data.osm_fetch import _covers

    bbox = bounding_box(1000)
    west, south, east, north = bbox
    full = _NodesStub([(south, west), (north, east)])
    old = _NodesStub([(10.745, 106.650), (10.825, 106.735)])  # vùng tải cũ của WP1
    assert _covers(full, bbox)
    assert not _covers(old, bbox)
    assert not _covers(_NodesStub([]), bbox)


# --- poi_io ---


def test_save_load_round_trip(tmp_path):
    pois = [
        _poi("2493366320", *BEN_THANH, "Quan 1", name="Lê Lợi x Nguyễn Huệ"),
        _poi("L1", *HO_CON_RUA, "Quan 3", kind="landmark", name="Hồ Con Rùa"),
    ]
    path = tmp_path / "sub" / "pois.csv"
    save_pois(pois, path)
    assert load_pois(path) == pois


# --- pois.csv thật ---

needs_pois = pytest.mark.skipif(not DEFAULT_POIS_PATH.exists(), reason="pois.csv chưa có")


@needs_pois
def test_real_pois_valid():
    pois = load_pois()
    assert validate_pois(pois, min_sep_m=150.0) == []
    assert len(pois) >= 100
    counts = Counter(p.district for p in pois)
    assert set(counts) == set(DISTRICTS) and min(counts.values()) >= 20


@needs_pois
def test_real_pois_labels_match_polygons():
    for p in load_pois():
        assert assign_district(p.lat, p.lon) == p.district, p
        assert distance_to_border_m(p.lat, p.lon, p.district) >= 20.0, p
