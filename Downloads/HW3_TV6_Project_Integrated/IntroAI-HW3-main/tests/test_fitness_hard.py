"""Test ràng buộc cứng H1, H3a, H3b, H4, H6.  [Gói 3: Một test per ràng buộc + cross-check validator]"""
from __future__ import annotations

import numpy as np
import pytest

from src import config as C
from src.fitness_hard import hard_penalties
from src.validator import validate
from src.chromosome import decode
from src._mocks import fake_chromosome


@pytest.mark.skip(reason="TODO Gói 3")
def test_h1_room_size_violation(tiny_inst):
    """H1: Phạt khi room_size[room] < sec_reg[section].

    Scenario tính tay:
    - tiny_inst: room_size=[0, 2] (nhỏ, lớn), sec_reg=[0, 2, 1, 0]
    - Section 1 (cỡ 2) → cần phòng kích ≥2 → phòng 1 (kích 2) OK, phòng 0 (kích 0) VI PHẠM
    - Xây dựng chrom sao cho session 0 của section 1 dùng phòng 0 → H1 = 1
    - Kỳ vọng: hard_penalties(chrom, tiny_inst)['H1'] == 1
    """
    ...


@pytest.mark.skip(reason="TODO Gói 3")
def test_h3a_prof_multiple_sessions_same_slot(tiny_inst):
    """H3a: GV dạy ≥2 buổi cùng ngày, cùng tiết → phạt (số buổi - 1).

    Scenario tính tay:
    - tiny_inst: 3 GV, 4 section
    - Xây dựng chrom sao cho prof 0 dạy 2 session:
      - Section 0: prof=0, pattern=0 (T2,T4), slot1=1, slot2=2
      - Section 2: prof=0, pattern=0 (T2,T4), slot1=1, slot2=3
      - → 2 buổi cùng ngày T2, cùng tiết 1 → H3a += (2-1) = 1
    - Kỳ vọng: hard_penalties(chrom, tiny_inst)['H3a'] >= 1
    """
    ...


@pytest.mark.skip(reason="TODO Gói 3")
def test_h3b_prof_too_many_sections(tiny_inst):
    """H3b: GV dạy > MAX_SECTIONS_PER_PROF → phạt (số section - max).

    Scenario tính tay:
    - config.MAX_SECTIONS_PER_PROF = 10
    - tiny_inst: 3 GV, 4 section
    - Xây chrom sao cho prof 0 được gán 2 section (trong 4) → OK (< 10)
    - Kỳ vọng: hard_penalties(chrom, tiny_inst)['H3b'] == 0
    - (Để test H3b > 0, cần instance lớn với 60 GV, nhiều section, hoặc instance khác)
    """
    ...


@pytest.mark.skip(reason="TODO Gói 3")
def test_h4_room_unavailable(tiny_inst):
    """H4: Phạt khi room_avail[room, day, slot] == False.

    Scenario tính tay:
    - tiny_inst mặc định: room_avail = tất cả True
    - Tạo inst' với room_avail[1, 0, 1] = False (phòng 1, T2, tiết 1)
    - Xây chrom sao cho section nào đó dùng phòng 1, T2, tiết 1 → H4 = 1
    - Kỳ vọng: hard_penalties(chrom, inst')['H4'] >= 1
    """
    ...


@pytest.mark.skip(reason="TODO Gói 3")
def test_h6_room_multiple_sessions_same_slot(tiny_inst):
    """H6: Phòng dùng ≥2 buổi cùng ngày, cùng tiết → phạt (số buổi - 1).

    Scenario tính tay:
    - tiny_inst: 2 phòng
    - Xây chrom sao cho 2 section khác nhau dùng cùng phòng, ngày, tiết:
      - Section 0: room1=1, pattern=0 (T2), slot1=1
      - Section 1: room1=1, pattern=0 (T2), slot1=1
      - → Phòng 1, T2, tiết 1: 2 buổi → H6 += (2-1) = 1
    - Kỳ vọng: hard_penalties(chrom, tiny_inst)['H6'] >= 1
    """
    ...


@pytest.mark.skip(reason="TODO Gói 3")
def test_hard_penalties_vs_validator_cross_check(tiny_inst, rng):
    """hard_penalties (vector) và validate (vòng lặp) phải ra cùng kết quả.

    Scenario:
    - Sinh 10 chromosome ngẫu nhiên từ _mocks.fake_chromosome
    - Với mỗi chrom:
      - hard = hard_penalties(chrom, tiny_inst)
      - val = validate(chrom, tiny_inst)
      - Kỳ vọng: hard['H1'] == val['H1'], ..., hard['H6'] == val['H6']
    """
    ...
