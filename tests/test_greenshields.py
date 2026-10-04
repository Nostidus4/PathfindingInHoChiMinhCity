"""Owner: P3. Hàm thuần Greenshields: q = k * v; v(0) = v_free; v(k_jam) = v_min; capacity."""

import pytest

from src.traffic import greenshields as gs

V_FREE, K_JAM, V_MIN = 50.0, 150.0, 5.0


def test_speed_at_zero_density_is_free_flow():
    assert gs.speed(0.0, V_FREE, K_JAM) == V_FREE


def test_speed_at_jam_density_is_floored_at_v_min():
    assert gs.speed(K_JAM, V_FREE, K_JAM) == 0.0
    assert gs.speed(K_JAM, V_FREE, K_JAM, V_MIN) == V_MIN


def test_speed_is_linear_in_density():
    assert gs.speed(K_JAM / 2, V_FREE, K_JAM) == pytest.approx(V_FREE / 2)
    assert gs.speed(30.0, V_FREE, K_JAM) == pytest.approx(V_FREE * (1 - 30.0 / K_JAM))


def test_density_outside_range_is_clamped():
    assert gs.speed(-10.0, V_FREE, K_JAM) == V_FREE
    assert gs.speed(2 * K_JAM, V_FREE, K_JAM, V_MIN) == V_MIN
    assert gs.flow(-10.0, V_FREE, K_JAM) == 0.0


@pytest.mark.parametrize("k", [0.0, 10.0, 75.0, 120.0, 149.0, 150.0])
def test_flow_equals_density_times_speed(k):
    assert gs.flow(k, V_FREE, K_JAM, V_MIN) == pytest.approx(k * gs.speed(k, V_FREE, K_JAM, V_MIN))


def test_capacity_is_max_flow_at_half_jam_density():
    cap = gs.capacity(V_FREE, K_JAM)
    assert cap == pytest.approx(V_FREE * K_JAM / 4)
    assert gs.flow(K_JAM / 2, V_FREE, K_JAM) == pytest.approx(cap)
    for k in range(0, 151, 5):
        assert gs.flow(float(k), V_FREE, K_JAM, V_MIN) <= cap + 1e-9


def test_density_from_ratio_clamps_to_unit_interval():
    assert gs.density_from_ratio(0.4, K_JAM) == pytest.approx(60.0)
    assert gs.density_from_ratio(-0.1, K_JAM) == 0.0
    assert gs.density_from_ratio(1.5, K_JAM) == K_JAM


def test_state_from_ratio_is_consistent():
    s = gs.state_from_ratio(0.3, V_FREE, K_JAM, V_MIN)
    assert s.density_veh_km == pytest.approx(45.0)
    assert s.speed_kmh == pytest.approx(35.0)
    assert s.flow_veh_h == pytest.approx(45.0 * 35.0)
    assert s.capacity_veh_h == pytest.approx(gs.capacity(V_FREE, K_JAM))


@pytest.mark.parametrize("v_free, k_jam", [(0.0, 150.0), (50.0, 0.0), (-1.0, 150.0)])
def test_invalid_parameters_raise(v_free, k_jam):
    with pytest.raises(ValueError):
        gs.speed(10.0, v_free, k_jam)
