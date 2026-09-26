"""Test tầng nền tảng (models, geo, timeutil, config, mocks). Owner: P6 + P5."""

import pytest

from src.geo import haversine_m
from src.mocks import MOCK_OPTIMA, MockGraph, MockTrafficProvider
from src.models import TrafficProvider
from src.timeutil import format_seconds, parse_hhmm


def test_haversine_known_distance():
    # 0.001 độ vĩ ~ 111 m
    assert haversine_m(10.77, 106.70, 10.771, 106.70) == pytest.approx(111.2, abs=0.5)


def test_parse_and_format_time():
    assert parse_hhmm("07:30") == 27000
    assert format_seconds(27000) == "07:30:00"
    with pytest.raises(ValueError):
        parse_hhmm("25:00")
    with pytest.raises(ValueError):
        parse_hhmm("abc")


def test_config_loads(cfg):
    assert cfg.grid_step_s == 900
    assert cfg.v_max_kmh >= cfg.free_flow_for("residential")
    assert "morning" in cfg.peaks


def test_mock_graph_length_ge_haversine(mock_graph: MockGraph):
    for e in mock_graph.edges():
        a, b = mock_graph.get_node(e.source), mock_graph.get_node(e.target)
        assert e.length_m >= haversine_m(a.lat, a.lon, b.lat, b.lon)


def test_mock_optimum_path_is_valid(mock_graph: MockGraph):
    path, length, _ = MOCK_OPTIMA[("A", "F")]
    total = 0.0
    for u, v in zip(path, path[1:], strict=False):
        total += mock_graph.get_edge(f"{u}->{v}").length_m
    assert total == length


def test_mock_provider_protocol_and_rush():
    p = MockTrafficProvider(rush_factor=0.5)
    assert isinstance(p, TrafficProvider)
    assert p.get_traffic("A->B", parse_hhmm("06:00")).speed_kmh == 36.0
    assert p.get_traffic("A->B", parse_hhmm("08:00")).speed_kmh == 18.0
