"""Owner: P3. FIFO: t1 < t2 => t1 + c(e, t1) <= t2 + c(e, t2) trên mọi edge.

check_fifo phát hiện được vi phạm (có edge + cặp thời điểm), và SyntheticProvider với
edge_cost của P4 không vi phạm, kể cả với cạnh dài và lưới mịn hơn lưới 15 phút.
"""

import pytest

from src.cost.edge_cost import make_edge_cost
from src.mocks import MockTrafficProvider
from src.timeutil import parse_hhmm
from src.traffic.synthetic import SyntheticProvider
from src.traffic.timeslots import TimeGrid
from src.validation.fifo import check_fifo, fifo_report
from tests.traffic_graph import make_traffic_graph

FINE_TIMES = TimeGrid(0.0, 24 * 3600, 60).points()  # 1 phút, kiểm cả bên trong ô 15 phút


def test_detects_violation_with_edge_and_times(mock_graph):
    # Đi lúc 08:00 mất 2 giờ, đi lúc 08:15 chỉ mất 1 phút -> đến sớm hơn: vi phạm FIFO.
    def bad_cost(segment, t):
        return 7200.0 if t < parse_hhmm("08:10") else 60.0

    times = [parse_hhmm("08:00"), parse_hhmm("08:15"), parse_hhmm("08:30")]
    violations = check_fifo(mock_graph, bad_cost, times)
    assert len(violations) == len(mock_graph.edges())
    edge_id, t1, t2 = violations[0]
    assert edge_id in {e.id for e in mock_graph.edges()}
    assert (t1, t2) == (parse_hhmm("08:00"), parse_hhmm("08:15"))


def test_constant_cost_never_violates(mock_graph):
    assert check_fifo(mock_graph, lambda s, t: 100.0, FINE_TIMES) == []


def test_unsorted_and_duplicate_times_are_handled(mock_graph):
    def bad_cost(segment, t):
        return 7200.0 if t < 1000 else 0.0

    assert check_fifo(mock_graph, bad_cost, [2000.0, 0.0, 2000.0]) != []
    assert check_fifo(mock_graph, bad_cost, [0.0]) == []


def test_step_traffic_breaks_fifo(mock_graph):
    """MockTrafficProvider đổi tốc độ đột ngột lúc 09:00 -> vi phạm FIFO ngay trước 09:00.

    Đây là lý do profile synthetic phải mượt (Gaussian + nội suy tuyến tính).
    """
    cost = make_edge_cost(MockTrafficProvider(rush_factor=0.5))
    violations = check_fifo(mock_graph, cost, FINE_TIMES)
    assert violations
    assert all(parse_hhmm("08:00") <= t1 < t2 <= parse_hhmm("09:00") for _, t1, t2 in violations)


def test_synthetic_provider_fifo_on_mock_graph(mock_graph, cfg):
    cost = make_edge_cost(SyntheticProvider(mock_graph, cfg))
    assert check_fifo(mock_graph, cost, FINE_TIMES) == []


@pytest.mark.parametrize("length_m", [500.0, 3000.0, 10_000.0])
def test_synthetic_provider_fifo_all_road_types_and_districts(cfg, length_m):
    graph = make_traffic_graph(cfg, length_m)
    cost = make_edge_cost(SyntheticProvider(graph, cfg))
    report = fifo_report(graph, cost, FINE_TIMES)
    assert report.ok, f"Vi phạm FIFO đầu tiên: {report.violations[:1]}"
    assert report.n_edges == len(graph.edges())
    assert report.n_checks == report.n_edges * (len(FINE_TIMES) - 1)
    assert report.min_slope > -1.0


def test_fifo_report_slope_statistics(mock_graph):
    def cost(segment, t):  # tăng rồi giảm, độ dốc +-0.5
        return 100.0 + 0.5 * min(t, 2000.0) - 0.5 * max(t - 2000.0, 0.0)

    report = fifo_report(mock_graph, cost, [0.0, 1000.0, 2000.0, 3000.0])
    assert report.ok
    assert report.min_slope == pytest.approx(-0.5)
    assert report.max_slope == pytest.approx(0.5)
    assert report.worst_t == 2000.0
