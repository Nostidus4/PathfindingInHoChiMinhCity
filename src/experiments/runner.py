"""Chạy 4 heuristic mode trên mọi scenario, xuất CSV. Owner: P6.

Cột: start, goal, departure, mode, found, cost_s, expanded_nodes, runtime_ms, path_len.
Output: outputs/experiments.csv.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from src.config import REPO_ROOT
from src.cost.heuristics import HEURISTIC_MODES


def run_experiments(
    pathfinder,
    scenarios: Sequence[tuple],
    modes: Sequence[str] = HEURISTIC_MODES,
    out_csv: Path = REPO_ROOT / "outputs" / "experiments.csv",
) -> Path:
    raise NotImplementedError("TODO(P6)")
