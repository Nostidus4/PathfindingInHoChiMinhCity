"""Vòng lặp GA và các toán tử.  [Gói 5]

Trước khi Gói 3/4 xong: dùng src._mocks.fake_evaluate (cùng chữ ký với evaluate).
"""
from __future__ import annotations

import numpy as np

from src.data_generator import Instance


def run_ga(inst: Instance, params: dict | None = None, evaluate_fn=None
           ) -> tuple[np.ndarray, list[dict]]:
    """Chạy GA, trả về (best_chrom, history).

    params mặc định = config.GA_PARAMS (+ 'seed'); evaluate_fn mặc định = fitness_soft.evaluate.
    history: list mỗi thế hệ được log, mỗi phần tử tối thiểu gồm
        {'gen', 'best', 'avg', 'best_penalty', 'avg_penalty', 'hard_best', 'soft_best', 'time'}
    ('best'/'avg' là fitness; visualize.plot_history dựa vào đúng các key này).
    """
    raise NotImplementedError("Gói 5")


def tournament_select(fitness: np.ndarray, k: int, n: int, rng: np.random.Generator) -> np.ndarray:
    """Trả về n chỉ số cá thể được chọn bằng tournament size k."""
    raise NotImplementedError("Gói 5")


def crossover(p1: np.ndarray, p2: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Uniform crossover theo section: mỗi section lấy nguyên dòng gene từ cha hoặc mẹ."""
    raise NotImplementedError("Gói 5")


def mutate(chrom: np.ndarray, inst: Instance, n_genes: int, rng: np.random.Generator,
           conflict_mask: np.ndarray | None = None) -> np.ndarray:
    """Đổi 1 trường (cặp ngày / tiết / phòng / GV) của n_genes section; nếu có conflict_mask
    thì ưu tiên các section đang vi phạm. Giá trị mới vẫn phải nằm trong miền hợp lệ."""
    raise NotImplementedError("Gói 5")
