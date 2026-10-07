"""Ghi lại từng bước A* để giải thích thuật toán. Owner: P5.

- TraceRecorder: A* gọi record(...) mỗi lần push/expand/update.
- format_trace(steps): in bảng step | node | g | h | f | t | open_size,
  dùng để sinh docs/algorithm_walkthrough.md và cho `hcmc route --trace`.

Ý nghĩa `action` (xem docs/algorithm_walkthrough.md §3):
    expand  lấy node ra khỏi open set và duyệt các cạnh đi ra
    push    lần đầu tìm được đường tới node này
    update  tìm được g nhỏ hơn cho node đã có nhãn (note="reopen" nếu node đã expand)
    skip    pop một nhãn cũ đã bị thay thế -> bỏ qua, không expand

`open_size` là số entry trong heap, gồm cả entry cũ chưa bị loại, nên nó là
chặn trên của số nhãn còn hiệu lực.
"""

from __future__ import annotations

from src.models import TraceStep
from src.timeutil import format_seconds

_HEADER = ("#", "action", "node", "g (s)", "h (s)", "f (s)", "t", "open", "note")


class TraceRecorder:
    def __init__(self, max_steps: int | None = None) -> None:
        self.steps: list[TraceStep] = []
        self.max_steps = max_steps

    def record(self, step: TraceStep) -> None:
        if self.max_steps is None or len(self.steps) < self.max_steps:
            self.steps.append(step)


def format_trace(steps: list[TraceStep]) -> str:
    """Chuỗi bảng dễ đọc của các bước trace."""
    if not steps:
        return "(không có bước nào: chạy lại với --trace để bật ghi trace)"

    rows = [
        (
            str(s.step),
            s.action,
            str(s.node),
            f"{s.g:.1f}",
            f"{s.h:.1f}",
            f"{s.f:.1f}",
            format_seconds(s.t),
            str(s.open_size),
            s.note,
        )
        for s in steps
    ]
    widths = [max(len(_HEADER[i]), *(len(r[i]) for r in rows)) for i in range(len(_HEADER))]

    def line(cells: tuple[str, ...]) -> str:
        parts = [
            cells[i].ljust(widths[i]) if i in (1, 2, 8) else cells[i].rjust(widths[i])
            for i in range(len(cells))
        ]
        return "  ".join(parts).rstrip()

    out = [line(_HEADER), "  ".join("-" * w for w in widths)]
    out += [line(r) for r in rows]
    expanded = sum(1 for s in steps if s.action == "expand")
    out.append(f"\nTổng: {len(steps)} bước, {expanded} lần expand.")
    return "\n".join(out)
