"""Điểm vào: chạy các kịch bản E1..E6.  [Gói 1]

    python -m src.main --exp E1
    python -m src.main --exp E2 --seed 7
    python -m src.main --exp all
"""
from __future__ import annotations

import argparse

from src import config as C


def run_experiment(exp: str, seed: int) -> None:
    """Sinh Instance -> in feasibility_report -> run_ga -> evaluate + validate lịch tốt nhất
    -> plot_history + export_schedule vào results/<exp>/..."""
    raise NotImplementedError("Gói 1")


def main() -> None:
    ap = argparse.ArgumentParser(description="HW3 – Class Scheduling using GA")
    ap.add_argument("--exp", default="E1", choices=[*C.EXPERIMENTS, "all"])
    ap.add_argument("--seed", type=int, default=C.SEED)
    args = ap.parse_args()
    for exp in (C.EXPERIMENTS if args.exp == "all" else [args.exp]):
        print(f"== {exp}: {C.EXPERIMENTS[exp]}")
        run_experiment(exp, args.seed)


if __name__ == "__main__":
    main()
