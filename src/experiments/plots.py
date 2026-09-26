"""Biểu đồ và bảng cho báo cáo (matplotlib). Owner: P6.

- plot_expanded_nodes: so expanded nodes giữa 4 mode.
- plot_runtime: so runtime.
- plot_cost_vs_time: cost theo giờ xuất phát (từ time_demo).
- summary_table: bảng trung bình theo mode (xuất Markdown/LaTeX cho docs/report/).
"""

from __future__ import annotations

from pathlib import Path

from src.config import REPO_ROOT

OUT_DIR = REPO_ROOT / "outputs"


def plot_expanded_nodes(csv_path: Path, out_dir: Path = OUT_DIR) -> Path:
    raise NotImplementedError("TODO(P6)")


def plot_runtime(csv_path: Path, out_dir: Path = OUT_DIR) -> Path:
    raise NotImplementedError("TODO(P6)")


def plot_cost_vs_time(csv_path: Path, out_dir: Path = OUT_DIR) -> Path:
    raise NotImplementedError("TODO(P6)")


def summary_table(csv_path: Path) -> str:
    raise NotImplementedError("TODO(P6)")
