"""Unit tests cho 4 heuristic của WP4.

Dùng FakeBounds thay cho SpeedBounds thật để WP4 có thể test độc lập trong lúc
WP3 vẫn đang implement traffic/speed_bounds.py.
"""

from dataclasses import dataclass

import pytest

from src.cost.heuristics import HEURISTIC_MODES, make_heuristic
from src.cost.heuristics.dynamic_ub import DynamicUBHeuristic
from src.cost.heuristics.dynamic_weighted import DynamicWeightedHeuristic
from src.cost.heuristics.static_vmax import StaticVmaxHeuristic
from src.cost.heuristics.zero import ZeroHeuristic
from src.cost.speed_model import kmh_to_ms
from src.timeutil import parse_hhmm


@dataclass(frozen=True)
class FakeBounds:
    v_max_kmh: float = 54.0

    def v_ub(self, t: float) -> float:
        # Chặn trên giảm sau 12:00 để kiểm h(node, goal, t) thực sự phụ thuộc t.
        return 54.0 if t < parse_hhmm("12:00") else 36.0

    def v_mean(self, t: float) -> float:
        return 30.0 if t < parse_hhmm("12:00") else 20.0


@pytest.fixture
def bounds() -> FakeBounds:
    return FakeBounds()


def test_registry_exposes_exactly_four_modes() -> None:
    assert HEURISTIC_MODES == ("zero", "static_vmax", "dynamic_ub", "dynamic_weighted")


def test_make_heuristic_creates_all_four_modes(mock_graph, bounds) -> None:
    assert isinstance(make_heuristic("zero", mock_graph, bounds), ZeroHeuristic)
    assert isinstance(make_heuristic("static_vmax", mock_graph, bounds), StaticVmaxHeuristic)
    assert isinstance(make_heuristic("dynamic_ub", mock_graph, bounds), DynamicUBHeuristic)
    assert isinstance(
        make_heuristic("dynamic_weighted", mock_graph, bounds), DynamicWeightedHeuristic
    )


def test_invalid_mode_raises_value_error(mock_graph, bounds) -> None:
    with pytest.raises(ValueError, match="Heuristic không hợp lệ"):
        make_heuristic("not-a-mode", mock_graph, bounds)


def test_zero_is_always_zero(mock_graph) -> None:
    h = make_heuristic("zero", mock_graph)
    assert h("A", "F", parse_hhmm("08:00")) == 0.0
    assert h("A", "F", parse_hhmm("18:00")) == 0.0


@pytest.mark.parametrize("mode", HEURISTIC_MODES)
def test_all_heuristics_are_zero_at_goal(mock_graph, bounds, mode: str) -> None:
    h = make_heuristic(mode, mock_graph, bounds)
    assert h("F", "F", parse_hhmm("08:00")) == pytest.approx(0.0)


@pytest.mark.parametrize("mode", HEURISTIC_MODES)
def test_all_heuristics_are_non_negative(mock_graph, bounds, mode: str) -> None:
    h = make_heuristic(mode, mock_graph, bounds)
    assert h("A", "F", parse_hhmm("08:00")) >= 0.0


def test_static_vmax_formula(mock_graph, bounds) -> None:
    h = StaticVmaxHeuristic(mock_graph, bounds)
    expected = h.dist_m("A", "F") / kmh_to_ms(bounds.v_max_kmh)
    assert h("A", "F", parse_hhmm("08:00")) == pytest.approx(expected)
    assert h("A", "F", parse_hhmm("18:00")) == pytest.approx(expected)


def test_dynamic_ub_changes_with_time(mock_graph, bounds) -> None:
    h = DynamicUBHeuristic(mock_graph, bounds)
    morning = h("A", "F", parse_hhmm("08:00"))
    evening = h("A", "F", parse_hhmm("18:00"))

    # v_ub giảm từ 54 xuống 36 km/h => lower bound thời gian tăng.
    assert evening > morning


def test_dynamic_weighted_uses_weight_and_mean_speed(mock_graph, bounds) -> None:
    h = DynamicWeightedHeuristic(mock_graph, bounds, w=1.5)
    t = parse_hhmm("08:00")
    expected = 1.5 * h.dist_m("A", "F") / kmh_to_ms(bounds.v_mean(t))
    assert h("A", "F", t) == pytest.approx(expected)


def test_dynamic_weighted_requires_weight_above_one(mock_graph, bounds) -> None:
    with pytest.raises(ValueError, match="w > 1"):
        DynamicWeightedHeuristic(mock_graph, bounds, w=1.0)


@pytest.mark.parametrize("mode", ("static_vmax", "dynamic_ub", "dynamic_weighted"))
def test_speed_bound_heuristics_require_bounds(mock_graph, mode: str) -> None:
    with pytest.raises(ValueError, match="SpeedBounds"):
        make_heuristic(mode, mock_graph, bounds=None)
