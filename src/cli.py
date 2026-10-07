"""Giao diện dòng lệnh `hcmc` (T0). Owner: P6.

Lệnh:
    hcmc route --start A --goal B --time 08:00 --heuristic dynamic_ub [--trace] [--map]
    hcmc compare --start A --goal B --time 08:00      # chạy cả 4 mode
    hcmc validate                                      # admissibility/consistency/FIFO
    hcmc experiments                                   # chạy runner + plots
    hcmc list-pois [--district "Quan 1"]
Mọi lệnh nhận --mock: dùng MockGraph (src/mocks.py) thay cho data/processed/graph.json.
Phải xử lý: input sai (POI không tồn tại, giờ sai định dạng, mode sai) và no-path
bằng thông báo rõ ràng + exit code != 0, không in traceback.
Chỉ gọi Pathfinder, không gọi astar trực tiếp.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from src.config import REPO_ROOT, SimConfig
from src.cost.edge_cost import make_edge_cost
from src.cost.heuristics import HEURISTIC_MODES, make_heuristic
from src.experiments.plots import (
    plot_cost_vs_time,
    plot_expanded_nodes,
    plot_runtime,
    summary_table,
)
from src.experiments.runner import run_experiments, write_csv
from src.experiments.scenarios import (
    DEFAULT_N_SCENARIOS,
    DEFAULT_TIMES,
    curated_scenarios,
    default_demo_pair,
    random_scenarios,
)
from src.experiments.time_demo import (
    COLUMNS as TIME_DEMO_COLUMNS,
)
from src.experiments.time_demo import (
    DEFAULT_DEMO_TIMES,
    distinct_routes,
    time_dependence_demo,
)
from src.graph.io import load_default_graph
from src.mocks import MockGraph
from src.models import NodeId, RouteResult
from src.search.pathfinder import Pathfinder
from src.search.trace import format_trace
from src.timeutil import format_duration, format_seconds, parse_hhmm, time_grid
from src.traffic.speed_bounds import compute_speed_bounds
from src.traffic.synthetic import SyntheticProvider
from src.validation.admissibility import check_admissibility
from src.validation.consistency import check_consistency
from src.validation.counterexamples import find_counterexamples
from src.validation.fifo import check_fifo
from src.viz.map_static import ROUTE_COLORS, render_map, render_routes_map

OUT_DIR = REPO_ROOT / "outputs"
VALIDATION_GOALS = 10  # số goal lấy mẫu khi kiểm admissibility/consistency
ADMISSIBLE_MODES = ("zero", "static_vmax", "dynamic_ub")
INADMISSIBLE_MODE = "dynamic_weighted"


class CliError(Exception):
    """Lỗi người dùng: in thông báo, exit code 1, không traceback."""


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--mock", action="store_true", help="Dùng graph mock 7 node thay cho graph.json"
    )

    p = argparse.ArgumentParser(prog="hcmc", description="Pathfinding in Ho Chi Minh City")
    sub = p.add_subparsers(dest="command", required=True)

    r = sub.add_parser("route", parents=[common], help="Tìm đường từ start tới goal")
    r.add_argument("--start", required=True)
    r.add_argument("--goal", required=True)
    r.add_argument("--time", default="08:00", help="Giờ xuất phát HH:MM")
    r.add_argument("--heuristic", default="dynamic_ub", choices=HEURISTIC_MODES)
    r.add_argument("--trace", action="store_true", help="In từng bước A*")
    r.add_argument("--map", action="store_true", help="Xuất bản đồ HTML")
    r.add_argument("--out", type=Path, default=OUT_DIR / "route.html", help="File HTML bản đồ")

    c = sub.add_parser("compare", parents=[common], help="So sánh 4 heuristic mode")
    c.add_argument("--start", required=True)
    c.add_argument("--goal", required=True)
    c.add_argument("--time", default="08:00")

    sub.add_parser("validate", parents=[common], help="Kiểm admissibility / consistency / FIFO")

    e = sub.add_parser("experiments", parents=[common], help="Chạy thí nghiệm và vẽ biểu đồ")
    e.add_argument("--n", type=int, default=DEFAULT_N_SCENARIOS, help="Số kịch bản ngẫu nhiên")
    e.add_argument("--out-dir", type=Path, default=OUT_DIR)

    lp = sub.add_parser("list-pois", parents=[common], help="Liệt kê POI")
    lp.add_argument("--district", default=None)
    return p


# ---------------------------------------------------------------- dựng dữ liệu


def load_graph(mock: bool):
    if mock:
        return MockGraph()
    try:
        return load_default_graph()
    except FileNotFoundError as exc:
        raise CliError(f"{exc}\nHoặc thêm --mock để chạy thử trên graph mock.") from exc


def make_pathfinder(graph, cfg: SimConfig) -> Pathfinder:
    """Điểm duy nhất tạo Pathfinder (test thay hàm này bằng FakePathfinder)."""
    return Pathfinder(graph, SyntheticProvider(graph, cfg, seed=cfg.seed), cfg)


def _check_node(graph, node: NodeId) -> NodeId:
    if node not in {p.id for p in graph.nodes()}:
        raise CliError(f"POI '{node}' không tồn tại. Xem danh sách bằng: hcmc list-pois")
    return node


def _parse_time(text: str) -> float:
    try:
        return parse_hhmm(text)
    except ValueError as exc:
        raise CliError(f"{exc}. Ví dụ: --time 07:30") from exc


def _poi_label(graph, node: NodeId) -> str:
    return f"{node} ({graph.get_node(node).name})"


# ---------------------------------------------------------------- in kết quả


def format_route(graph, r: RouteResult) -> str:
    lines = [
        f"Route   : {_poi_label(graph, r.path[0])} -> {_poi_label(graph, r.path[-1])}"
        f"  [{r.heuristic_mode}]",
        f"Xuất phát: {format_seconds(r.departure_time_s)}",
        f"Đến nơi  : {format_seconds(r.arrival_time_s)}",
        f"Thời gian: {format_duration(r.travel_time_s)}",
        f"Quãng đường: {r.total_distance_m / 1000:.2f} km",
        f"Expanded : {r.expanded_nodes} node · runtime {r.runtime_ms:.2f} ms",
        f"Đường đi ({len(r.path)} POI):",
    ]
    lines += [f"  {i:>2}. {n:<12} {graph.get_node(n).name}" for i, n in enumerate(r.path, 1)]
    return "\n".join(lines)


def _no_path(graph, start: NodeId, goal: NodeId, t: float) -> CliError:
    return CliError(
        f"Không có đường từ {_poi_label(graph, start)} tới {_poi_label(graph, goal)} "
        f"khi xuất phát lúc {format_seconds(t)}."
    )


# ---------------------------------------------------------------- các lệnh


def cmd_route(args, cfg: SimConfig) -> int:
    graph = load_graph(args.mock)
    start, goal = _check_node(graph, args.start), _check_node(graph, args.goal)
    t = _parse_time(args.time)
    pf = make_pathfinder(graph, cfg)
    # --map cần trace để lấy ETA từng node
    r = pf.route(start, goal, t, heuristic_mode=args.heuristic, trace=args.trace or args.map)
    if not r.found:
        raise _no_path(graph, start, goal, t)
    print(format_route(graph, r))
    if args.trace:
        print("\nTrace A*:")
        print(format_trace(r.trace))
    if args.map:
        out = render_map(graph, graph.nodes(), r, args.out)
        print(f"\nBản đồ: {out}")
    return 0


def cmd_compare(args, cfg: SimConfig) -> int:
    graph = load_graph(args.mock)
    start, goal = _check_node(graph, args.start), _check_node(graph, args.goal)
    t = _parse_time(args.time)
    pf = make_pathfinder(graph, cfg)
    results = {m: pf.route(start, goal, t, heuristic_mode=m) for m in HEURISTIC_MODES}
    if not any(r.found for r in results.values()):
        raise _no_path(graph, start, goal, t)

    opt = results["zero"].total_cost if results["zero"].found else None
    print(
        f"So sánh heuristic: {_poi_label(graph, start)} -> {_poi_label(graph, goal)}"
        f" lúc {format_seconds(t)}\n"
    )
    print(
        f"{'Mode':<18}{'Cost (s)':>10}{'ETA':>10}{'Expanded':>10}{'Runtime ms':>12}"
        f"{'POI':>5}  Ghi chú"
    )
    for mode, r in results.items():
        if not r.found:
            print(
                f"{mode:<18}{'—':>10}{'—':>10}{r.expanded_nodes:>10}{r.runtime_ms:>12.2f}"
                f"{'—':>5}  không có đường"
            )
            continue
        note = ""
        if opt is not None and r.total_cost > opt * (1 + 1e-6):
            note = f"vượt tối ưu {100 * (r.total_cost - opt) / opt:.2f}%"
        print(
            f"{mode:<18}{r.total_cost:>10.1f}{format_seconds(r.arrival_time_s):>10}"
            f"{r.expanded_nodes:>10}{r.runtime_ms:>12.2f}{len(r.path):>5}  {note}"
        )
    return 0


def run_validation(graph, cfg: SimConfig) -> int:
    """Kiểm FIFO, admissibility/consistency của các mode, phản ví dụ của dynamic_weighted.

    Trả 0 nếu mọi kỳ vọng ở scope mục 14 đều đúng, ngược lại 1.
    """
    provider = SyntheticProvider(graph, cfg, seed=cfg.seed)
    bounds = compute_speed_bounds(graph, provider, cfg)
    cost = make_edge_cost(provider)
    grid = time_grid(cfg.window_start_s, cfg.window_end_s, cfg.grid_step_s)
    hourly = time_grid(cfg.window_start_s, cfg.window_end_s, 3600)
    ids = sorted(p.id for p in graph.nodes())
    goals = random.Random(cfg.seed).sample(ids, min(VALIDATION_GOALS, len(ids)))
    ok = True

    def report(name: str, violations: list, expect_violation: bool = False) -> None:
        nonlocal ok
        passed = bool(violations) if expect_violation else not violations
        ok &= passed
        status = "ĐẠT" if passed else "LỖI"
        detail = f"{len(violations)} vi phạm"
        if violations:
            detail += f", ví dụ: {violations[0]}"
        print(f"[{status}] {name}: {detail}")

    report("FIFO trên mọi edge", check_fifo(graph, cost, grid))
    params = {"w": cfg.weight_w}
    for mode in ADMISSIBLE_MODES:
        h = make_heuristic(mode, graph, bounds, params)
        report(f"{mode} admissible", check_admissibility(graph, h, cost, goals, hourly))
        report(f"{mode} consistent", check_consistency(graph, h, cost, goals, grid))

    scenarios = random_scenarios(graph, DEFAULT_N_SCENARIOS, DEFAULT_TIMES, cfg.seed)
    counter = find_counterexamples(make_pathfinder(graph, cfg), scenarios, INADMISSIBLE_MODE)
    report(
        f"{INADMISSIBLE_MODE} có phản ví dụ (cost A* > Dijkstra)", counter, expect_violation=True
    )
    return 0 if ok else 1


def cmd_validate(args, cfg: SimConfig) -> int:
    return run_validation(load_graph(args.mock), cfg)


def cmd_experiments(args, cfg: SimConfig) -> int:
    if args.n < 1:
        raise CliError("--n phải >= 1")
    graph = load_graph(args.mock)
    pf = make_pathfinder(graph, cfg)
    out_dir = Path(args.out_dir)

    scenarios = list(
        dict.fromkeys(
            curated_scenarios(graph, DEFAULT_TIMES)
            + random_scenarios(graph, args.n, DEFAULT_TIMES, cfg.seed)
        )
    )
    print(f"Chạy {len(scenarios)} kịch bản x {len(HEURISTIC_MODES)} mode ...")
    csv_path = run_experiments(pf, scenarios, out_csv=out_dir / "experiments.csv")
    outputs = [csv_path, plot_expanded_nodes(csv_path, out_dir), plot_runtime(csv_path, out_dir)]
    table = summary_table(csv_path)
    summary_path = out_dir / "summary.md"
    summary_path.write_text(table + "\n", encoding="utf-8")
    outputs.append(summary_path)

    start, goal = default_demo_pair(graph)
    print(f"Time demo: {_poi_label(graph, start)} -> {_poi_label(graph, goal)} ...")
    rows = time_dependence_demo(pf, start, goal, DEFAULT_DEMO_TIMES)
    demo_csv = write_csv(rows, TIME_DEMO_COLUMNS, out_dir / "time_demo.csv")
    outputs += [demo_csv, plot_cost_vs_time(demo_csv, out_dir)]
    routes = distinct_routes(rows)
    if len(routes) > len(ROUTE_COLORS):
        print(f"Có {len(routes)} route khác nhau, bản đồ chỉ vẽ {len(ROUTE_COLORS)} route đầu.")
        routes = routes[: len(ROUTE_COLORS)]
    outputs.append(render_routes_map(graph, graph.nodes(), routes, out_dir / "time_demo_map.html"))

    print("\n" + table + "\n")
    print("Đã ghi:")
    for path in outputs:
        print(f"  {path}")
    return 0


def cmd_list_pois(args, cfg: SimConfig) -> int:
    graph = load_graph(args.mock)
    pois = sorted(graph.nodes(), key=lambda p: (p.district, p.id))
    if args.district:
        wanted = args.district.strip().lower()
        selected = [p for p in pois if p.district.lower() == wanted]
        if not selected:
            districts = ", ".join(sorted({p.district for p in pois}))
            raise CliError(f"Không có POI ở quận '{args.district}'. Các quận có: {districts}")
        pois = selected
    print(f"{'ID':<14}{'Quận':<14}{'Loại':<14}Tên")
    for p in pois:
        print(f"{p.id:<14}{p.district:<14}{p.kind:<14}{p.name}")
    print(f"\nTổng: {len(pois)} POI")
    return 0


COMMANDS = {
    "route": cmd_route,
    "compare": cmd_compare,
    "validate": cmd_validate,
    "experiments": cmd_experiments,
    "list-pois": cmd_list_pois,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return COMMANDS[args.command](args, SimConfig.load())
    except CliError as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
    except NotImplementedError as exc:
        owner = f" ({exc})" if str(exc) else ""
        print(
            f"Lỗi: lệnh '{args.command}' cần một phần chưa được cài đặt{owner}. "
            "Chờ work package đó merge rồi chạy lại.",
            file=sys.stderr,
        )
    except ValueError as exc:  # Pathfinder/heuristic báo input sai
        print(f"Lỗi: {exc}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
