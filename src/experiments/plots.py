"""Biểu đồ và bảng cho báo cáo (matplotlib). Owner: P6.

- plot_expanded_nodes: so expanded nodes giữa 4 mode.
- plot_runtime: so runtime.
- plot_cost_vs_time: cost theo giờ xuất phát (từ time_demo).
- summary_table: bảng trung bình theo mode (xuất Markdown/LaTeX cho docs/report/).

Dùng matplotlib.figure.Figure (không qua pyplot) để chạy được trên máy không có màn hình.
Màu mỗi mode cố định theo thứ tự HEURISTIC_MODES, giống nhau ở mọi biểu đồ.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from matplotlib.figure import Figure

from src.config import REPO_ROOT
from src.cost.heuristics import HEURISTIC_MODES

OUT_DIR = REPO_ROOT / "outputs"

# dataviz reference palette (light), slot 1..4 theo thứ tự HEURISTIC_MODES.
MODE_COLORS: dict[str, str] = dict(
    zip(HEURISTIC_MODES, ("#2a78d6", "#eb6834", "#1baf7a", "#eda100"), strict=True)
)
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID_COLOR = "#e4e3df"
OPT_RTOL = 1e-6  # sai số tương đối khi so cost với Dijkstra (mode zero)


def _load_found(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["found"] = df["found"].astype(str).str.lower() == "true"
    return df


def _ordered_modes(df: pd.DataFrame) -> list[str]:
    present = list(dict.fromkeys(df["mode"]))
    return [m for m in HEURISTIC_MODES if m in present] + [
        m for m in present if m not in HEURISTIC_MODES
    ]


def _style_axes(ax) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID_COLOR)
    ax.tick_params(colors=TEXT_SECONDARY, length=0)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
    ax.set_axisbelow(True)


def _bar_by_mode(df: pd.DataFrame, column: str, title: str, ylabel: str, fmt: str, out: Path):
    found = df[df["found"]]
    modes = _ordered_modes(df)
    means = [found.loc[found["mode"] == m, column].mean() for m in modes]

    fig = Figure(figsize=(7, 4.2), dpi=150)
    ax = fig.subplots()
    bars = ax.bar(
        modes,
        means,
        width=0.6,
        color=[MODE_COLORS.get(m, TEXT_SECONDARY) for m in modes],
        edgecolor="white",
        linewidth=2,
    )
    ax.bar_label(bars, labels=[fmt.format(v) for v in means], padding=3, color=TEXT_PRIMARY)
    ax.set_title(title, loc="left", color=TEXT_PRIMARY, fontsize=12)
    ax.set_ylabel(ylabel, color=TEXT_SECONDARY)
    n_scenarios = len(df[["start", "goal", "departure"]].drop_duplicates())
    ax.set_xlabel(
        f"Heuristic mode · trung bình trên {n_scenarios} kịch bản (chỉ tính lần có đường)",
        color=TEXT_SECONDARY,
    )
    _style_axes(ax)
    ax.margins(y=0.12)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    return out


def plot_expanded_nodes(csv_path: Path, out_dir: Path = OUT_DIR) -> Path:
    """Cột: số node expanded trung bình theo mode (ít hơn = heuristic dẫn đường tốt hơn)."""
    return _bar_by_mode(
        _load_found(csv_path),
        "expanded_nodes",
        "Số node expanded trung bình theo heuristic",
        "Expanded nodes",
        "{:.1f}",
        Path(out_dir) / "expanded_nodes.png",
    )


def plot_runtime(csv_path: Path, out_dir: Path = OUT_DIR) -> Path:
    """Cột: runtime trung bình (ms) theo mode."""
    return _bar_by_mode(
        _load_found(csv_path),
        "runtime_ms",
        "Runtime trung bình theo heuristic",
        "Runtime (ms)",
        "{:.2f}",
        Path(out_dir) / "runtime.png",
    )


def plot_cost_vs_time(csv_path: Path, out_dir: Path = OUT_DIR) -> Path:
    """Đường: travel time (phút) theo giờ xuất phát, từ CSV của time_demo."""
    df = _load_found(csv_path)
    df = df[df["found"]].sort_values("departure")
    hours = df["departure"] / 3600
    minutes = df["cost_s"] / 60
    mode = df["mode"].iloc[0] if len(df) else ""

    fig = Figure(figsize=(8, 4.2), dpi=150)
    ax = fig.subplots()
    ax.plot(
        hours,
        minutes,
        color=MODE_COLORS.get(mode, "#2a78d6"),
        linewidth=2,
        marker="o",
        markersize=4,
    )
    changed = df["route_changed"].astype(str).str.lower() == "true"
    if changed.any():
        ax.scatter(
            hours[changed],
            minutes[changed],
            s=70,
            facecolors="none",
            edgecolors=TEXT_PRIMARY,
            linewidths=1.5,
            zorder=3,
            label="Route đổi so với giờ trước",
        )
        ax.legend(frameon=False, labelcolor=TEXT_SECONDARY, loc="upper left")
    ax.set_title(
        f"Thời gian di chuyển theo giờ xuất phát ({mode})",
        loc="left",
        color=TEXT_PRIMARY,
        fontsize=12,
    )
    ax.set_xlabel("Giờ xuất phát", color=TEXT_SECONDARY)
    ax.set_ylabel("Travel time (phút)", color=TEXT_SECONDARY)
    if len(df):
        lo, hi = int(hours.min()), int(hours.max()) + 1
        ax.set_xticks(range(lo, hi + 1, 2), [f"{h:02d}:00" for h in range(lo, hi + 1, 2)])
    _style_axes(ax)
    fig.tight_layout()
    out = Path(out_dir) / "cost_vs_time.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    return out


def summary_table(csv_path: Path) -> str:
    """Bảng Markdown trung bình theo mode, kèm tỉ lệ ra cost tối ưu so với mode zero (Dijkstra)."""
    df = _load_found(csv_path)
    key = ["start", "goal", "departure"]
    has_zero = "zero" in set(df["mode"])
    if has_zero:
        opt = df[(df["mode"] == "zero") & df["found"]][key + ["cost_s"]]
        df = df.merge(opt.rename(columns={"cost_s": "opt_cost"}), on=key, how="left")

    header = (
        "| Mode | Runs | Found | Cost TB (s) | Expanded TB | Runtime TB (ms) "
        "| Tối ưu (%) | Vượt tối ưu max (%) |"
    )
    lines = [header, "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for mode in _ordered_modes(df):
        sub = df[df["mode"] == mode]
        found = sub[sub["found"]]
        if has_zero and len(found):
            excess = (found["cost_s"] - found["opt_cost"]) / found["opt_cost"]
            optimal = f"{100 * (excess <= OPT_RTOL).mean():.1f}"
            worst = f"{100 * max(excess.max(), 0.0):.2f}"
        else:
            optimal = worst = "—"
        lines.append(
            f"| {mode} | {len(sub)} | {len(found)} | {found['cost_s'].mean():.1f} "
            f"| {found['expanded_nodes'].mean():.1f} | {found['runtime_ms'].mean():.3f} "
            f"| {optimal} | {worst} |"
        )
    return "\n".join(lines)
