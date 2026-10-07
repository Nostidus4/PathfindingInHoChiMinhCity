"""Owner: P5.

zero, static_vmax, dynamic_ub không có vi phạm admissibility trên mock
(và trên graph thật khi WP2 commit graph.json — dùng cùng hàm này).
Kèm ca ngược: heuristic cố tình overestimate phải BỊ phát hiện, nếu không thì
validator "đạt" cũng không có giá trị gì.
"""

from __future__ import annotations

import pytest

from src.cost.edge_cost import make_edge_cost
from src.cost.heuristics import make_heuristic
from src.search.dijkstra import true_cost
from src.timeutil import time_grid
from src.traffic.speed_bounds import compute_speed_bounds
from src.traffic.synthetic import SyntheticProvider
from src.validation.admissibility import check_admissibility

ADMISSIBLE_MODES = ("zero", "static_vmax", "dynamic_ub")


@pytest.fixture
def setup(mock_graph, cfg):
    provider = SyntheticProvider(mock_graph, cfg, seed=cfg.seed)
    bounds = compute_speed_bounds(mock_graph, provider, cfg)
    cost = make_edge_cost(provider)
    times = time_grid(cfg.window_start_s, cfg.window_end_s, 3600)
    goals = sorted(p.id for p in mock_graph.nodes())
    return mock_graph, bounds, cost, goals, times


@pytest.mark.parametrize("mode", ADMISSIBLE_MODES)
def test_admissible_modes_have_no_violations(setup, cfg, mode):
    graph, bounds, cost, goals, times = setup
    h = make_heuristic(mode, graph, bounds, {"w": cfg.weight_w})
    assert check_admissibility(graph, h, cost, goals, times) == []


def test_overestimating_heuristic_is_detected(setup):
    """Phủ định: h = 10x true cost phải sinh vi phạm, kèm đủ thông tin để sửa."""
    graph, _, cost, goals, times = setup

    def inflated(node, goal, t):
        return 10.0 * true_cost(graph, node, goal, t, cost) if node != goal else 0.0

    violations = check_admissibility(graph, inflated, cost, goals, times)
    assert violations
    for node, goal, _t, h, true in violations:
        assert node != goal
        assert h > true
        assert h == pytest.approx(10.0 * true)


def test_dynamic_weighted_violates_admissibility(setup, cfg):
    """w > 1 trên v_mean (không phải chặn trên) -> không admissible. Đây là chủ ý."""
    graph, bounds, cost, goals, times = setup
    h = make_heuristic("dynamic_weighted", graph, bounds, {"w": cfg.weight_w})
    assert check_admissibility(graph, h, cost, goals, times)


def test_unreachable_pairs_are_skipped_not_reported(setup):
    """A -> G không có đường: true = +inf nên mọi h hữu hạn đều hợp lệ."""
    graph, _, cost, _, times = setup

    def big_for_g(node, goal, t):
        return 0.0 if node == goal else 1e9

    # Chỉ goal G: mọi node (trừ G) đều không tới được G.
    assert check_admissibility(graph, big_for_g, cost, ["G"], times) == []
    # Còn với goal tới được thì cùng heuristic đó phải bị bắt lỗi.
    assert check_admissibility(graph, big_for_g, cost, ["F"], times)


def test_rejects_empty_or_unknown_inputs(setup):
    graph, bounds, cost, goals, times = setup
    h = make_heuristic("zero", graph, bounds)
    with pytest.raises(ValueError, match="ít nhất một goal"):
        check_admissibility(graph, h, cost, [], times)
    with pytest.raises(ValueError, match="ít nhất một goal"):
        check_admissibility(graph, h, cost, goals, [])
    with pytest.raises(ValueError, match="không có trong graph"):
        check_admissibility(graph, h, cost, ["ZZZ"], times)
