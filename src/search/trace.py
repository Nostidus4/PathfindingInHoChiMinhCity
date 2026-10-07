"""Ghi lại từng bước A* để giải thích thuật toán. Owner: P5.

- TraceRecorder: A* gọi record(...) mỗi lần push/expand/update.
- format_trace(steps): in bảng step | node | g | h | f | t | open_size,
  dùng để sinh docs/algorithm_walkthrough.md và cho `hcmc route --trace`.
"""

from __future__ import annotations

from src.models import TraceStep


class TraceRecorder:
    def __init__(self, max_steps: int | None = None) -> None:
        self.steps: list[TraceStep] = []
        self.max_steps = max_steps

    def record(self, step: TraceStep) -> None:
        if self.max_steps is None or len(self.steps) < self.max_steps:
            self.steps.append(step)


def format_trace(steps: list[TraceStep]) -> str:
    """Chuỗi bảng dễ đọc của các bước trace."""
    raise NotImplementedError("TODO(P5)")
