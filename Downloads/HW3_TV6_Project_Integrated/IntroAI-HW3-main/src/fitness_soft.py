"""Ràng buộc mềm S1–S4, bonus B1/B2, và hàm evaluate() tổng hợp.  [Gói 4]

Penalty(x) = W_H * (H1 + H3a + H3b + H4 + H6 [+ B2]) + Σ w_k * S_k + w_B1 * B1
Fitness(x) = 1 / (1 + Penalty(x))      # càng lớn càng tốt, tối đa = 1
"""
from __future__ import annotations

import numpy as np

from src import config as C
from src.data_generator import Instance

SOFT_KEYS = ("S1", "S2", "S3", "S4", "B1", "B2")


def soft_penalties(chrom: np.ndarray, inst: Instance) -> dict:
    """Trả về {'S1', 'S2', 'S3', 'S4', 'B1', 'B2'} (số, có thể float với S1).

    S1 : Σ (GV, ngày) của (tiết cuối − tiết đầu + 1 − số buổi)
         + S1_LAMBDA × Σ GV của (số ngày dạy − ceil(số buổi / 3))
    S2 : số cặp (GV, ngày) có cả buổi sáng (tiết 1–3) và buổi chiều (tiết 4–6)
    S3 : số section có half(slot1) != half(slot2)
    S4 : Σ (room_size − sec_reg) trên các buổi có room_size >= sec_reg
    B1 : số GV không dạy section nào thuộc 3 môn yêu thích
    B2 : số section có môn không nằm trong prof_can_teach của GV
    (+ ràng buộc tự thêm – Bonus 3 – nếu có, thêm key mới và báo cả nhóm)
    """
    raise NotImplementedError("Gói 4")


def evaluate(chrom: np.ndarray, inst: Instance, weights: dict | None = None
             ) -> tuple[float, float, dict]:
    """Trả về (fitness, penalty, details).

    details = {**hard_penalties, **soft_penalties, 'hard_total': int, 'soft_total': float}
    weights mặc định = config.WEIGHTS; B2 tính vào phần cứng nếu config.B2_IS_HARD.
    """
    raise NotImplementedError("Gói 4")
