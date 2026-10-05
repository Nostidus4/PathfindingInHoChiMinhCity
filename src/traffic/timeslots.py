"""Xử lý thời gian của Traffic Data Layer (WP3.4). Owner: P3.

Quy ước (giống timeutil.py):
    - Thời điểm = số giây kể từ 00:00 (float).
    - Traffic được xác định tại các mốc lưới start, start + step, ... (mặc định 15 phút).
    - Giữa hai mốc: nội suy tuyến tính.
    - Ngoài cửa sổ [start, mốc cuối]: clamp về giá trị biên (KHÔNG quay vòng theo ngày,
      để hàm traffic theo t liên tục và không phá FIFO quanh nửa đêm).

Mọi bảng theo thời gian của WP3 (profile rho, SpeedBounds) dùng chung TimeGrid này,
nên nội suy của các bảng khớp nhau trên cùng lưới.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from src.config import SimConfig
from src.timeutil import time_grid


def interpolate_on_grid(values: Sequence[float], start_s: float, step_s: float, t: float) -> float:
    """Nội suy tuyến tính values (giá trị tại start + i*step) tại t, clamp ngoài lưới.

    Hàm thuần, không tạo object, dùng ở các đường nóng (SpeedBounds.v_ub gọi mỗi lần
    heuristic được tính).
    """
    n = len(values)
    if n == 0:
        raise ValueError("Bảng giá trị theo thời gian rỗng")
    x = (t - start_s) / step_s
    if not x > 0.0:  # gồm cả trường hợp t trước cửa sổ
        if math.isnan(x):
            raise ValueError(f"Thời điểm không hợp lệ: {t!r}")
        return float(values[0])
    if x >= n - 1:
        return float(values[-1])
    i = int(x)
    frac = x - i
    return float(values[i]) + frac * (float(values[i + 1]) - float(values[i]))


@dataclass(frozen=True, slots=True)
class TimeGrid:
    """Lưới thời gian start, start + step, ..., mốc cuối <= end."""

    start_s: float
    end_s: float
    step_s: int

    def __post_init__(self) -> None:
        if self.step_s <= 0:
            raise ValueError(f"step_s phải > 0, nhận {self.step_s}")
        if self.end_s < self.start_s:
            raise ValueError("end_s phải >= start_s")

    @classmethod
    def from_config(cls, cfg: SimConfig) -> TimeGrid:
        return cls(cfg.window_start_s, cfg.window_end_s, cfg.grid_step_s)

    @property
    def n_points(self) -> int:
        """Số mốc trên lưới (gồm cả hai đầu)."""
        return int((self.end_s - self.start_s) // self.step_s) + 1

    @property
    def last_s(self) -> float:
        """Mốc cuối của lưới (= end_s nếu cửa sổ chia hết cho step)."""
        return self.start_s + (self.n_points - 1) * self.step_s

    def points(self) -> list[float]:
        """Danh sách các mốc thời gian (giây)."""
        return time_grid(self.start_s, self.end_s, self.step_s)

    def normalize_time(self, t: float) -> float:
        """Clamp t về [start, mốc cuối]. Báo ValueError nếu t là NaN."""
        if math.isnan(t):
            raise ValueError(f"Thời điểm không hợp lệ: {t!r}")
        return max(self.start_s, min(self.last_s, float(t)))

    def get_time_slot(self, t: float) -> tuple[int, float]:
        """(i, frac): t nằm giữa mốc i và i+1, frac trong [0, 1) là vị trí tương đối.

        Tại mốc cuối (hoặc sau cửa sổ) trả (n_points - 1, 0.0).
        """
        x = (self.normalize_time(t) - self.start_s) / self.step_s
        i = min(int(x), self.n_points - 1)
        return i, (x - i if i < self.n_points - 1 else 0.0)

    def interpolate(self, values: Sequence[float], t: float) -> float:
        """Giá trị tại t của một bảng có đúng n_points phần tử (một giá trị mỗi mốc)."""
        if len(values) != self.n_points:
            raise ValueError(f"Bảng cần {self.n_points} giá trị, nhận {len(values)}")
        return interpolate_on_grid(values, self.start_s, self.step_s, t)
