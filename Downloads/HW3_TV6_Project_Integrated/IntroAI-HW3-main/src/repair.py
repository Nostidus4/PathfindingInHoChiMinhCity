"""Local search / repair cho memetic GA.  [Gói 5]"""
from __future__ import annotations

import numpy as np

from src.data_generator import Instance


def repair(chrom: np.ndarray, inst: Instance, rng: np.random.Generator,
           max_moves: int = 200) -> np.ndarray:
    """Trả về bản sao chrom đã sửa: buổi bị trùng (phòng/GV) hoặc sai cỡ/phòng bận
    thì thử dời sang ô (phòng, tiết) trống phù hợp. Không làm tăng tổng vi phạm cứng."""
    raise NotImplementedError("Gói 5")
