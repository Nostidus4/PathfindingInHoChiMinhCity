"""Giao diện dòng lệnh `hcmc` (T0). Owner: P6.

Lệnh:
    hcmc route --start A --goal B --time 08:00 --heuristic dynamic_ub [--trace] [--map]
    hcmc compare --start A --goal B --time 08:00      # chạy cả 4 mode
    hcmc validate                                      # admissibility/consistency/FIFO
    hcmc experiments                                   # chạy runner + plots
    hcmc list-pois [--district "Quan 1"]
Phải xử lý: input sai (POI không tồn tại, giờ sai định dạng, mode sai) và no-path
bằng thông báo rõ ràng + exit code != 0, không in traceback.
Chỉ gọi Pathfinder, không gọi astar trực tiếp.
"""

from __future__ import annotations

import argparse
import sys

from src.cost.heuristics import HEURISTIC_MODES


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hcmc", description="Pathfinding in Ho Chi Minh City")
    sub = p.add_subparsers(dest="command", required=True)

    r = sub.add_parser("route", help="Tìm đường từ start tới goal")
    r.add_argument("--start", required=True)
    r.add_argument("--goal", required=True)
    r.add_argument("--time", default="08:00", help="Giờ xuất phát HH:MM")
    r.add_argument("--heuristic", default="dynamic_ub", choices=HEURISTIC_MODES)
    r.add_argument("--trace", action="store_true", help="In từng bước A*")
    r.add_argument("--map", action="store_true", help="Xuất bản đồ HTML")

    c = sub.add_parser("compare", help="So sánh 4 heuristic mode")
    c.add_argument("--start", required=True)
    c.add_argument("--goal", required=True)
    c.add_argument("--time", default="08:00")

    sub.add_parser("validate", help="Kiểm admissibility / consistency / FIFO")
    sub.add_parser("experiments", help="Chạy thí nghiệm và vẽ biểu đồ")

    lp = sub.add_parser("list-pois", help="Liệt kê POI")
    lp.add_argument("--district", default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # TODO(P6): dispatch từng lệnh -> Pathfinder ; bắt ValueError/no-path -> in lỗi, return 1
    print(f"Lệnh '{args.command}' chưa được cài đặt (TODO P6).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
