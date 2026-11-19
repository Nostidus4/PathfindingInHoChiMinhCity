"""Dữ liệu/fitness giả đúng giao diện – để Gói 5, 6 làm trước khi Gói 1–4 xong.

Xóa các chỗ import _mocks khỏi code chính sau khi ghép (mốc 1 – 15/11).
"""
from __future__ import annotations

import numpy as np

from src import config as C
from src.data_generator import Instance


def fake_instance(n_rooms: int = C.N_ROOMS_DEFAULT, n_courses: int = C.N_COURSES,
                  seed: int = 0) -> Instance:
    """Instance ngẫu nhiên tối giản (không kiểm tra khả thi)."""
    rng = np.random.default_rng(seed)
    n_sec = n_courses * C.SECTIONS_PER_COURSE
    return Instance(
        n_rooms=n_rooms,
        room_size=rng.integers(0, 3, n_rooms),
        room_avail=np.ones((n_rooms, C.N_DAYS, C.N_SLOTS), dtype=bool),
        sec_course=np.repeat(np.arange(n_courses), C.SECTIONS_PER_COURSE),
        sec_reg=rng.integers(0, 3, n_sec),
        prof_fav=np.stack([rng.choice(n_courses, 3, replace=False) for _ in range(C.N_PROFS)]),
        prof_can_teach=[np.arange(n_courses) for _ in range(C.N_PROFS)],
        seed=seed,
    )


def fake_chromosome(inst: Instance, rng: np.random.Generator) -> np.ndarray:
    """Chromosome ngẫu nhiên hoàn toàn (không ràng buộc miền)."""
    s = inst.n_sections
    return np.column_stack([
        rng.integers(0, len(C.DAY_PATTERNS), s),
        rng.integers(0, C.N_SLOTS, s),
        rng.integers(0, C.N_SLOTS, s),
        rng.integers(0, inst.n_rooms, s),
        rng.integers(0, inst.n_rooms, s),
        rng.integers(0, inst.n_profs, s),
    ]).astype(np.int64)


def fake_evaluate(chrom: np.ndarray, inst: Instance, weights: dict | None = None
                  ) -> tuple[float, float, dict]:
    """Cùng chữ ký với fitness_soft.evaluate. Chỉ đếm H6 (trùng phòng) + S3 cho có tín hiệu."""
    from src.chromosome import decode
    ses = decode(chrom)
    key = (ses[:, 3] * C.N_DAYS + ses[:, 1]) * C.N_SLOTS + ses[:, 2]
    cnt = np.bincount(key, minlength=inst.n_rooms * C.N_DAYS * C.N_SLOTS)
    h6 = int(np.maximum(cnt - 1, 0).sum())
    s3 = int(((chrom[:, C.GENE_SLOT1] < 3) != (chrom[:, C.GENE_SLOT2] < 3)).sum())
    penalty = 1000 * h6 + 2 * s3
    details = {"H6": h6, "S3": s3, "hard_total": h6, "soft_total": s3}
    return 1.0 / (1.0 + penalty), float(penalty), details


def fake_history(n_gen: int = 500, seed: int = 0) -> list[dict]:
    """History giả có hình dạng hợp lý (penalty giảm dần) để vẽ đồ thị."""
    rng = np.random.default_rng(seed)
    hist, best, hard = [], 400_000.0, 400
    for g in range(n_gen):
        hard = max(0, hard - rng.integers(0, 3))
        best = hard * 1000 + 300 * np.exp(-g / 150) + 50
        avg = best * (1.3 + 0.2 * rng.random())
        hist.append({"gen": g, "best": 1 / (1 + best), "avg": 1 / (1 + avg),
                     "best_penalty": best, "avg_penalty": avg,
                     "hard_best": hard, "soft_best": best - hard * 1000, "time": g * 0.05})
    return hist
