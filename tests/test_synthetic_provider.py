"""Owner: P3. SyntheticProvider (WP3.3 + WP3.5).

Tái lập theo seed; giá trị trong khoảng hợp lệ; flow = density * speed; thay đổi theo giờ;
nội suy giữa hai mốc; clamp ngoài cửa sổ; tương thích với speed_model/edge_cost của P4.
"""

from dataclasses import replace

import pytest

from src.cost.edge_cost import edge_cost
from src.cost.speed_model import effective_speed, kmh_to_ms
from src.models import TrafficProvider
from src.timeutil import parse_hhmm
from src.traffic import greenshields
from src.traffic.checks import check_traffic_states
from src.traffic.synthetic import SyntheticProvider
from src.traffic.timeslots import TimeGrid
from tests.traffic_graph import make_traffic_graph

FINE_TIMES = TimeGrid(0.0, 24 * 3600, 300).points()  # 5 phút, phủ cả ngoài cửa sổ


@pytest.fixture
def graph(cfg):
    return make_traffic_graph(cfg)


@pytest.fixture
def provider(graph, cfg) -> SyntheticProvider:
    return SyntheticProvider(graph, cfg, seed=42)


def _all_states(graph, provider, times):
    return [provider.get_traffic(e.id, t) for e in graph.edges() for t in times]


def test_implements_traffic_provider_protocol(provider):
    assert isinstance(provider, TrafficProvider)


def test_same_seed_same_states(graph, cfg, provider):
    other = SyntheticProvider(graph, cfg, seed=42)
    times = TimeGrid.from_config(cfg).points()
    assert _all_states(graph, provider, times) == _all_states(graph, other, times)


def test_different_seed_different_states(graph, cfg, provider):
    other = SyntheticProvider(graph, cfg, seed=7)
    t = [parse_hhmm("08:00")]
    assert _all_states(graph, provider, t) != _all_states(graph, other, t)


def test_seed_none_uses_config_seed(graph, cfg):
    a = SyntheticProvider(graph, cfg)
    b = SyntheticProvider(graph, cfg, seed=cfg.seed)
    assert a.seed == cfg.seed
    assert _all_states(graph, a, [parse_hhmm("08:00")]) == _all_states(
        graph, b, [parse_hhmm("08:00")]
    )


def test_noise_off_gives_identical_edges_of_same_class(graph, cfg):
    p = SyntheticProvider(graph, replace(cfg, edge_noise=0.0))
    t = parse_hhmm("17:30")
    assert p.get_traffic("primary-0-u->primary-0-v", t) == p.get_traffic(
        "primary-0-v->primary-0-u", t
    )


def test_traffic_values_valid_everywhere(graph, cfg, provider):
    """density >= 0, speed > 0, flow >= 0, flow = k * v, flow <= capacity (kèm edge + thời điểm)."""
    problems = check_traffic_states(graph, provider, FINE_TIMES, k_jam=cfg.k_jam_veh_km)
    assert problems == []


def test_density_ratio_in_unit_interval(graph, provider):
    for e in graph.edges():
        for t in FINE_TIMES:
            assert 0.0 <= provider.get_density_ratio(e.id, t) <= 1.0


def test_speed_bounded_by_free_flow_and_min_speed(graph, cfg, provider):
    for e in graph.edges():
        for t in FINE_TIMES:
            v = provider.get_traffic(e.id, t).speed_kmh
            assert cfg.min_speed_kmh <= v <= cfg.free_flow_for(e.road_type)


def test_rush_hour_slower_than_off_peak(graph, provider):
    for e in graph.edges():
        speed = {
            h: provider.get_traffic(e.id, parse_hhmm(h)).speed_kmh
            for h in ("05:00", "07:30", "10:00", "17:30", "22:30")
        }
        assert speed["07:30"] < speed["10:00"] < speed["05:00"]
        assert speed["17:30"] < speed["22:30"]
        state_peak = provider.get_traffic(e.id, parse_hhmm("17:30"))
        state_night = provider.get_traffic(e.id, parse_hhmm("05:00"))
        assert state_peak.density_veh_km > state_night.density_veh_km


def test_traffic_differs_between_edges(provider):
    t = parse_hhmm("17:30")
    q1 = provider.get_traffic("primary-1-u->primary-1-v", t)  # Quan 1
    bt = provider.get_traffic("primary-0-u->primary-0-v", t)  # Binh Thanh
    res = provider.get_traffic("residential-1-u->residential-1-v", t)
    assert q1.density_veh_km > bt.density_veh_km
    assert q1.speed_kmh != res.speed_kmh


def test_interpolation_between_slots(cfg, provider):
    """Tại giữa hai mốc: rho là trung bình hai mốc, và (k, v, q) vẫn đúng Greenshields."""
    eid = "primary-1-u->primary-1-v"
    t0, t1 = parse_hhmm("07:00"), parse_hhmm("07:15")
    mid = (t0 + t1) / 2
    r0, r1 = provider.get_density_ratio(eid, t0), provider.get_density_ratio(eid, t1)
    assert provider.get_density_ratio(eid, mid) == pytest.approx((r0 + r1) / 2)
    expected = greenshields.state_from_ratio(
        (r0 + r1) / 2, cfg.free_flow_for("primary"), cfg.k_jam_veh_km, cfg.min_speed_kmh
    )
    s = provider.get_traffic(eid, mid)
    assert s.density_veh_km == pytest.approx(expected.density_veh_km)
    assert s.speed_kmh == pytest.approx(expected.speed_kmh)
    assert s.flow_veh_h == pytest.approx(s.density_veh_km * s.speed_kmh)
    lo, hi = sorted(
        (provider.get_traffic(eid, t0).speed_kmh, provider.get_traffic(eid, t1).speed_kmh)
    )
    assert lo <= s.speed_kmh <= hi


def test_clamp_outside_simulation_window(cfg, provider):
    eid = "secondary-2-u->secondary-2-v"
    first = provider.get_traffic(eid, cfg.window_start_s)
    last = provider.get_traffic(eid, cfg.window_end_s)
    assert provider.get_traffic(eid, 0.0) == first
    assert provider.get_traffic(eid, parse_hhmm("04:59")) == first
    assert provider.get_traffic(eid, parse_hhmm("23:30")) == last
    assert provider.get_traffic(eid, 25 * 3600) == last


def test_unknown_edge_raises_key_error(provider):
    with pytest.raises(KeyError, match="không có trong graph"):
        provider.get_traffic("X->Y", 0.0)


def test_speed_table_matches_get_traffic(cfg, provider):
    table = provider.speed_table()
    grid = TimeGrid.from_config(cfg)
    eid = "tertiary-3-u->tertiary-3-v"
    assert len(table[eid]) == grid.n_points
    for t, v in zip(grid.points(), table[eid], strict=True):
        assert v == pytest.approx(provider.get_traffic(eid, t).speed_kmh)


def test_no_capacity_penalty_in_speed_model(graph, provider):
    """Greenshields giữ flow <= capacity nên v_eff của P4 đúng bằng speed_kmh của provider."""
    for e in graph.edges():
        for t in TimeGrid(0.0, 24 * 3600, 1800).points():
            s = provider.get_traffic(e.id, t)
            assert effective_speed(s, e) == pytest.approx(kmh_to_ms(s.speed_kmh))


def test_edge_cost_on_mock_graph_is_time_dependent(mock_graph, cfg):
    p = SyntheticProvider(mock_graph, cfg)
    seg = mock_graph.get_edge("A->B")
    assert edge_cost(seg, parse_hhmm("17:30"), p) > edge_cost(seg, parse_hhmm("05:00"), p)
