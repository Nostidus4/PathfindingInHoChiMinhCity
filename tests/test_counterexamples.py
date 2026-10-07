"""Owner: P5.

find_counterexamples chạy được; mọi ca tìm được thật sự có cost_A* > cost_Dijkstra
(kiểm lại bằng Dijkstra ĐỘC LẬP, không tin vào số do pathfinder trả về).
"""

from __future__ import annotations

import pytest

from src.cost.edge_cost import make_edge_cost
from src.experiments.scenarios import DEFAULT_TIMES, random_scenarios
from src.search.dijkstra import dijkstra
from src.search.pathfinder import Pathfinder
from src.timeutil import parse_hhmm
from src.traffic.synthetic import SyntheticProvider
from src.validation.counterexamples import find_counterexamples


@pytest.fixture
def pf(mock_graph, cfg):
    return Pathfinder(mock_graph, SyntheticProvider(mock_graph, cfg, seed=cfg.seed), cfg)


@pytest.fixture
def scenarios(mock_graph, cfg):
    return random_scenarios(mock_graph, 300, DEFAULT_TIMES, cfg.seed)


def test_dynamic_weighted_has_at_least_one_counterexample(pf, scenarios):
    """Tiêu chí đạt của WP5: phải chứng minh được heuristic không admissible mất tối ưu."""
    assert find_counterexamples(pf, scenarios, "dynamic_weighted")


def test_every_counterexample_is_real(pf, scenarios, mock_graph, mock_provider):
    """Chi phí "tối ưu" trong báo cáo phải khớp Dijkstra độc lập, và A* phải tệ hơn thật."""
    cost = make_edge_cost(pf.provider)
    found = find_counterexamples(pf, scenarios, "dynamic_weighted")
    for case in found:
        start, goal, t = case["start"], case["goal"], case["departure"]
        oracle = dijkstra(mock_graph, start, goal, t, cost)
        assert oracle.found
        assert case["optimal_cost"] == pytest.approx(oracle.total_cost)
        assert case["astar_cost"] > case["optimal_cost"]
        assert case["excess_s"] == pytest.approx(case["astar_cost"] - case["optimal_cost"])
        assert case["excess_pct"] > 0.0
        assert case["astar_path"] != case["optimal_path"]
        assert case["optimal_path"] == oracle.path
        assert case["mode"] == "dynamic_weighted"


def test_admissible_modes_have_no_counterexamples(pf, scenarios):
    for mode in ("zero", "static_vmax", "dynamic_ub"):
        assert find_counterexamples(pf, scenarios, mode) == []


def test_unreachable_pairs_are_skipped(pf):
    """A -> G không có đường: không kết luận được gì, không được coi là vi phạm."""
    assert find_counterexamples(pf, [("A", "G", parse_hhmm("08:00"))]) == []


def test_empty_scenarios(pf):
    assert find_counterexamples(pf, []) == []
