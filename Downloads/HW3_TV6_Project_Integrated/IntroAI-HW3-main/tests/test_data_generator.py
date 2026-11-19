"""Test sinh dữ liệu Instance.  [Gói 1: Tái lập theo seed, section→course, prof_fav⊆prof_can_teach, khả thi]"""
from __future__ import annotations

import numpy as np
import pytest

from src import config as C
from src.data_generator import generate_instance, feasibility_report


@pytest.mark.skip(reason="TODO Gói 1")
def test_generate_instance_seed_reproducibility():
    """Hai lần sinh cùng seed phải ra Instance giống hệt.

    Scenario tính tay:
    - Seed = 123
    - Lần 1: inst1 = generate_instance(seed=123)
    - Lần 2: inst2 = generate_instance(seed=123)
    - Kỳ vọng: inst1.room_size == inst2.room_size, inst1.sec_course == inst2.sec_course, ...
    """
    ...


@pytest.mark.skip(reason="TODO Gói 1")
def test_section_belongs_to_course():
    """Section i phải thuộc môn i // SECTIONS_PER_COURSE.

    Scenario:
    - 60 môn × 8 section = 480 section
    - sec_course[i] phải = i // 8
    - Ví dụ: section 0–7 → môn 0, section 8–15 → môn 1, ...
    """
    ...


@pytest.mark.skip(reason="TODO Gói 1")
def test_prof_fav_subset_of_can_teach():
    """prof_fav[p] ⊆ prof_can_teach[p] (môn yêu thích phải nằm trong danh sách dạy được).

    Scenario:
    - 60 GV, mỗi GV 3 môn yêu thích (prof_fav)
    - prof_can_teach[p] = danh sách từ 5–10 môn
    - Kỳ vọng: ∀p, ∀c ∈ prof_fav[p] → c ∈ prof_can_teach[p]
    """
    ...


@pytest.mark.skip(reason="TODO Gói 1")
def test_feasibility_report_room_sizes():
    """feasibility_report(inst) kiểm tra điều kiện kích thước phòng.

    Scenario:
    - Instance nhỏ: 2 phòng, ~50 section
    - Kiểm tra n_k (số buổi cỡ k), c_k (ô cỡ k)
    - Kỳ vọng: report ghi rõ cond_n2_le_c2, cond_n1n2_le_c1c2, cond_total (đúng/sai)
    """
    ...


@pytest.mark.skip(reason="TODO Gói 1")
def test_feasibility_report_room_clash_lower_bound():
    """feasibility_report ghi cận dưới xung đột phòng.

    Scenario:
    - 20 phòng × 5 ngày × 6 tiết = 600 ô khả dụng (nếu tất cả)
    - 960 buổi cần xếp
    - Cận dưới = max(0, 960 - 600) = 360 (vào cùng phòng–ngày–tiết)
    - Kỳ vọng: report['room_clash_lower_bound'] = 360
    """
    ...
