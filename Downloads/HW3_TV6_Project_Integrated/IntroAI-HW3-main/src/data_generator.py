"""Sinh dữ liệu ngẫu nhiên (Instance) và kiểm tra khả thi.  [Gói 1]

Instance là input DUY NHẤT mà các module khác nhận về dữ liệu bài toán.
Không đổi tên field khi chưa báo cả nhóm.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src import config as C


@dataclass
class Instance:
    n_rooms: int
    room_size: np.ndarray       # (R,) int in {0,1,2}
    room_avail: np.ndarray      # (R, N_DAYS, N_SLOTS) bool – False = phòng bận (H4)
    sec_course: np.ndarray      # (S,) int, mã môn 0..N_COURSES-1 của mỗi section
    sec_reg: np.ndarray         # (S,) int in {0,1,2}, cỡ đăng ký của section
    prof_fav: np.ndarray        # (P, 3) int, 3 môn yêu thích của mỗi GV (Bonus 1)
    prof_can_teach: list        # list[P] các ndarray/list mã môn GV được dạy (Bonus 2)
    seed: int = 0

    @property
    def n_sections(self) -> int:
        return len(self.sec_course)

    @property
    def n_profs(self) -> int:
        return len(self.prof_fav)


def generate_instance(n_rooms: int = C.N_ROOMS_DEFAULT, seed: int = C.SEED,
                      params: dict | None = None) -> Instance:
    """Sinh Instance ngẫu nhiên, tái lập được theo seed.

    Yêu cầu:
    - section i thuộc môn i // SECTIONS_PER_COURSE.
    - prof_fav[p] ⊆ prof_can_teach[p]; mỗi môn phải có ít nhất 1 GV được dạy,
      và tổng sức chứa đủ (mỗi GV ≤ MAX_SECTIONS_PER_PROF section).
    - Dữ liệu sinh ra phải qua feasibility_report() (cỡ phòng đủ cho từng loại).
    """
    raise NotImplementedError("Gói 1")


def feasibility_report(inst: Instance) -> dict:
    """Trả về các con số khả thi để in ra và đưa vào báo cáo (mục 2 tài liệu chia việc).

    Gợi ý keys: 'n_k' (số buổi theo cỡ đăng ký), 'c_k' (số ô khả dụng theo cỡ phòng),
    'cond_n2_le_c2', 'cond_n1n2_le_c1c2', 'cond_total', 'room_clash_lower_bound'
    (= max(0, N_SESSIONS - tổng ô khả dụng)), 'min_rooms_needed'.
    """
    raise NotImplementedError("Gói 1")
