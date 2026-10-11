"""Owner: P2.

Cần test: Graph interface; graph.json liên thông mạnh, không node cô lập, length >= haversine;
save/load round-trip.
"""

from collections import Counter

import pytest

from src.geo import haversine_m
from src.graph.builder import normalize_road_type, parse_lanes
from src.graph.checks import (
    check_isolated_nodes,
    check_length_vs_haversine,
    check_strongly_connected,
    run_all_checks,
)
from src.graph.graph import Graph
from src.graph.io import DEFAULT_GRAPH_PATH, load_default_graph, load_graph, save_graph
from src.mocks import MOCK_POIS, MockGraph, _build_edges
from src.models import POI, RoadSegment


@pytest.fixture
def graph() -> Graph:
    return Graph(MOCK_POIS, _build_edges())


def _without_g() -> Graph:
    pois = [p for p in MOCK_POIS if p.id != "G"]
    edges = [e for e in _build_edges() if "G" not in (e.source, e.target)]
    return Graph(pois, edges)


# --- Graph interface ---


def test_same_interface_as_mock(graph, mock_graph: MockGraph):
    assert {p.id for p in graph.nodes()} == {p.id for p in mock_graph.nodes()}
    assert {e.id for e in graph.edges()} == {e.id for e in mock_graph.edges()}
    for p in mock_graph.nodes():
        assert graph.get_node(p.id) == p
        assert {e.id for e in graph.get_neighbors(p.id)} == {
            e.id for e in mock_graph.get_neighbors(p.id)
        }
    assert graph.get_edge("A->B").length_m == 1000.0


def test_neighbors_returns_copy(graph):
    graph.get_neighbors("A").clear()
    assert graph.get_neighbors("A")


def test_in_edges(graph):
    assert {e.source for e in graph.get_in_edges("A")} == {"B", "C", "G"}
    assert graph.get_in_edges("G") == []


def test_unknown_ids_raise_keyerror(graph):
    with pytest.raises(KeyError):
        graph.get_node("Z")
    with pytest.raises(KeyError):
        graph.get_edge("A->Z")
    assert graph.get_neighbors("Z") == []


def test_invalid_construction():
    a = POI("A", "a", 10.77, 106.70, "Quan 1")
    b = POI("B", "b", 10.78, 106.70, "Quan 1")
    with pytest.raises(ValueError):
        Graph([a, a], [])
    with pytest.raises(ValueError):
        Graph([a], [RoadSegment("A->B", "A", "B", 1200.0)])
    seg = RoadSegment("A->B", "A", "B", 1200.0)
    with pytest.raises(ValueError):
        Graph([a, b], [seg, seg])


# --- checks ---


def test_mock_graph_not_strongly_connected(graph):
    errors = check_strongly_connected(graph)
    assert errors and any("G" in e for e in errors)
    assert any("G" in e and "vào" in e for e in check_isolated_nodes(graph))


def test_valid_graph_passes_all_checks():
    assert run_all_checks(_without_g()) == []


def test_empty_graph_fails():
    assert check_strongly_connected(Graph([], []))


def test_isolated_node_detected():
    pois = [*MOCK_POIS[:6], POI("X", "x", 10.78, 106.71, "Quan 3")]
    edges = [e for e in _build_edges() if "G" not in (e.source, e.target)]
    errors = check_isolated_nodes(Graph(pois, edges))
    assert len(errors) == 2 and all("X" in e for e in errors)


def test_edge_shorter_than_haversine_detected():
    a = POI("A", "a", 10.7700, 106.7000, "Quan 1")
    b = POI("B", "b", 10.7800, 106.7000, "Quan 1")  # cách ~1.1 km
    graph = Graph([a, b], [RoadSegment("A->B", "A", "B", 500.0)])
    errors = check_length_vs_haversine(graph)
    assert len(errors) == 1 and "A->B" in errors[0]


# --- io ---


def test_save_load_round_trip(tmp_path):
    a = POI("P001", "Chợ Bến Thành", 10.7725, 106.6980, "Quan 1", "landmark")
    b = POI("P002", "Lê Lợi x Nam Kỳ Khởi Nghĩa", 10.7740, 106.7010, "Quan 1")
    geom = ((10.7725, 106.698), (10.7731, 106.6995), (10.774, 106.701))
    e1 = RoadSegment("P001->P002", "P001", "P002", 412.5, "secondary", "Quan 1", "Lê Lợi", 2, geom)
    e2 = RoadSegment("P002->P001", "P002", "P001", 412.5, "secondary", "Quan 1", "Lê Lợi", 2)
    original = Graph([a, b], [e1, e2])

    path = tmp_path / "sub" / "graph.json"
    save_graph(original, path)
    loaded = load_graph(path)

    assert loaded.nodes() == original.nodes()
    assert sorted(loaded.edges(), key=lambda e: e.id) == sorted(
        original.edges(), key=lambda e: e.id
    )
    assert isinstance(loaded.get_edge("P001->P002").geometry[0], tuple)
    assert "Bến Thành" in path.read_text(encoding="utf-8")


def test_save_rounds_length_up(tmp_path):
    a = POI("A", "a", 10.7700, 106.7000, "Quan 1")
    b = POI("B", "b", 10.7800, 106.7000, "Quan 1")
    straight = haversine_m(a.lat, a.lon, b.lat, b.lon)
    path = tmp_path / "graph.json"
    save_graph(Graph([a, b], [RoadSegment("A->B", "A", "B", straight)]), path)
    loaded = load_graph(path)
    assert check_length_vs_haversine(loaded, tol_m=0.0) == []
    assert loaded.get_edge("A->B").length_m - straight < 0.01
    save_graph(loaded, path)
    assert load_graph(path).get_edge("A->B").length_m == loaded.get_edge("A->B").length_m


def test_load_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_graph(tmp_path / "nope.json")


def test_load_wrong_version(tmp_path):
    path = tmp_path / "graph.json"
    path.write_text('{"version": 99, "nodes": [], "edges": []}', encoding="utf-8")
    with pytest.raises(ValueError):
        load_graph(path)


# --- builder helpers ---


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("primary", "primary"),
        ("trunk_link", "primary"),
        ("secondary_link", "secondary"),
        ("living_street", "residential"),
        ("footway", "default"),
        (None, "default"),
        (["residential", "tertiary"], "tertiary"),
    ],
)
def test_normalize_road_type(tag, expected):
    assert normalize_road_type(tag) == expected


@pytest.mark.parametrize(
    ("raw", "expected"), [("2", 2), ("2;3", 3), (["1", "4"], 4), (None, None), ("x", None)]
)
def test_parse_lanes(raw, expected):
    assert parse_lanes(raw) == expected


# --- builder trên mạng đường giả lập nhỏ ---


def _osm(coords, edges):
    """Mạng đường giả lập: coords {node: (lat, lon)}, edges [(u, v, highway)] một chiều."""
    nx = pytest.importorskip("networkx")
    g = nx.MultiDiGraph()
    for n, (lat, lon) in coords.items():
        g.add_node(n, y=lat, x=lon)
    for u, v, highway in edges:
        (la, lo), (lb, lob) = coords[u], coords[v]
        g.add_edge(u, v, length=haversine_m(la, lo, lb, lob), highway=highway, name="Đường Thử")
    return g


def _line_osm():
    """5 node OSM thẳng hàng 0..4, hai chiều."""
    coords = {i: (10.7700, 106.7000 + 0.001 * i) for i in range(5)}
    edges = [(i, i + 1, "secondary") for i in range(4)] + [
        (i + 1, i, "secondary") for i in range(4)
    ]
    return _osm(coords, edges)


def _line_pois():
    return [
        POI("A", "a", 10.77003, 106.70000, "Quan 1"),  # lệch node 0 khoảng 3 m
        POI("B", "b", 10.77000, 106.70200, "Quan 1"),
        POI("C", "c", 10.77000, 106.70400, "Quan 3"),
    ]


def test_build_graph_filters_through_poi():
    from src.graph.builder import build_graph_with_report

    graph, report = build_graph_with_report(_line_pois(), _line_osm(), k=2)
    # A<->C đi xuyên qua B nên bị lọc, chỉ còn các cạnh trực tiếp
    assert {e.id for e in graph.edges()} == {"A->B", "B->A", "B->C", "C->B"}
    assert report.through_poi == 2
    assert report.candidate_pairs == 3
    assert run_all_checks(graph) == []


def test_build_graph_segment_fields():
    from src.graph.builder import build_graph

    graph = build_graph(_line_pois(), _line_osm(), k=2)
    a, b = graph.get_node("A"), graph.get_node("B")
    seg = graph.get_edge("A->B")
    assert seg.length_m >= haversine_m(a.lat, a.lon, b.lat, b.lon)
    assert seg.geometry[0] == (a.lat, a.lon) and seg.geometry[-1] == (b.lat, b.lon)
    assert seg.road_type == "secondary" and seg.name == "Đường Thử" and seg.lanes == 1
    assert seg.district == "Quan 1"
    assert graph.get_edge("C->B").district == "Quan 3"


def _oneway_osm(with_return: bool = True):
    """X(0) -> 1 -> Y(2) một chiều; chiều về Y(2) -> 3 -> X(0) đi vòng (nếu with_return)."""
    coords = {0: (10.7700, 106.7000), 1: (10.7700, 106.7010), 2: (10.7700, 106.7020)}
    coords[3] = (10.7730, 106.7010)
    edges = [(0, 1, "primary"), (1, 2, "primary")]
    if with_return:
        edges += [(2, 3, "residential"), (3, 0, "residential")]
    return _osm(coords, edges)


_ONEWAY_POIS = [
    POI("X", "x", 10.7700, 106.7000, "Quan 5"),
    POI("Y", "y", 10.7700, 106.7020, "Quan 5"),
]


def test_build_graph_respects_oneway():
    from src.graph.builder import build_graph

    graph = build_graph(_ONEWAY_POIS, _oneway_osm(), k=1)
    there, back = graph.get_edge("X->Y"), graph.get_edge("Y->X")
    assert back.length_m > there.length_m
    assert (10.7730, 106.7010) in back.geometry
    assert there.road_type == "primary" and back.road_type == "residential"


def test_build_graph_snaps_dead_end_into_main_component():
    from src.graph.builder import build_graph_with_report

    # 0 <-> 1 <-> 2 hai chiều, thêm nhánh cụt một chiều 2 -> 3 (vào được nhưng không ra được)
    coords = {0: (10.7700, 106.7000), 1: (10.7700, 106.7010), 2: (10.7700, 106.7020)}
    coords[3] = (10.7704, 106.7024)
    edges = [(0, 1, "primary"), (1, 0, "primary"), (1, 2, "primary"), (2, 1, "primary")]
    osm = _osm(coords, [*edges, (2, 3, "residential")])
    pois = [
        POI("X", "x", 10.7700, 106.7000, "Quan 5"),
        POI("Z", "z", 10.7704, 106.7024, "Quan 5"),  # nằm đúng node cụt 3
    ]
    graph, report = build_graph_with_report(pois, osm, k=1)
    assert {e.id for e in graph.edges()} == {"X->Z", "Z->X"}
    assert any(r.startswith("Z ") for r in report.repairs)
    assert run_all_checks(graph) == []


# --- graph.json thật (chỉ chạy khi đã commit file) ---

needs_real_graph = pytest.mark.skipif(
    not DEFAULT_GRAPH_PATH.exists(), reason="data/processed/graph.json chưa có"
)


@needs_real_graph
def test_real_graph_passes_checks():
    assert run_all_checks(load_default_graph()) == []


@needs_real_graph
def test_real_graph_size():
    graph = load_default_graph()
    assert len(graph.nodes()) >= 100
    per_district = Counter(p.district for p in graph.nodes())
    assert len(per_district) == 5 and min(per_district.values()) >= 20
