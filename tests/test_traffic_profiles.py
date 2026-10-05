"""Owner: P3. Profile rho(e, t) (WP3.2): nằm trong [0, 1], thay đổi theo giờ, loại đường, quận."""

from dataclasses import replace

import pytest

from src.models import RoadSegment
from src.timeutil import parse_hhmm
from src.traffic import profiles
from src.traffic.timeslots import TimeGrid
from tests.traffic_graph import make_traffic_graph


def _seg(road_type="primary", district="Quan 1") -> RoadSegment:
    return RoadSegment("u->v", "u", "v", 1000.0, road_type, district)


def test_peak_multiplier_is_highest_at_peak_centers(cfg):
    night = profiles.peak_multiplier(parse_hhmm("05:00"), cfg)
    for name in ("morning", "evening"):
        center = cfg.peaks[name].center_s
        assert profiles.peak_multiplier(center, cfg) >= cfg.peaks[name].amplitude
        assert profiles.peak_multiplier(center, cfg) > night


def test_rush_hours_denser_than_off_peak(cfg):
    seg = _seg()
    rho = {
        h: profiles.density_ratio(seg, parse_hhmm(h), cfg)
        for h in ("05:00", "07:30", "10:00", "12:00", "14:30", "17:30", "22:30")
    }
    assert rho["07:30"] > rho["10:00"] > rho["05:00"]
    assert rho["17:30"] > rho["14:30"]
    assert rho["17:30"] > rho["22:30"]
    assert rho["12:00"] > rho["05:00"]  # ban ngày đông hơn sáng sớm


def test_road_type_and_district_factors(cfg):
    t = parse_hhmm("17:30")
    assert profiles.density_ratio(_seg("primary"), t, cfg) > profiles.density_ratio(
        _seg("residential"), t, cfg
    )
    assert profiles.density_ratio(_seg(district="Quan 1"), t, cfg) > profiles.density_ratio(
        _seg(district="Binh Thanh"), t, cfg
    )
    # Loại đường / quận lạ dùng hệ số mặc định, không lỗi
    assert profiles.road_type_factor(_seg("unclassified"), cfg) == cfg.road_type_factor["default"]
    assert profiles.area_factor(_seg(district="Quan 7"), cfg) == 1.0


def test_density_ratio_in_unit_interval_everywhere(cfg):
    graph = make_traffic_graph(cfg)
    times = TimeGrid(0.0, 24 * 3600, 600).points()
    for e in graph.edges():
        for t in times:
            for noise in (0.9, 1.0, 1.1):
                assert 0.0 <= profiles.density_ratio(e, t, cfg, noise) <= 1.0


def test_density_ratio_is_clamped_to_one_when_factors_explode(cfg):
    heavy = replace(cfg, base_density_ratio=0.9)
    assert profiles.density_ratio(_seg(), parse_hhmm("17:30"), heavy) == 1.0


def test_density_ratio_interpolates_between_grid_points(cfg):
    seg = _seg()
    t0, t1 = parse_hhmm("07:00"), parse_hhmm("07:15")
    r0, r1 = profiles.density_ratio_at(seg, t0, cfg), profiles.density_ratio_at(seg, t1, cfg)
    assert profiles.density_ratio(seg, t0, cfg) == pytest.approx(r0)
    assert profiles.density_ratio(seg, (t0 + t1) / 2, cfg) == pytest.approx((r0 + r1) / 2)


def test_density_ratio_clamped_outside_window(cfg):
    seg = _seg()
    start = profiles.density_ratio(seg, cfg.window_start_s, cfg)
    end = profiles.density_ratio(seg, cfg.window_end_s, cfg)
    assert profiles.density_ratio(seg, parse_hhmm("02:00"), cfg) == start
    assert profiles.density_ratio(seg, parse_hhmm("23:45"), cfg) == end


def test_profile_is_smooth(cfg):
    """Chênh lệch rho giữa hai mốc 15 phút liền kề nhỏ (không nhảy đột ngột)."""
    for e in make_traffic_graph(cfg).edges():
        table = profiles.density_profile(e, cfg, noise_factor=1.1)
        assert max(abs(b - a) for a, b in zip(table, table[1:], strict=False)) < 0.06


def test_edge_noise_factor_is_deterministic_and_bounded():
    a = profiles.edge_noise_factor("A->B", 42, 0.1)
    assert a == profiles.edge_noise_factor("A->B", 42, 0.1)
    assert 0.9 <= a <= 1.1
    assert a != profiles.edge_noise_factor("A->B", 7, 0.1)
    assert a != profiles.edge_noise_factor("B->A", 42, 0.1)
    assert profiles.edge_noise_factor("A->B", 42, 0.0) == 1.0
