"""Test ràng buộc mềm S1–S4, B1, B2, và evaluate.  [Gói 4: S1/S2/S3/S4/B1/B2 + fitness formula]"""
from __future__ import annotations

import numpy as np
import pytest

from src import config as C
from src.fitness_soft import soft_penalties, evaluate
from src.chromosome import decode


@pytest.mark.skip(reason="TODO Gói 4")
def test_s1_prof_day_spread(tiny_inst):
    """S1: Giảm gãy giờ GV (khoảng trống ngày) + cân bằng số ngày.

    Scenario tính tay:
    - GV p dạy 4 buổi (ví dụ)
    - Nếu all 4 buổi cùng 1 ngày → gãy lớn
    - Nếu spread qua 3 ngày → gãy nhỏ
    - S1 = Σ (GV,day) (tiết_max - tiết_min + 1 - số_buổi) + λ × Σ GV (num_day - ceil(num_session/3))
    - Kỳ vọng: S1 >= 0, giảm khi spread tốt hơn
    """
    ...


@pytest.mark.skip(reason="TODO Gói 4")
def test_s2_prof_morning_afternoon(tiny_inst):
    """S2: Số cặp (GV, ngày) vừa có tiết sáng vừa chiều.

    Scenario tính tay:
    - GV p, ngày t: có buổi sáng (tiết 0–2) và chiều (tiết 3–5)
    - Ví dụ: Section A buổi 1 (T2 tiết 1), section B buổi 1 (T2 tiết 4) → cặp (p, T2) = 1
    - S2 = đếm cặp này
    - Kỳ vọng: S2 >= 0
    """
    ...


@pytest.mark.skip(reason="TODO Gói 4")
def test_s3_section_split_morning_afternoon(tiny_inst):
    """S3: Section có 2 buổi khác nửa ngày (một sáng, một chiều).

    Scenario tính tay:
    - Section s: slot1 ∈ {0,1,2}, slot2 ∈ {3,4,5}
    - S3 = số section với (slot1 < 3) != (slot2 < 3)
    - Kỳ vọng: S3 = số section có split
    """
    ...


@pytest.mark.skip(reason="TODO Gói 4")
def test_s4_room_capacity_waste(tiny_inst):
    """S4: Giảm lãng phí kích thước phòng (room_size - sec_reg khi room_size > sec_reg).

    Scenario tính tay:
    - Section: sec_reg = 1, room_size = 2 → lãng phí = 2 - 1 = 1
    - S4 = Σ (room_size - sec_reg) trên tất cả buổi có room_size >= sec_reg
    - Kỳ vọng: S4 >= 0
    """
    ...


@pytest.mark.skip(reason="TODO Gói 4")
def test_b1_prof_teach_favorite_course(tiny_inst):
    """B1 (Bonus 1): GV không dạy section nào từ 3 môn yêu thích → phạt.

    Scenario tính tay:
    - tiny_inst: prof_fav = [[0, 1, 0], [0, 1, 1], [1, 0, 1]]
    - Nếu prof 0 không dạy section nào từ môn 0 hay 1 → B1 += 1
    - Kỳ vọng: B1 = số GV không dạy môn yêu thích
    """
    ...


@pytest.mark.skip(reason="TODO Gói 4")
def test_b2_prof_can_teach_violation(tiny_inst):
    """B2 (Bonus 2): Section có môn không nằm prof_can_teach[prof] → phạt (hoặc hard).

    Scenario tính tay:
    - tiny_inst: prof_can_teach = [[0,1], [0], [1]]
    - Nếu prof 1 dạy section môn 1 → VI PHẠM (prof 1 chỉ dạy môn 0)
    - B2 = số section vi phạm
    - Nếu config.B2_IS_HARD = True → tính vào hard
    - Kỳ vọng: B2 >= 0, hoặc hard penalty
    """
    ...


@pytest.mark.skip(reason="TODO Gói 4")
def test_evaluate_returns_correct_fitness(tiny_inst):
    """evaluate(chrom, inst, weights) → (fitness, penalty, details).

    Scenario tính tay:
    - Xây chrom bất kỳ (hoặc sinh ngẫu nhiên)
    - fitness, penalty, details = evaluate(chrom, tiny_inst)
    - Kỳ vọng:
      - fitness ∈ [0, 1]
      - penalty ≥ 0
      - fitness == 1.0 / (1.0 + penalty)
      - details gồm H1–H6, S1–S4, B1, B2, hard_total, soft_total
    """
    ...
