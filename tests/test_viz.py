"""Owner: P6. Bản đồ T1: route theo geometry thật, fallback nét đứt, ETA từ trace."""

import pytest

from src.graph.graph import Graph
from src.mocks import MOCK_POIS, MockTrafficProvider
from src.models import RoadSegment
from src.viz.map_static import ROUTE_COLORS, node_arrival_times, render_map, render_routes_map
from tests.fake_pathfinder import FakePathfinder


def test_render_map_fallback_dashed(mock_graph, tmp_path):
    pf = FakePathfinder(mock_graph, MockTrafficProvider())
    r = pf.route("A", "F", 0.0, trace=True)
    out = render_map(mock_graph, mock_graph.nodes(), r, tmp_path / "m.html")
    html = out.read_text(encoding="utf-8")
    assert "cạnh thiếu geometry" in html  # mock không có polyline -> nét đứt
    assert "Xuất phát: Mock A" in html and "Đích: Mock F" in html
    assert "00:03:00" in html  # ETA tại đích


def test_render_map_uses_geometry(tmp_path):
    a, b = MOCK_POIS[0], MOCK_POIS[2]  # A, C
    bend = (10.7715, 106.6990)
    seg = RoadSegment("A->C", "A", "C", 400.0, geometry=((a.lat, a.lon), bend, (b.lat, b.lon)))
    graph = Graph([a, b], [seg])
    pf = FakePathfinder(graph, MockTrafficProvider())
    r = pf.route("A", "C", 0.0)
    html = render_map(graph, graph.nodes(), r, tmp_path / "g.html").read_text(encoding="utf-8")
    assert "cạnh thiếu geometry" not in html
    assert str(bend[1]) in html


def test_render_map_without_route(mock_graph, tmp_path):
    assert render_map(mock_graph, mock_graph.nodes(), None, tmp_path / "p.html").exists()


def test_eta_from_trace(mock_graph):
    pf = FakePathfinder(mock_graph, MockTrafficProvider())
    times = node_arrival_times(pf.route("A", "F", 100.0, trace=True))
    assert times == {"A": 100.0, "C": 140.0, "B": 170.0, "D": 220.0, "F": 280.0}


def test_too_many_routes_rejected(mock_graph, tmp_path):
    r = FakePathfinder(mock_graph, MockTrafficProvider()).route("A", "F", 0.0)
    routes = [(str(i), r) for i in range(len(ROUTE_COLORS) + 1)]
    with pytest.raises(ValueError, match="Tối đa"):
        render_routes_map(mock_graph, mock_graph.nodes(), routes, tmp_path / "x.html")
