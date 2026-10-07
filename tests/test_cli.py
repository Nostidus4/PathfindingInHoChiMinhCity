"""Owner: P6.

Input sai (POI không tồn tại, giờ sai, mode sai) -> exit code != 0 và thông báo rõ;
no-path -> thông báo không có đường; thiếu graph.json / phần chưa cài -> báo lỗi, không traceback.
CLI chạy với FakePathfinder để không phụ thuộc WP3/WP5.
"""

import pytest

from src import cli
from src.mocks import MockTrafficProvider
from tests.fake_pathfinder import FakePathfinder


@pytest.fixture
def fake_pf(monkeypatch):
    holder = {}

    def factory(graph, cfg):
        holder["pf"] = FakePathfinder(graph, MockTrafficProvider(rush_factor=0.5))
        return holder["pf"]

    monkeypatch.setattr(cli, "make_pathfinder", factory)
    return holder


def run(capsys, *argv):
    rc = cli.main(list(argv))
    out, err = capsys.readouterr()
    return rc, out, err


def test_route_ok(fake_pf, capsys):
    rc, out, err = run(capsys, "route", "--mock", "--start", "A", "--goal", "F", "--time", "05:00")
    assert rc == 0, err
    assert "A (Mock A) -> F (Mock F)" in out
    assert "Đến nơi  : 05:03:00" in out  # 1800 m ở 10 m/s
    assert "1.80 km" in out


def test_route_trace_and_map(fake_pf, capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "format_trace", lambda steps: f"<{len(steps)} steps>")
    out_html = tmp_path / "r.html"
    rc, out, err = run(
        capsys,
        "route",
        "--mock",
        "--start",
        "A",
        "--goal",
        "F",
        "--trace",
        "--map",
        "--out",
        str(out_html),
    )
    assert rc == 0, err
    assert "steps>" in out
    assert out_html.exists()


def test_route_unknown_poi(fake_pf, capsys):
    rc, _, err = run(capsys, "route", "--mock", "--start", "A", "--goal", "ZZZ")
    assert rc == 1
    assert "POI 'ZZZ' không tồn tại" in err
    assert "Traceback" not in err


@pytest.mark.parametrize("bad", ["8h", "25:00", "07:61", ""])
def test_route_bad_time(fake_pf, capsys, bad):
    rc, _, err = run(capsys, "route", "--mock", "--start", "A", "--goal", "F", "--time", bad)
    assert rc == 1
    assert "Thời gian" in err


def test_route_bad_mode(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["route", "--mock", "--start", "A", "--goal", "F", "--heuristic", "magic"])
    assert exc.value.code != 0
    assert "invalid choice" in capsys.readouterr().err


def test_route_no_path(fake_pf, capsys):
    rc, _, err = run(capsys, "route", "--mock", "--start", "A", "--goal", "G")
    assert rc == 1
    assert "Không có đường từ A (Mock A) tới G (Mock G)" in err


def test_missing_graph_suggests_mock(capsys, monkeypatch, tmp_path):
    import src.graph.io as gio

    monkeypatch.setattr(gio, "DEFAULT_GRAPH_PATH", tmp_path / "missing.json")
    rc, _, err = run(capsys, "list-pois")
    assert rc == 1
    assert "--mock" in err


def test_not_implemented_is_reported(capsys, monkeypatch):
    def boom(graph, cfg):
        raise NotImplementedError("TODO(P5)")

    monkeypatch.setattr(cli, "make_pathfinder", boom)
    rc, _, err = run(capsys, "route", "--mock", "--start", "A", "--goal", "F")
    assert rc == 1
    assert "chưa được cài đặt (TODO(P5))" in err
    assert "Traceback" not in err


def test_compare_lists_all_modes(fake_pf, capsys):
    rc, out, err = run(capsys, "compare", "--mock", "--start", "A", "--goal", "F")
    assert rc == 0, err
    for mode in ("zero", "static_vmax", "dynamic_ub", "dynamic_weighted"):
        assert mode in out


def test_compare_no_path(fake_pf, capsys):
    rc, _, err = run(capsys, "compare", "--mock", "--start", "A", "--goal", "G")
    assert rc == 1
    assert "Không có đường" in err


def test_list_pois_filter(capsys):
    rc, out, _ = run(capsys, "list-pois", "--mock", "--district", "quan 3")
    assert rc == 0
    assert "Tổng: 3 POI" in out
    assert "Mock D" in out and "Mock A" not in out


def test_list_pois_unknown_district(capsys):
    rc, _, err = run(capsys, "list-pois", "--mock", "--district", "Quan 99")
    assert rc == 1
    assert "Các quận có: Quan 1, Quan 3" in err


def test_validate_exit_code_follows_result(capsys, monkeypatch):
    monkeypatch.setattr(cli, "run_validation", lambda graph, cfg: 1)
    assert cli.main(["validate", "--mock"]) == 1
    monkeypatch.setattr(cli, "run_validation", lambda graph, cfg: 0)
    assert cli.main(["validate", "--mock"]) == 0


def test_experiments_writes_outputs(fake_pf, capsys, tmp_path):
    rc, out, err = run(capsys, "experiments", "--mock", "--n", "12", "--out-dir", str(tmp_path))
    assert rc == 0, err
    for name in (
        "experiments.csv",
        "expanded_nodes.png",
        "runtime.png",
        "summary.md",
        "time_demo.csv",
        "cost_vs_time.png",
        "time_demo_map.html",
    ):
        assert (tmp_path / name).exists(), name
    assert "| dynamic_ub |" in out
