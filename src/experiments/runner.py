"""Chạy 4 heuristic mode trên mọi scenario, xuất CSV. Owner: P6.

Cột: start, goal, departure, mode, found, cost_s, expanded_nodes, runtime_ms, path_len.
Output: outputs/experiments.csv.
departure là giây kể từ 00:00; cost_s để trống khi không có đường.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from src.config import REPO_ROOT
from src.cost.heuristics import HEURISTIC_MODES

COLUMNS: tuple[str, ...] = (
    "start",
    "goal",
    "departure",
    "mode",
    "found",
    "cost_s",
    "expanded_nodes",
    "runtime_ms",
    "path_len",
)


def write_csv(rows: Iterable[Mapping], columns: Sequence[str], out_csv: Path) -> Path:
    """Ghi rows ra CSV, chỉ lấy các cột trong columns (bỏ qua key khác)."""
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return out_csv


def run_experiments(
    pathfinder,
    scenarios: Sequence[tuple],
    modes: Sequence[str] = HEURISTIC_MODES,
    out_csv: Path = REPO_ROOT / "outputs" / "experiments.csv",
) -> Path:
    """Chạy pathfinder.route cho mọi (scenario, mode), ghi một dòng mỗi lần chạy."""
    rows = []
    for start, goal, departure in scenarios:
        for mode in modes:
            r = pathfinder.route(start, goal, departure, heuristic_mode=mode)
            rows.append(
                {
                    "start": start,
                    "goal": goal,
                    "departure": departure,
                    "mode": mode,
                    "found": r.found,
                    "cost_s": round(r.total_cost, 3) if r.found else "",
                    "expanded_nodes": r.expanded_nodes,
                    "runtime_ms": round(r.runtime_ms, 3),
                    "path_len": len(r.path),
                }
            )
    return write_csv(rows, COLUMNS, out_csv)
