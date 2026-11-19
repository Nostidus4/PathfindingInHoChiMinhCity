"""Test mã hóa chromosome.  [Gói 2: init_population shape/dtype/domain, rooms, pattern-balance]"""
from __future__ import annotations

import numpy as np
import pytest

from src import config as C
from src.chromosome import init_population, decode
from src.data_generator import Instance


@pytest.mark.skip(reason="TODO Gói 2")
def test_init_population_shape_and_dtype(tiny_inst):
    """init_population trả về ndarray (pop_size, n_sections, 6) với dtype int64.

    Scenario:
    - tiny_inst: 4 section
    - pop_size = 10
    - Kỳ vọng: shape (10, 4, 6), dtype int64
    """
    ...


@pytest.mark.skip(reason="TODO Gói 2")
def test_init_population_gene_domain(tiny_inst):
    """Mỗi gene nằm trong miền hợp lệ.

    Scenario:
    - pattern ∈ [0, 6)
    - slot1, slot2 ∈ [0, 6)
    - room1, room2 ∈ [0, n_rooms)
    - prof ∈ [0, n_profs)
    - Kỳ vọng: ∀gene ∈ valid range
    """
    ...


@pytest.mark.skip(reason="TODO Gói 2")
def test_init_population_room_size_constraint(tiny_inst):
    """Phòng được chọn phải đủ cỡ cho section.

    Scenario:
    - tiny_inst: room_size = [0, 2]
    - Section 1 cỡ 2 (sec_reg=2) → phải dùng phòng 1 (kích 2)
    - Section 2 cỡ 1 (sec_reg=1) → có thể dùng phòng 1 hoặc (phòng 0 nếu có kích 1+, ngoài ví dụ)
    - Kỳ vọng: room_size[chrom[:, GENE_ROOM*]] >= sec_reg[:]
    """
    ...


@pytest.mark.skip(reason="TODO Gói 2")
def test_random_chromosome_weighted_day_pattern(tiny_inst, rng):
    """random_chromosome cân bằng tải ngày: T2/T6 xuất hiện nhiều hơn T3/T4/T5.

    Scenario:
    - Sinh 1000 chromosome ngẫu nhiên (nhỏ nhưng đủ thống kê)
    - Đếm tần suất mỗi pattern (0–5) → tần suất ngày (0–4)
    - Kỳ vọng: Ngày 0 (T2) và 4 (T6) xuất hiện ~3/6 tần suất,
              Ngày 1 (T3), 2 (T4), 3 (T5) xuất hiện ~2/6 tần suất
    """
    ...


def test_decode_shape_and_days(tiny_inst):
    """decode(chrom) trả về (2*n_sections, 5) với ngày đúng.

    Scenario tính tay:
    - tiny_inst: 4 section
    - Xây dựng chrom 4×6 bằng tay:
      - Section 0: pattern=0 (T2,T4), slot1=1, slot2=2, room1=0, room2=1, prof=0
      - Section 1: pattern=1 (T2,T5), slot1=0, slot2=3, room1=1, room2=0, prof=1
      - Section 2: pattern=2 (T2,T6), ...
      - Section 3: pattern=3 (T3,T5), ...
    - decode(chrom) → (8, 5)
    - Dòng 0, 1: session 0 buổi 1, 2 (section=0, days từ DAY_PATTERNS[0])
    - Kỳ vọng:
      - Shape (8, 5) ✓
      - chrom[0, 0] = pattern=0 → DAY_PATTERNS[0] = (0, 2) (T2, T4)
      - out[0, 1] = 0 (T2), out[1, 1] = 2 (T4) ✓
    """
    chrom = np.array([
        [0, 1, 2, 0, 1, 0],  # pattern 0 = (T2, T4)
        [1, 0, 3, 1, 0, 1],  # pattern 1 = (T2, T5)
        [2, 2, 1, 0, 1, 2],  # pattern 2 = (T2, T6)
        [3, 3, 4, 1, 0, 0],  # pattern 3 = (T3, T5)
    ], dtype=np.int64)

    out = decode(chrom)

    # Kiểm tra shape
    assert out.shape == (8, 5), f"Expected shape (8, 5), got {out.shape}"

    # Kiểm tra section index
    assert np.array_equal(out[:, 0], [0, 0, 1, 1, 2, 2, 3, 3])

    # Kiểm tra days từ DAY_PATTERNS
    pattern_to_days = C.DAY_PATTERNS
    for sec_idx in range(4):
        pattern = chrom[sec_idx, C.GENE_PATTERN]
        day1, day2 = pattern_to_days[pattern]
        # Session 0: day=day1, Session 1: day=day2
        assert out[2 * sec_idx, 1] == day1, f"Section {sec_idx} session 0: expected day {day1}, got {out[2 * sec_idx, 1]}"
        assert out[2 * sec_idx + 1, 1] == day2, f"Section {sec_idx} session 1: expected day {day2}, got {out[2 * sec_idx + 1, 1]}"

    # Kiểm tra slot
    assert np.array_equal(out[0::2, 2], chrom[:, C.GENE_SLOT1])  # Session 0: slot từ GENE_SLOT1
    assert np.array_equal(out[1::2, 2], chrom[:, C.GENE_SLOT2])  # Session 1: slot từ GENE_SLOT2

    # Kiểm tra room
    assert np.array_equal(out[0::2, 3], chrom[:, C.GENE_ROOM1])  # Session 0: room từ GENE_ROOM1
    assert np.array_equal(out[1::2, 3], chrom[:, C.GENE_ROOM2])  # Session 1: room từ GENE_ROOM2

    # Kiểm tra prof
    assert np.array_equal(out[:, 4], np.repeat(chrom[:, C.GENE_PROF], 2))
