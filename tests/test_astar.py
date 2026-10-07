"""Owner: P5.

Trên mock: A->F ra đúng MOCK_OPTIMA (1800 m, 180 s); mode zero cho cùng cost với
Dijkstra ĐỘC LẬP; A->G trả found=False; expanded(dynamic_ub) <= expanded(zero).
Thêm các ca biên của engine: reopen, nhãn cũ, cạnh song song, cạnh bị chặn,
chu trình cost 0, start == goal, và dữ liệu sai phải báo ValueError.
"""

from __future__ import annotations

import math

import pytest

from src.cost.edge_cost import make_edge_cost
from src.graph.graph import Graph
from src.mocks import MOCK_NO_PATH, MOCK_OPTIMA, MockTrafficProvider
from src.models import POI, CostMode, RoadSegment
from src.search.astar import astar
from src.search.dijkstra import dijkstra, earliest_arrival_times, true_cost
from src.search.pathfinder import Pathfinder
from src.search.trace import TraceRecorder, format_trace
from src.timeutil import parse_hhmm
from src.traffic.synthetic import SyntheticProvider

T0 = parse_hhmm("08:00")
MODES = ("zero", "static_vmax", "dynamic_ub", "dynamic_weighted")


def zero_h(node, goal, t):
    return 0.0


def length_cost(segment, t):
    """Cost = chiều dài: tĩnh, nên đáp án tối ưu tính được bằng tay."""
    return float(segment.length_m)


def line_graph(specs, pois=None):
    """Graph nhỏ từ (edge_id, source, target, length_m); POI đặt trùng toạ độ."""
    names = sorted({n for _, u, v, _ in specs for n in (u, v)} | set(pois or ()))
    return Graph(
        [POI(n, f"POI {n}", 10.77, 106.70, "Quan 1") for n in names],
        [RoadSegment(eid, u, v, length) for eid, u, v, length in specs],
    )


@pytest.fixture
def cost(mock_provider):
    return make_edge_cost(mock_provider)


@pytest.fixture
def pf(mock_graph, cfg):
    return Pathfinder(mock_graph, SyntheticProvider(mock_graph, cfg, seed=cfg.seed), cfg)


# ------------------------------------------------------------------ đáp án mock


@pytest.mark.parametrize(("start", "goal"), sorted(MOCK_OPTIMA))
def test_matches_known_mock_optimum(mock_graph, cost, start, goal):
    path, distance_m, travel_s = MOCK_OPTIMA[(start, goal)]
    result = astar(mock_graph, start, goal, T0, cost, zero_h)
    assert result.found
    assert result.path == path
    assert result.total_cost == pytest.approx(travel_s)
    assert result.total_distance_m == pytest.approx(distance_m)
    assert result.arrival_time_s == pytest.approx(T0 + travel_s)
    assert result.travel_time_s == pytest.approx(travel_s)


def test_zero_mode_matches_independent_dijkstra(mock_graph, cost):
    """Phép kiểm chéo giữa hai cài đặt tách rời: A*(h=0) == Dijkstra độc lập.

    Mọi validator đều tin vào tính chất này, nên nó phải được kiểm tường minh.
    """
    ids = sorted(p.id for p in mock_graph.nodes())
    for start in ids:
        for goal in ids:
            for t in (0.0, T0, parse_hhmm("17:30")):
                a = astar(mock_graph, start, goal, t, cost, zero_h, None, "zero")
                d = dijkstra(mock_graph, start, goal, t, cost)
                assert a.found is d.found, (start, goal, t)
                if a.found:
                    assert a.total_cost == pytest.approx(d.total_cost), (start, goal, t)
                    assert a.total_distance_m == pytest.approx(d.total_distance_m)


def test_no_path_returns_found_false(mock_graph, cost):
    start, goal = MOCK_NO_PATH
    for result in (
        astar(mock_graph, start, goal, T0, cost, zero_h),
        dijkstra(mock_graph, start, goal, T0, cost),
    ):
        assert result.found is False
        assert result.path == []
        assert result.edges == []
        assert result.total_cost == math.inf
        assert result.expanded_nodes > 0  # vẫn quét hết thành phần liên thông


def test_admissible_heuristics_expand_at_most_as_many_nodes(pf):
    """dynamic_ub/static_vmax không được expand nhiều node hơn zero trên mock.

    Không phải định lý chung (xem docs/algorithm_walkthrough.md §4), nhưng đúng
    trên fixture này và là tiêu chí đạt của WP5.
    """
    ids = sorted(p.id for p in pf.graph.nodes())
    for start in ids:
        for goal in ids:
            baseline = pf.route(start, goal, T0, heuristic_mode="zero")
            for mode in ("static_vmax", "dynamic_ub"):
                guided = pf.route(start, goal, T0, heuristic_mode=mode)
                assert guided.found is baseline.found
                assert guided.expanded_nodes <= baseline.expanded_nodes, (start, goal, mode)
                if baseline.found:
                    assert guided.total_cost == pytest.approx(baseline.total_cost)


# ------------------------------------------------------- phụ thuộc thời gian


def test_cost_is_evaluated_at_arrival_time_not_departure(mock_graph):
    """Cạnh thứ hai phải được hỏi giá tại t0 + g(u), không phải tại t0."""
    seen: list[tuple[str, float]] = []
    provider = MockTrafficProvider()
    base = make_edge_cost(provider)

    def spy(segment, t):
        seen.append((segment.id, t))
        return base(segment, t)

    result = astar(mock_graph, "A", "F", T0, spy, zero_h)
    assert result.found
    # A->C dài 400 m ở 10 m/s = 40 s, nên cạnh C->B được hỏi giá lúc T0 + 40.
    assert ("C->B", T0 + 40.0) in seen
    assert ("C->B", T0) not in seen


def test_departure_time_changes_cost(mock_graph, cfg):
    """Giờ cao điểm phải đắt hơn giờ thấp điểm (rush_factor < 1)."""
    cost = make_edge_cost(MockTrafficProvider(rush_factor=0.5))
    off_peak = astar(mock_graph, "A", "F", parse_hhmm("05:00"), cost, zero_h)
    peak = astar(mock_graph, "A", "F", parse_hhmm("08:00"), cost, zero_h)
    assert peak.total_cost > off_peak.total_cost


# ------------------------------------------------------------------ ca biên


def test_start_equals_goal(mock_graph, cost):
    result = astar(mock_graph, "A", "A", T0, cost, zero_h, TraceRecorder())
    assert result.found
    assert result.path == ["A"]
    assert result.edges == []
    assert result.total_cost == 0.0
    assert result.total_distance_m == 0.0
    assert result.expanded_nodes == 1


def test_parallel_edges_pick_the_cheaper_one_and_report_it():
    """Hai cạnh cùng cặp node: edges/total_distance_m phải theo cạnh ĐƯỢC CHỌN."""
    graph = line_graph(
        [("slow", "S", "M", 900.0), ("fast", "S", "M", 100.0), ("out", "M", "G", 200.0)]
    )
    for result in (
        astar(graph, "S", "G", 0.0, length_cost, zero_h),
        dijkstra(graph, "S", "G", 0.0, length_cost),
    ):
        assert result.edges == ["fast", "out"]
        assert result.total_cost == pytest.approx(300.0)
        assert result.total_distance_m == pytest.approx(300.0)


def test_reopening_recovers_optimum_for_inconsistent_heuristic():
    """h admissible nhưng KHÔNG consistent: node B bị expand sớm rồi phải mở lại."""
    graph = line_graph(
        [
            ("S->A", "S", "A", 5.0),
            ("S->B", "S", "B", 1.0),
            ("B->A", "B", "A", 1.0),
            ("A->G", "A", "G", 10.0),
        ]
    )
    overrated = {"S": 0.0, "B": 10.0, "A": 0.0, "G": 0.0}

    def h(node, goal, t):
        return overrated[node]

    recorder = TraceRecorder()
    result = astar(graph, "S", "G", 0.0, length_cost, h, recorder)
    assert result.path == ["S", "B", "A", "G"]
    assert result.total_cost == pytest.approx(12.0)
    assert any(s.note == "reopen" for s in recorder.steps)
    # Đáp án trùng oracle độc lập, tức reopening đã khôi phục đúng tối ưu.
    assert dijkstra(graph, "S", "G", 0.0, length_cost).total_cost == pytest.approx(12.0)


def test_zero_cost_cycle_terminates():
    specs = [("S->A", "S", "A", 0.0), ("A->S", "A", "S", 0.0), ("A->G", "A", "G", 1.0)]
    graph = line_graph(specs)
    result = astar(graph, "S", "G", 0.0, length_cost, zero_h)
    assert result.found
    assert result.total_cost == pytest.approx(1.0)


def test_blocked_edge_is_skipped_and_can_make_goal_unreachable(mock_graph):
    assert astar(mock_graph, "A", "F", T0, lambda e, t: math.inf, zero_h).found is False

    def block_direct(segment, t):
        return math.inf if segment.id == "B->D" else float(segment.length_m)

    result = astar(mock_graph, "A", "F", T0, block_direct, zero_h)
    assert result.found
    assert "B->D" not in result.edges


def test_stale_labels_are_skipped_not_expanded_twice(mock_graph, cost):
    """Số lần expand không được vượt số node: nhãn cũ phải bị loại khi pop."""
    recorder = TraceRecorder()
    result = astar(mock_graph, "A", "F", T0, cost, zero_h, recorder)
    expands = [s for s in recorder.steps if s.action == "expand"]
    assert len(expands) == result.expanded_nodes
    assert len(expands) <= len(mock_graph.nodes())
    assert len({s.node for s in expands}) == len(expands)  # consistent h -> không reopen
    assert any(s.action == "skip" for s in recorder.steps)


# ------------------------------------------------------------- trace và lỗi


def test_trace_is_off_by_default_and_consistent_when_on(mock_graph, cost):
    assert astar(mock_graph, "A", "F", T0, cost, zero_h).trace == []
    recorder = TraceRecorder()
    result = astar(mock_graph, "A", "F", T0, cost, zero_h, recorder)
    assert result.trace == recorder.steps
    for step in result.trace:
        assert step.f == pytest.approx(step.g + step.h)
        assert step.t == pytest.approx(T0 + step.g)
        assert step.action in {"expand", "push", "update", "skip"}
    table = format_trace(result.trace)
    assert "expand" in table and "lần expand" in table
    assert format_trace([]).startswith("(không có bước nào")


def test_trace_respects_max_steps(mock_graph, cost):
    recorder = TraceRecorder(max_steps=3)
    astar(mock_graph, "A", "F", T0, cost, zero_h, recorder)
    assert len(recorder.steps) == 3


@pytest.mark.parametrize("bad", [-1.0, float("nan")])
def test_invalid_edge_cost_raises(mock_graph, bad):
    with pytest.raises(ValueError, match="edge_cost"):
        astar(mock_graph, "A", "F", T0, lambda e, t: bad, zero_h)
    with pytest.raises(ValueError, match="edge_cost"):
        dijkstra(mock_graph, "A", "F", T0, lambda e, t: bad)


@pytest.mark.parametrize("bad", [-1.0, float("nan"), float("inf")])
def test_invalid_heuristic_raises(mock_graph, cost, bad):
    with pytest.raises(ValueError, match="heuristic"):
        astar(mock_graph, "A", "F", T0, cost, lambda n, g, t: bad)


def test_nonzero_heuristic_at_goal_raises(mock_graph, cost):
    with pytest.raises(ValueError, match="heuristic\\(goal, goal, t\\) phải bằng 0"):
        astar(mock_graph, "A", "F", T0, cost, lambda n, g, t: 1.0)


def test_unknown_node_raises(mock_graph, cost):
    with pytest.raises(ValueError, match="start"):
        astar(mock_graph, "ZZZ", "F", T0, cost, zero_h)
    with pytest.raises(ValueError, match="goal"):
        dijkstra(mock_graph, "A", "ZZZ", T0, cost)


def test_negative_departure_time_raises(mock_graph, cost):
    with pytest.raises(ValueError, match="departure_time"):
        astar(mock_graph, "A", "F", -1.0, cost, zero_h)


def test_incoming_edge_from_get_neighbors_raises():
    """Graph trả cạnh đi vào sẽ làm A* đi ngược chiều -> phải bị chặn ngay."""
    graph = line_graph([("S->M", "S", "M", 10.0), ("M->G", "M", "G", 10.0)])

    class WrongGraph:
        def nodes(self):
            return graph.nodes()

        def edges(self):
            return graph.edges()

        def get_neighbors(self, node):
            return graph.get_in_edges(node)

    with pytest.raises(ValueError, match="chỉ được trả cạnh đi ra"):
        astar(WrongGraph(), "G", "S", 0.0, length_cost, zero_h)


# ------------------------------------------------- oracle một-tới-mọi node


def test_earliest_arrival_times_matches_per_goal_dijkstra(mock_graph, cost):
    reachable = earliest_arrival_times(mock_graph, "A", T0, cost)
    assert reachable["A"] == 0.0
    assert "G" not in reachable  # G chỉ có cạnh một chiều G->A
    for goal, g in reachable.items():
        assert g == pytest.approx(true_cost(mock_graph, "A", goal, T0, cost))
    assert true_cost(mock_graph, "A", "G", T0, cost) == math.inf


# ------------------------------------------------------------- Pathfinder


def test_pathfinder_rejects_bad_input(pf):
    with pytest.raises(ValueError, match="không tồn tại"):
        pf.route("ZZZ", "F", T0)
    with pytest.raises(ValueError, match="Heuristic không hợp lệ"):
        pf.route("A", "F", T0, heuristic_mode="magic")
    with pytest.raises(ValueError, match="CostMode không hợp lệ"):
        pf.route("A", "F", T0, cost_mode="magic")


def test_pathfinder_caches_heuristics_and_labels_result(pf):
    assert pf.heuristic("dynamic_ub") is pf.heuristic("dynamic_ub")
    result = pf.route("A", "F", T0, heuristic_mode="dynamic_ub", trace=True)
    assert result.heuristic_mode == "dynamic_ub"
    assert result.cost_mode is CostMode.TIME
    assert result.trace and result.runtime_ms >= 0.0


def test_pathfinder_distance_mode_minimises_metres_and_keeps_real_eta(pf):
    by_time = pf.route("A", "F", T0, heuristic_mode="dynamic_ub")
    by_distance = pf.route("A", "F", T0, cost_mode=CostMode.DISTANCE)
    assert by_distance.cost_mode is CostMode.DISTANCE
    # total_cost là MÉT ở mode này và bằng đúng tổng chiều dài tuyến.
    assert by_distance.total_cost == pytest.approx(by_distance.total_distance_m)
    assert by_distance.total_distance_m == pytest.approx(MOCK_OPTIMA[("A", "F")][1])
    assert by_distance.total_distance_m <= by_time.total_distance_m
    # ETA được tính lại bằng chi phí thời gian, nên tuyến ngắn hơn vẫn có thể lâu hơn.
    assert by_distance.arrival_time_s > T0
    assert by_distance.travel_time_s >= by_time.travel_time_s
