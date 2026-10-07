"""Tiện ích thời gian. Quy ước: thời điểm = số giây kể từ 00:00 (float).

Ví dụ: parse_hhmm("07:30") == 27000.0 ; format_seconds(27000) == "07:30:00".
GRID_STEP = 900 giây (15 phút) là bước lưới dùng cho profile giao thông,
SpeedBounds và các test consistency/FIFO.
"""

from __future__ import annotations

SECONDS_PER_DAY = 24 * 3600
GRID_STEP = 900  # 15 phút


def parse_hhmm(text: str) -> float:
    """ "HH:MM" hoặc "HH:MM:SS" -> giây kể từ 00:00. Báo ValueError nếu sai định dạng."""
    parts = text.strip().split(":")
    if len(parts) not in (2, 3) or not all(p.isdigit() for p in parts):
        raise ValueError(f"Thời gian không hợp lệ: {text!r} (cần HH:MM)")
    h, m = int(parts[0]), int(parts[1])
    s = int(parts[2]) if len(parts) == 3 else 0
    if not (0 <= h < 24 and 0 <= m < 60 and 0 <= s < 60):
        raise ValueError(f"Thời gian ngoài khoảng: {text!r}")
    return float(h * 3600 + m * 60 + s)


def format_seconds(t: float) -> str:
    """Giây kể từ 00:00 -> "HH:MM:SS" (quá 24h vẫn in giờ > 23, ví dụ "24:10:00")."""
    total = int(round(t))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_duration(seconds: float) -> str:
    """Khoảng thời gian -> chuỗi dễ đọc, ví dụ "12 phút 30 giây"."""
    total = int(round(seconds))
    m, s = divmod(total, 60)
    return f"{m} phút {s} giây" if m else f"{s} giây"


def clamp(x: float, lo: float, hi: float) -> float:
    """Giới hạn x trong [lo, hi]."""
    return max(lo, min(hi, x))


def grid_index(t: float, step: int = GRID_STEP) -> int:
    """Chỉ số ô lưới chứa thời điểm t."""
    return int(t // step)


def time_grid(start: float, end: float, step: int = GRID_STEP) -> list[float]:
    """Danh sách mốc thời gian start, start+step, ..., <= end."""
    n = int((end - start) // step)
    return [start + i * step for i in range(n + 1)]
