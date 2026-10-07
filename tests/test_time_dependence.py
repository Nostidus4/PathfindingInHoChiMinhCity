"""Owner: P5/P6.

Cùng A/B, giờ cao điểm cost > giờ thấp điểm (MockTrafficProvider rush_factor < 1).
Phần P6: time_dependence_demo trên FakePathfinder. P5 bổ sung test với Pathfinder thật.
"""

from src.experiments.time_demo import distinct_routes, time_dependence_demo
from src.mocks import MockTrafficProvider
from src.timeutil import parse_hhmm
from tests.fake_pathfinder import FakePathfinder


def test_rush_hour_costs_more(mock_graph):
    pf = FakePathfinder(mock_graph, MockTrafficProvider(rush_factor=0.5))
    times = [parse_hhmm("05:00"), parse_hhmm("07:30"), parse_hhmm("12:00")]
    rows = time_dependence_demo(pf, "A", "F", times)
    off_peak, rush, noon = (r["cost_s"] for r in rows)
    assert rush > off_peak
    assert off_peak == noon == 180.0
    assert [r["departure_hhmm"] for r in rows] == ["05:00", "07:30", "12:00"]
    assert all(r["mode"] == "dynamic_ub" for r in rows)


def test_route_changed_flag_and_distinct_routes(mock_graph):
    pf = FakePathfinder(mock_graph, MockTrafficProvider())
    rows = time_dependence_demo(pf, "A", "F", [0.0, 3600.0], mode="zero")
    assert [r["route_changed"] for r in rows] == [False, False]
    routes = distinct_routes(rows)
    assert len(routes) == 1
    assert routes[0][0] == "00:00, 01:00"


def test_no_path_rows(mock_graph):
    pf = FakePathfinder(mock_graph, MockTrafficProvider())
    rows = time_dependence_demo(pf, "A", "G", [0.0])
    assert rows[0]["found"] is False
    assert rows[0]["cost_s"] == ""
    assert distinct_routes(rows) == []
