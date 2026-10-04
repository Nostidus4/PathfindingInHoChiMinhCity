"""Owner: P3. Xử lý thời gian WP3.4: lưới 15 phút, nội suy tuyến tính, clamp ngoài cửa sổ."""

import math

import pytest

from src.timeutil import parse_hhmm
from src.traffic.timeslots import TimeGrid, interpolate_on_grid


@pytest.fixture
def grid(cfg) -> TimeGrid:
    return TimeGrid.from_config(cfg)


def test_grid_from_default_config(grid):
    assert grid.start_s == parse_hhmm("05:00")
    assert grid.step_s == 900
    assert grid.n_points == 18 * 4 + 1
    assert grid.last_s == parse_hhmm("23:00")
    assert grid.points()[:2] == [parse_hhmm("05:00"), parse_hhmm("05:15")]
    assert len(grid.points()) == grid.n_points


def test_normalize_time_clamps_outside_window(grid):
    assert grid.normalize_time(parse_hhmm("03:00")) == grid.start_s
    assert grid.normalize_time(parse_hhmm("23:59")) == grid.last_s
    assert grid.normalize_time(26 * 3600) == grid.last_s  # qua nửa đêm: không quay vòng
    assert grid.normalize_time(parse_hhmm("08:10")) == parse_hhmm("08:10")
    with pytest.raises(ValueError):
        grid.normalize_time(math.nan)


def test_get_time_slot(grid):
    assert grid.get_time_slot(parse_hhmm("05:00")) == (0, 0.0)
    i, frac = grid.get_time_slot(parse_hhmm("05:20"))
    assert i == 1 and frac == pytest.approx(1 / 3)
    assert grid.get_time_slot(parse_hhmm("23:00")) == (grid.n_points - 1, 0.0)
    assert grid.get_time_slot(0.0) == (0, 0.0)


def test_interpolation_midpoint_and_exact_points():
    values = [10.0, 20.0, 40.0]
    assert interpolate_on_grid(values, 0.0, 900, 0.0) == 10.0
    assert interpolate_on_grid(values, 0.0, 900, 450.0) == pytest.approx(15.0)
    assert interpolate_on_grid(values, 0.0, 900, 900.0) == 20.0
    assert interpolate_on_grid(values, 0.0, 900, 1575.0) == pytest.approx(35.0)


def test_interpolation_clamps_to_boundary_values():
    values = [10.0, 20.0, 40.0]
    assert interpolate_on_grid(values, 0.0, 900, -500.0) == 10.0
    assert interpolate_on_grid(values, 0.0, 900, 10_000.0) == 40.0


def test_interpolation_rejects_bad_input(grid):
    with pytest.raises(ValueError):
        interpolate_on_grid([], 0.0, 900, 0.0)
    with pytest.raises(ValueError):
        interpolate_on_grid([1.0, 2.0], 0.0, 900, math.nan)
    with pytest.raises(ValueError):
        grid.interpolate([1.0, 2.0], 0.0)  # sai số phần tử so với lưới


def test_invalid_grid_raises():
    with pytest.raises(ValueError):
        TimeGrid(0.0, 100.0, 0)
    with pytest.raises(ValueError):
        TimeGrid(100.0, 0.0, 900)
