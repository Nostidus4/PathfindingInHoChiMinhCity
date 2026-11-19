"""Fixtures pytest dùng chung cho tất cả test."""
from __future__ import annotations

import numpy as np
import pytest

from src.data_generator import Instance


@pytest.fixture
def rng():
    """RNG seed cố định cho tái lập."""
    return np.random.default_rng(0)


@pytest.fixture
def tiny_inst():
    """Instance nhỏ tối ưu cho unit test.

    - 2 phòng: kích thước [0, 2] (nhỏ, lớn)
    - Tất cả ô khả dụng
    - 4 section:
      sec_course = [0, 0, 1, 1] (2 section môn 0, 2 section môn 1)
      sec_reg = [0, 2, 1, 0] (kích cỡ)
    - 3 giáo viên
    - prof_fav: (3, 3) với course ids trong {0, 1}
    - prof_can_teach: [[0, 1], [0], [1]]
    """
    return Instance(
        n_rooms=2,
        room_size=np.array([0, 2], dtype=np.int64),  # nhỏ, lớn
        room_avail=np.ones((2, 5, 6), dtype=bool),   # tất cả khả dụng
        sec_course=np.array([0, 0, 1, 1], dtype=np.int64),
        sec_reg=np.array([0, 2, 1, 0], dtype=np.int64),
        prof_fav=np.array([
            [0, 1, 0],
            [0, 1, 1],
            [1, 0, 1],
        ], dtype=np.int64),
        prof_can_teach=[
            np.array([0, 1], dtype=np.int64),
            np.array([0], dtype=np.int64),
            np.array([1], dtype=np.int64),
        ],
        seed=0,
    )
