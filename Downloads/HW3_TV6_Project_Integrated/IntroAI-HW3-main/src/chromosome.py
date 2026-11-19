"""Mã hóa nhiễm sắc thể, giải mã và khởi tạo quần thể.  [Gói 2]

chrom: ndarray int, shape (n_sections, 6), cột theo config.GENE_*:
    [pattern, slot1, slot2, room1, room2, prof]
    pattern in 0..5 -> config.DAY_PATTERNS[pattern] = (day1, day2)
"""
from __future__ import annotations

import numpy as np

from src import config as C
from src.data_generator import Instance


def init_population(inst: Instance, pop_size: int, rng: np.random.Generator) -> np.ndarray:
    """Trả về ndarray (pop_size, n_sections, 6).

    ~90% random_chromosome (ràng buộc miền) + ~10% greedy_chromosome
    (tỉ lệ = config.GA_PARAMS['greedy_init_ratio']).
    """
    raise NotImplementedError("Gói 2")


def random_chromosome(inst: Instance, rng: np.random.Generator) -> np.ndarray:
    """Ngẫu nhiên có ràng buộc miền: chỉ chọn phòng đủ cỡ (room_size >= sec_reg),
    GV được phép dạy môn đó; chọn cặp ngày theo trọng số để cân bằng tải
    (T2/T6 xuất hiện 3 lần trong DAY_PATTERNS, T3/T4/T5 chỉ 2 lần)."""
    raise NotImplementedError("Gói 2")


def greedy_chromosome(inst: Instance, rng: np.random.Generator) -> np.ndarray:
    """Heuristic tham lam: xếp section cỡ lớn trước, ưu tiên ô (phòng, ngày, tiết) còn trống."""
    raise NotImplementedError("Gói 2")


def decode(chrom: np.ndarray) -> np.ndarray:
    """Chuyển chrom -> bảng buổi học, shape (2 * n_sections, 5):
    mỗi dòng [section, day, slot, room, prof]; dòng 2i là buổi 1, 2i+1 là buổi 2 của section i.
    Dùng chung cho fitness, validator, visualize, export.
    """
    pattern = chrom[:, C.GENE_PATTERN]
    days = np.asarray(C.DAY_PATTERNS)[pattern]            # (S, 2)
    n = len(chrom)
    out = np.empty((2 * n, 5), dtype=np.int64)
    out[0::2, 0] = out[1::2, 0] = np.arange(n)
    out[0::2, 1], out[1::2, 1] = days[:, 0], days[:, 1]
    out[0::2, 2], out[1::2, 2] = chrom[:, C.GENE_SLOT1], chrom[:, C.GENE_SLOT2]
    out[0::2, 3], out[1::2, 3] = chrom[:, C.GENE_ROOM1], chrom[:, C.GENE_ROOM2]
    out[0::2, 4] = out[1::2, 4] = chrom[:, C.GENE_PROF]
    return out
