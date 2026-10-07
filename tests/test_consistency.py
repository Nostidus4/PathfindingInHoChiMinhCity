"""Owner: P5.

zero, static_vmax, dynamic_ub consistent trên mọi edge x lưới thời gian.
Kèm ca ngược (heuristic lệch) và ca điều kiện biên h(goal, t) != 0.
"""

from __future__ import annotations

import pytest

from src.cost.edge_cost import make_edge_cost
from src.cost.heuristics import make_heuristic
from src.timeutil import time_grid
from src.traffic.speed_bounds import compute_speed_bounds
from src.traffic.synthetic import SyntheticProvider
from src.validation.consistency import GOAL_CHECK, check_consistency

CONSISTENT_MODES = ("zero", "static_vmax", "dynamic_ub")


@pytest.fixture
def setup(mock_graph, cfg):
    provider = SyntheticProvider(mock_graph, cfg, seed=cfg.seed)
    bounds = compute_speed_bounds(mock_graph, provider, cfg)
    cost = make_edge_cost(provider)
    times = time_grid(cfg.window_start_s, cfg.window_end_s, cfg.grid_step_s)
    goals = sorted(p.id for p in mock_graph.nodes())
    return mock_graph, bounds, cost, goals, times


@pytest.mark.parametrize("mode", CONSISTENT_MODES)
def test_consistent_modes_have_no_violations(setup, cfg, mode):
    graph, bounds, cost, goals, times = setup
    h = make_heuristic(mode, graph, bounds, {"w": cfg.weight_w})
    assert check_consistency(graph, h, cost, goals, times) == []


def test_dynamic_weighted_violates_consistency(setup, cfg):
    graph, bounds, cost, goals, times = setup
    h = make_heuristic("dynamic_weighted", graph, bounds, {"w": cfg.weight_w})
    violations = check_consistency(graph, h, cost, goals, times)
    assert violations
    for edge_id, _goal, _t, h_u, c, h_v in violations:
        assert h_u > c + h_v  # đúng dạng bất đẳng thức bị vi phạm
        assert edge_id in {e.id for e in graph.edges()} or edge_id == GOAL_CHECK


def test_nonzero_heuristic_at_goal_is_reported(setup):
    """h(goal, t) != 0 làm A* có thể dừng sai ở goal -> phải bị bắt riêng."""
    graph, _, cost, _, times = setup

    def never_zero(node, goal, t):
        return 5.0

    violations = check_consistency(graph, never_zero, cost, ["F"], times)
    boundary = [v for v in violations if v[0] == GOAL_CHECK]
    assert len(boundary) == len(times)
    for _, goal, _t, h_goal, c, h_v in boundary:
        assert (goal, h_goal, c, h_v) == ("F", 5.0, 0.0, 0.0)


def test_inconsistent_heuristic_is_detected(setup):
    """h nhảy bậc giữa hai node kề nhau -> vi phạm h(u) <= c + h(v)."""
    graph, _, cost, _, times = setup

    def spiky(node, goal, t):
        if node == goal:
            return 0.0
        return 1e6 if node == "A" else 0.0

    violations = check_consistency(graph, spiky, cost, ["F"], times)
    assert violations
    assert all(v[0] != GOAL_CHECK for v in violations)
    assert {v[0] for v in violations} <= {e.id for e in graph.edges() if e.source == "A"}


def test_rejects_empty_or_unknown_inputs(setup):
    graph, bounds, cost, goals, times = setup
    h = make_heuristic("zero", graph, bounds)
    with pytest.raises(ValueError, match="ít nhất một goal"):
        check_consistency(graph, h, cost, [], times)
    with pytest.raises(ValueError, match="không có trong graph"):
        check_consistency(graph, h, cost, ["ZZZ"], times)
