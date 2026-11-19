"""Ràng buộc cứng H1, H3a, H3b, H4, H6 – vector hóa bằng numpy.  [Gói 3]

H2 (cặp ngày) và H5 (1 section 2 phòng cùng lúc) tự thỏa nhờ mã hóa, không cần phạt.
Mục tiêu tốc độ: < 5 ms / cá thể (dùng np.bincount / np.add.at, tránh vòng lặp Python).
"""
from __future__ import annotations

import numpy as np

from src.data_generator import Instance

HARD_KEYS = ("H1", "H3a", "H3b", "H4", "H6")


def hard_penalties(chrom: np.ndarray, inst: Instance) -> dict:
    """Trả về {'H1': int, 'H3a': int, 'H3b': int, 'H4': int, 'H6': int}.

    H1  : số buổi có room_size[room] < sec_reg[section]
    H3a : Σ theo (GV, ngày, tiết) của max(0, số buổi − 1)
    H3b : Σ theo GV của max(0, số section − MAX_SECTIONS_PER_PROF)
    H4  : số buổi rơi vào ô room_avail == False
    H6  : Σ theo (phòng, ngày, tiết) của max(0, số buổi − 1)
    """
    raise NotImplementedError("Gói 3")


def section_conflicts(chrom: np.ndarray, inst: Instance) -> np.ndarray:
    """(Tùy chọn, dùng cho đột biến hướng xung đột – Gói 5)
    Trả về mảng bool/int (n_sections,) đánh dấu section đang vi phạm ràng buộc cứng."""
    raise NotImplementedError("Gói 3")
