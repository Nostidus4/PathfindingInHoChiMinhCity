"""Test GA operators và vòng lặp.  [Gói 5: tournament, crossover, mutate, run_ga + history]"""
from __future__ import annotations

import numpy as np
import pytest

from src import config as C
from src.ga import tournament_select, crossover, mutate, run_ga
from src._mocks import fake_instance, fake_chromosome, fake_evaluate


@pytest.mark.skip(reason="TODO Gói 5")
def test_tournament_select_returns_valid_indices(rng):
    """tournament_select(fitness, k, n, rng) trả về n chỉ số cá thể hợp lệ.

    Scenario:
    - fitness shape (100,) – 100 cá thể
    - k = 3 (tournament size)
    - n = 50 (chọn 50 cá thể)
    - Kỳ vọng:
      - indices shape (50,)
      - indices ∈ [0, 100)
      - các indices được chọn từ top trong mỗi tournament
    """
    ...


@pytest.mark.skip(reason="TODO Gói 5")
def test_crossover_keeps_row_from_parents(rng):
    """crossover (uniform theo section) → 2 child có mỗi section từ cha hoặc mẹ.

    Scenario tính tay:
    - parent1 shape (10, 6), parent2 shape (10, 6)
    - child1, child2 = crossover(parent1, parent2, rng)
    - Kỳ vọng:
      - child1, child2 shape (10, 6)
      - ∀ section i: child1[i] ∈ {parent1[i], parent2[i]} (giống nguyên dòng)
      - tương tự child2
    """
    ...


@pytest.mark.skip(reason="TODO Gói 5")
def test_mutate_stays_in_valid_domain(tiny_inst, rng):
    """mutate(chrom, inst, n_genes, rng) → giá trị mới vẫn trong miền hợp lệ.

    Scenario:
    - chrom từ tiny_inst (4 section, 2 phòng, 3 GV)
    - Gọi mutate(chrom, tiny_inst, n_genes=1, rng)
    - Kỳ vọng:
      - pattern ∈ [0, 6)
      - slot ∈ [0, 6)
      - room ∈ [0, 2)
      - prof ∈ [0, 3)
      - room_size[room] >= sec_reg[section]
      - prof ∈ prof_can_teach[section's course]
    """
    ...


@pytest.mark.skip(reason="TODO Gói 5")
def test_run_ga_returns_best_and_history(rng):
    """run_ga(inst, params, evaluate_fn) → (best_chrom, history) đúng định dạng.

    Scenario:
    - inst = fake_instance (nhỏ, seed=0)
    - params = custom GA_PARAMS (generations=10 để nhanh, pop_size=20)
    - evaluate_fn = fake_evaluate (từ _mocks)
    - best_chrom, history = run_ga(inst, params, fake_evaluate)
    - Kỳ vọng:
      - best_chrom shape (n_sections, 6)
      - history: list[dict], len = generations
      - history[i] gồm: 'gen', 'best', 'avg', 'best_penalty', 'avg_penalty',
                        'hard_best', 'soft_best', 'time'
      - history[i]['gen'] = i
    """
    ...
