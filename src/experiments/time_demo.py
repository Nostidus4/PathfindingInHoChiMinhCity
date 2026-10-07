"""Demo phụ thuộc thời gian: cùng A/B, đổi giờ xuất phát. Owner: P6.

Cho thấy cost và/hoặc route thay đổi theo giờ (ví dụ 05:00 vs 07:30 vs 17:30).
Output: bảng CSV + bản đồ các route chồng lên nhau.

time_dependence_demo trả list dict (mỗi giờ một dòng), có key "result" là RouteResult
để vẽ bản đồ; CSV chỉ ghi các cột trong COLUMNS.
"""

from __future__ import annotations

from collections.abc import Sequence

from src.models import NodeId, RouteResult
from src.timeutil import format_seconds, parse_hhmm, time_grid

COLUMNS: tuple[str, ...] = (
    "departure",
    "departure_hhmm",
    "mode",
    "found",
    "cost_s",
    "arrival_hhmm",
    "distance_m",
    "expanded_nodes",
    "path",
    "route_changed",
)

DEFAULT_DEMO_TIMES: tuple[float, ...] = tuple(
    time_grid(parse_hhmm("05:00"), parse_hhmm("23:00"), step=1800)
)


def time_dependence_demo(
    pathfinder, start: NodeId, goal: NodeId, times: Sequence[float], mode: str = "dynamic_ub"
) -> list[dict]:
    """Chạy cùng A/B ở từng giờ xuất phát. route_changed = path khác giờ liền trước."""
    rows: list[dict] = []
    prev_path: list[NodeId] | None = None
    for t in times:
        r = pathfinder.route(start, goal, t, heuristic_mode=mode)
        rows.append(
            {
                "departure": t,
                "departure_hhmm": format_seconds(t)[:5],
                "mode": mode,
                "found": r.found,
                "cost_s": round(r.total_cost, 3) if r.found else "",
                "arrival_hhmm": format_seconds(r.arrival_time_s)[:5] if r.found else "",
                "distance_m": round(r.total_distance_m, 1) if r.found else "",
                "expanded_nodes": r.expanded_nodes,
                "path": " > ".join(r.path),
                "route_changed": prev_path is not None and r.path != prev_path,
                "result": r,
            }
        )
        prev_path = r.path
    return rows


def distinct_routes(rows: Sequence[dict]) -> list[tuple[str, RouteResult]]:
    """Gộp các giờ cho cùng một path -> [(label, RouteResult)] để vẽ chồng trên bản đồ.

    Label liệt kê các giờ xuất phát dùng route đó, ví dụ "05:00, 05:30, 21:00".
    """
    groups: dict[tuple[str, ...], list[dict]] = {}
    for row in rows:
        r = row["result"]
        if r.found:
            groups.setdefault(tuple(r.path), []).append(row)
    out = []
    for group in groups.values():
        hhmm = [g["departure_hhmm"] for g in group]
        label = ", ".join(hhmm) if len(hhmm) <= 4 else f"{hhmm[0]} … {hhmm[-1]} ({len(hhmm)} giờ)"
        out.append((label, group[0]["result"]))
    return out
