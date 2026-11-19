# HW3 – Xếp lịch học dùng Genetic Algorithm (CO3061, HCMUT)

**Đề tài:** Xây dựng hệ thống xếp lịch học tự động cho trường đại học sử dụng giải thuật di truyền (GA), thỏa mãn các ràng buộc về phòng học, giáo viên, thời gian và tối ưu hóa các tiêu chí mềm.

## Cài đặt

Dùng [uv](https://docs.astral.sh/uv/) (không dùng pip). Python được pin ở `.python-version` (3.12), uv tự tải nếu máy chưa có.

```bash
uv sync          # tạo .venv và cài toàn bộ dependency theo uv.lock
```

## Chạy

```bash
# Chạy thí nghiệm E1
uv run python -m src.main --exp E1

# Chạy thí nghiệm E2 với seed khác
uv run python -m src.main --exp E2 --seed 7

# Chạy tất cả thí nghiệm E1..E6
uv run python -m src.main --exp all

# Chạy pytest
uv run pytest
```

## Cấu trúc thư mục

```
src/
  config.py              # Hằng số, trọng số, tham số GA, kịch bản thí nghiệm (Gói 1)
  data_generator.py      # Sinh Instance ngẫu nhiên (Gói 1)
  chromosome.py          # Mã hóa, giải mã, khởi tạo quần thể (Gói 2)
  fitness_hard.py        # Ràng buộc cứng H1, H3a, H3b, H4, H6 (Gói 3)
  validator.py           # Kiểm tra lại bằng vòng lặp (Gói 3)
  fitness_soft.py        # Ràng buộc mềm S1..S4, B1, B2 (Gói 4)
  ga.py                  # Vòng lặp GA, toán tử (Gói 5)
  visualize.py           # Vẽ đồ thị fitness, heatmap (Gói 6)
  export.py              # Xuất CSV, Excel, HTML (Gói 6)
  main.py                # Điểm vào (Gói 1)
  _mocks.py              # Dữ liệu giả tạm thời

tests/
  conftest.py            # Fixtures pytest
  test_data_generator.py # Test sinh dữ liệu
  test_chromosome.py     # Test mã hóa
  test_fitness_hard.py   # Test ràng buộc cứng
  test_fitness_soft.py   # Test ràng buộc mềm
  test_ga.py             # Test GA
  test_export_visualize.py # Test xuất và vẽ

results/
  figures/               # Lưu PNG
  schedules/             # Lưu CSV/Excel/HTML
  logs/                  # Lưu log

report/
  outline.md             # Khung báo cáo
  HW3_YOURNAME.pdf       # Báo cáo cuối cùng
```

## Phân công (Gói → File → Người)

| Gói | Trách nhiệm | File chính | Người |
|---|---|---|---|
| 1 | Dữ liệu & Tích hợp | config.py, data_generator.py, main.py | _điền tên_ |
| 2 | Mã hóa & Khởi tạo | chromosome.py | _điền tên_ |
| 3 | Fitness cứng | fitness_hard.py, validator.py | _điền tên_ |
| 4 | Fitness mềm & Bonus | fitness_soft.py | _điền tên_ |
| 5 | GA & Thí nghiệm | ga.py, repair.py | _điền tên_ |
| 6 | Trực quan & Tài liệu | visualize.py, export.py, README.md | _điền tên_ |

## Giả định

- **60 môn học** (mã 0–59): Đề ghi 1–50 nhưng 50 môn × 8 section/môn = 400 < 480 section cần xếp → giả định có 60 môn để đạt 480 section.
- **480 section**: 60 môn × 8 section/môn.
- **960 buổi**: 480 section × 2 buổi/section (T2–T6: 5 ngày, Chỉ xét Thứ 2 đến Thứ 6).
- **Thời gian**: Sáng = tiết 1–3 (slot 0–2), Chiều = tiết 4–6 (slot 3–5).
- **6 cặp ngày hợp lệ**: (T2,T4), (T2,T5), (T2,T6), (T3,T5), (T3,T6), (T4,T6) – thỏa H2 (không cùng ngày, không liền nhau).
- **Tham số phòng** theo kịch bản:
  - E1: 20 phòng (cận dưới xung đột = 360)
  - E2: 32, 36, 40 phòng
- **Seed**: Để tái lập kết quả, ghi seed trong báo cáo; mặc định = 42.

## Kiểm thử

```bash
# Chạy tất cả test
uv run pytest -v

# Chạy riêng module
uv run pytest tests/test_chromosome.py -v
```

Mỗi ràng buộc (H1, H3a, H3b, H4, H6, S1–S4, B1, B2) có unit test với ví dụ tính tay.
Hard penalties và validator phải ra cùng kết quả trên lịch ngẫu nhiên.

## TV6 – Trực quan hóa và xuất thời khóa biểu

TV6 cung cấp hai hàm trong `src/visualize.py` và hàm xuất trong `src/export.py`:

```python
from src.visualize import plot_history, plot_room_heatmap
from src.export import export_schedule

# history là danh sách các dict do run_ga trả về
plot_history(history, 'results/figures/fitness.png')
plot_room_heatmap(best_chrom, inst, 'results/figures/room_heatmap.png')
export_schedule(best_chrom, inst, 'results/schedules')
```

`plot_history()` yêu cầu các key `gen`, `best_penalty`, `avg_penalty`, `hard_best`; hỗ trợ giá trị penalty bằng 0. Heatmap biểu diễn phòng × (ngày, tiết): trắng = trống, xanh = 1 buổi, đỏ = từ 2 buổi, xám = phòng không khả dụng. CSV gồm 1 dòng/buổi, ID người/phòng/môn/lớp bắt đầu từ 1. Excel có 3 sheet `By Room`, `By Professor`, `By Day` và đánh dấu đỏ dòng có xung đột. HTML có menu xem tổng quan theo ngày, xem riêng phòng và giảng viên. Cờ xung đột bao gồm trùng phòng, trùng giảng viên, phòng không khả dụng, phòng thiếu sức chứa. Không đồng nhất cờ `conflict` (đếm số **buổi bị ảnh hưởng**) với H6/H3a (đếm **số lần trùng** theo occupancy−1).

**Demo độc lập TV6 (khi các gói khác chưa hoàn thiện):**

```bash
uv run python -m src.demo_tv6
uv run pytest tests/test_export_visualize.py -v
```

Demo tạo file trong `results/tv6_demo/`; tất cả dữ liệu demo đều là **MOCK**, không phải kết quả thực nghiệm GA. Sau khi TV1–TV5 hoàn tất, dùng lịch và history thực từ `run_ga()` để tạo hình cuối cho báo cáo. Không dùng hình mô phỏng để khẳng định kết quả tối ưu.

**Ghi chú tích hợp:** `src/main.py` thuộc TV1, hiện cần gọi `plot_history(history, path)`, `plot_room_heatmap(best_chrom, inst, path)` và `export_schedule(best_chrom, inst, folder)` sau `run_ga`. TV6 không sửa code của các gói còn lại.
