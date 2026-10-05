"""Owner: P3.

v_ub(t) không tăng theo t; v_ub(t) >= mọi tốc độ thật tại mọi t' >= t; v_max >= mọi tốc độ;
v_mean nằm giữa min và max; heuristic dynamic_ub của P4 với SpeedBounds thật vẫn consistent.
"""

from dataclasses import replace

import pytest

from src.cost.edge_cost import make_edge_cost
from src.cost.heuristics import make_heuristic
from src.cost.speed_model import effective_speed
from src.mocks import MockTrafficProvider
from src.timeutil import parse_hhmm
from src.traffic.speed_bounds import SpeedBounds, compute_speed_bounds
from src.traffic.synthetic import SyntheticProvider
from src.traffic.timeslots import TimeGrid
from tests.traffic_graph import make_traffic_graph

FINE_TIMES = TimeGrid(0.0, 24 * 3600, 300).points()


@pytest.fixture
def graph(cfg):
    return make_traffic_graph(cfg)


@pytest.fixture
def provider(graph, cfg):
    return SyntheticProvider(graph, cfg, seed=42)


@pytest.fixture
def bounds(graph, provider, cfg) -> SpeedBounds:
    return compute_speed_bounds(graph, provider, cfg)


def test_table_shapes(bounds, cfg):
    n = TimeGrid.from_config(cfg).n_points
    assert len(bounds.v_ub_kmh) == len(bounds.v_mean_kmh) == len(bounds.v_now_max_kmh) == n
    assert bounds.grid_times()[0] == cfg.window_start_s
    assert bounds.grid_times()[-1] == cfg.window_end_s


def test_v_ub_non_increasing(bounds):
    ub = [bounds.v_ub(t) for t in FINE_TIMES]
    assert all(b <= a + 1e-12 for a, b in zip(ub, ub[1:], strict=False))


def test_v_ub_dominates_all_future_speeds(graph, provider, bounds):
    """v_ub(t) >= speed(e, t') với mọi e, mọi t' >= t (kiểm trên lưới 5 phút, kể cả giữa mốc)."""
    now_max = [
        max(provider.get_traffic(e.id, t).speed_kmh for e in graph.edges()) for t in FINE_TIMES
    ]
    suffix = now_max[:]
    for i in range(len(suffix) - 2, -1, -1):
        suffix[i] = max(suffix[i], suffix[i + 1])
    for t, future_max in zip(FINE_TIMES, suffix, strict=True):
        assert bounds.v_ub(t) >= future_max - 1e-9, f"v_ub({t}) < {future_max}"


def test_v_max_dominates_everything(graph, provider, bounds, cfg):
    assert bounds.v_max_kmh == pytest.approx(max(bounds.v_ub_kmh))
    assert bounds.v_max_kmh <= cfg.v_max_kmh
    for e in graph.edges():
        for t in FINE_TIMES:
            assert provider.get_traffic(e.id, t).speed_kmh <= bounds.v_max_kmh + 1e-9


def test_network_max_speed_and_mean(graph, provider, bounds, cfg):
    for t in TimeGrid.from_config(cfg).points():
        speeds = [provider.get_traffic(e.id, t).speed_kmh for e in graph.edges()]
        assert bounds.network_max_speed(t) == pytest.approx(max(speeds))
        assert bounds.v_mean(t) == pytest.approx(sum(speeds) / len(speeds))
        assert min(speeds) <= bounds.v_mean(t) <= bounds.network_max_speed(t) <= bounds.v_ub(t)


def test_v_mean_drops_at_rush_hour(bounds):
    assert bounds.v_mean(parse_hhmm("17:30")) < bounds.v_mean(parse_hhmm("05:00"))
    assert bounds.v_mean(parse_hhmm("07:30")) < bounds.v_mean(parse_hhmm("10:00"))


def test_v_ub_is_time_dependent_when_late_window_is_congested(graph, cfg):
    """Cửa sổ kết thúc lúc cao điểm chiều -> suffix max giảm dần, v_ub thực sự phụ thuộc t."""
    short = replace(cfg, window_end_s=parse_hhmm("17:30"))
    b = compute_speed_bounds(graph, SyntheticProvider(graph, short), short)
    assert b.v_ub(parse_hhmm("17:00")) < b.v_ub(parse_hhmm("06:00"))


def test_speed_fn_hook_uses_effective_speed(graph, provider, cfg, bounds):
    b = compute_speed_bounds(
        graph, provider, cfg, speed_fn=lambda s, e: effective_speed(s, e) * 3.6
    )
    assert b.v_max_kmh == pytest.approx(bounds.v_max_kmh)


def test_works_with_mock_provider(mock_graph, cfg):
    b = compute_speed_bounds(mock_graph, MockTrafficProvider(rush_factor=0.5), cfg)
    assert b.v_max_kmh == pytest.approx(36.0)
    assert b.v_mean(parse_hhmm("08:00")) == pytest.approx(18.0)


def test_empty_graph_raises(cfg):
    class Empty:
        def edges(self):
            return []

    with pytest.raises(ValueError):
        compute_speed_bounds(Empty(), MockTrafficProvider(), cfg)


@pytest.mark.parametrize("window_end", ["23:00", "17:30"])
def test_dynamic_ub_consistent_on_mock_graph(mock_graph, cfg, window_end):
    """Tích hợp với heuristic của P4: h(u, t) <= c(u, v, t) + h(v, t + c) trên mọi edge x giờ."""
    c = replace(cfg, window_end_s=parse_hhmm(window_end))
    provider = SyntheticProvider(mock_graph, c)
    h = make_heuristic("dynamic_ub", mock_graph, compute_speed_bounds(mock_graph, provider, c))
    cost = make_edge_cost(provider)
    for goal in (p.id for p in mock_graph.nodes()):
        for e in mock_graph.edges():
            for t in TimeGrid(0.0, 24 * 3600, 600).points():
                ce = cost(e, t)
                assert h(e.source, goal, t) <= ce + h(e.target, goal, t + ce) + 1e-6
