"""Kiểm tra độc lập lịch cuối – viết bằng vòng lặp đơn giản, KHÔNG dùng lại fitness_hard.  [Gói 3]

Mục đích: kiểm tra chéo kết quả của fitness_hard (vector hóa) để bắt lỗi cài đặt.
"""
from __future__ import annotations

import numpy as np

from src.data_generator import Instance


def validate(chrom: np.ndarray, inst: Instance) -> dict:
    """Đếm lại H1, H2, H3a, H3b, H4, H5, H6 bằng vòng lặp/dict thuần Python.

    Trả về {'H1': int, ..., 'H6': int, 'violations': list[str]} – violations mô tả
    từng vi phạm (vd. "H6: room 3, T2 tiết 1: sections 12, 87") để in/ghi log.
    """
    raise NotImplementedError("Gói 3")
