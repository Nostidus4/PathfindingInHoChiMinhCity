"""Owner: P6. Test scenarios, runner, plots, summary_table trên FakePathfinder."""

import csv

import pytest

from src.cost.heuristics import HEURISTIC_MODES
from src.experiments import scenarios as sc
from src.experiments.plots import (
    plot_cost_vs_time,
    plot_expanded_nodes,
    plot_runtime,
    summary_table,
)
from src.experiments.runner import COLUMNS, run_experiments, write_csv
from src.experiments.time_demo import COLUMNS as DEMO_COLUMNS
from src.experiments.time_demo import time_dependence_demo
from src.mocks import MockTrafficProvider
from tests.fake_pathfinder import FakePathfinder


def test_random_scenarios_reproducible_and_unique(mock_graph):
    a = sc.random_scenarios(mock_graph, 30, sc.DEFAULT_TIMES, seed=7)
    b = sc.random_scenarios(mock_graph, 30, sc.DEFAULT_TIMES, seed=7)
    assert a == b
    assert len(a) == len(set(a)) == 30
    assert all(s != g for s, g, _ in a)
    assert {t for _, _, t in a} <= set(sc.DEFAULT_TIMES)


def test_random_scenarios_capped(mock_graph):
    # 7 node -> 42 cặp có hướng x 2 mốc giờ = 84 tổ hợp
    assert len(sc.random_scenarios(mock_graph, 1000, [0.0, 1.0])) == 84


def test_random_scenarios_rejects_bad_input(mock_graph):
    with pytest.raises(ValueError):
        sc.random_scenarios(mock_graph, 5, [])
    with pytest.raises(ValueError):
        sc.random_scenarios(mock_graph, -1, [0.0])


def test_curated_and_demo_pair(mock_graph, monkeypatch):
    # Không có cặp curated -> 2 POI xa nhau nhất có đường đi: G, F ở 2 góc,
    # G -> A -> ... -> F đi được, còn F -> G thì không (G chỉ có cạnh ra)
    assert sc.default_demo_pair(mock_graph) == ("G", "F")
    monkeypatch.setattr(sc, "CURATED_PAIRS", [("X", "Y"), ("A", "F")])
    assert sc.default_demo_pair(mock_graph) == ("A", "F")
    assert sc.curated_scenarios(mock_graph, [0.0, 60.0]) == [("A", "F", 0.0), ("A", "F", 60.0)]


@pytest.fixture
def experiments_csv(mock_graph, tmp_path):
    pf = FakePathfinder(mock_graph, MockTrafficProvider())
    scen = [("A", "F", 0.0), ("C", "F", 0.0), ("A", "G", 0.0)]
    return run_experiments(pf, scen, out_csv=tmp_path / "exp.csv")


def test_runner_csv(experiments_csv):
    with open(experiments_csv, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert tuple(rows[0]) == COLUMNS
    assert len(rows) == 3 * len(HEURISTIC_MODES)
    af_zero = next(
        r for r in rows if r["start"] == "A" and r["goal"] == "F" and r["mode"] == "zero"
    )
    assert af_zero["found"] == "True" and float(af_zero["cost_s"]) == 180.0
    assert af_zero["path_len"] == "5"
    no_path = [r for r in rows if r["goal"] == "G"]
    assert all(r["found"] == "False" and r["cost_s"] == "" for r in no_path)


def test_summary_table(experiments_csv):
    table = summary_table(experiments_csv)
    lines = table.splitlines()
    assert len(lines) == 2 + len(HEURISTIC_MODES)
    zero = next(line for line in lines if line.startswith("| zero |"))
    # 3 runs, 2 có đường, cả 2 đều tối ưu
    assert zero.startswith("| zero | 3 | 2 | 160.0 |")
    assert "| 100.0 | 0.00 |" in zero


def test_plots_written(experiments_csv, mock_graph, tmp_path):
    assert plot_expanded_nodes(experiments_csv, tmp_path).stat().st_size > 0
    assert plot_runtime(experiments_csv, tmp_path).stat().st_size > 0

    pf = FakePathfinder(mock_graph, MockTrafficProvider(rush_factor=0.5))
    rows = time_dependence_demo(pf, "A", "F", [0.0, 7.5 * 3600, 12 * 3600])
    demo_csv = write_csv(rows, DEMO_COLUMNS, tmp_path / "demo.csv")
    assert plot_cost_vs_time(demo_csv, tmp_path).name == "cost_vs_time.png"
