# HW3 – Class Scheduling using Genetic Algorithm (CO3061, HCMUT)

Bài tập nhóm 6 người, mỗi người 1 "gói việc". Tài liệu gốc: đề `HW3.pdf`, kế hoạch `HW3_ChiaViec.pdf` (ở `~/Downloads/`).
Hạn nộp LMS: **CN 29/11/2026 23:59** (mục tiêu nội bộ: code đóng băng 19/11, nộp trước 22/11). Nộp `HW3_YOURNAME.zip` = source + báo cáo PDF.

## Lệnh

Dùng **uv**, không dùng pip/venv thủ công. Dependency khai báo trong `pyproject.toml`, Python pin ở `.python-version` (3.12).

```bash
uv sync                                  # tạo .venv + cài deps (gồm nhóm dev: pytest)
uv run python -m src.main --exp E1       # E1..E6 hoặc all
uv run pytest                            # pyproject đã set pythonpath = .
uv add <pkg>   /   uv add --dev <pkg>    # thêm thư viện (commit cả uv.lock)
```

Import luôn dạng tuyệt đối `from src.xxx import ...`; chạy bằng `python -m src.main` (không chạy `python src/main.py`).

## Chủ sở hữu file (không sửa file của gói khác khi chưa báo nhóm)

| File | Gói |
|---|---|
| `src/config.py`, `src/data_generator.py`, `src/main.py` | 1 – Dữ liệu & Tích hợp |
| `src/chromosome.py` | 2 – Mã hóa & Khởi tạo |
| `src/fitness_hard.py`, `src/validator.py` | 3 – Fitness cứng |
| `src/fitness_soft.py` | 4 – Fitness mềm & Bonus |
| `src/ga.py`, `src/repair.py` | 5 – GA & Thí nghiệm |
| `src/visualize.py`, `src/export.py`, `README.md` | 6 – Trực quan & Tài liệu |
| `src/_mocks.py` | dùng chung, tạm thời – xóa import sau mốc 1 (15/11) |

## Giao diện chung – KHÔNG đổi tên/chữ ký khi chưa báo cả nhóm

```
Instance(n_rooms, room_size[R], room_avail[R,5,6] bool, sec_course[S], sec_reg[S],
         prof_fav[P,3], prof_can_teach: list[P])                       # Gói 1
init_population(inst, pop_size, rng) -> ndarray (pop, S, 6)            # Gói 2
decode(chrom) -> ndarray (2S, 5) [section, day, slot, room, prof]      # Gói 2 (đã cài)
hard_penalties(chrom, inst) -> {'H1','H3a','H3b','H4','H6'}            # Gói 3
validate(chrom, inst) -> {..., 'violations': [str]}                    # Gói 3
soft_penalties(chrom, inst) -> {'S1','S2','S3','S4','B1','B2'}         # Gói 4
evaluate(chrom, inst, weights) -> (fitness, penalty, details)          # Gói 4
run_ga(inst, params, evaluate_fn=None) -> (best_chrom, history)        # Gói 5
    history[i] ⊇ {'gen','best','avg','best_penalty','avg_penalty','hard_best','soft_best','time'}
plot_history(history, path); plot_room_heatmap(chrom, inst, path)      # Gói 6
export_schedule(chrom, inst, folder)                                   # Gói 6
```

## Quy ước mô hình (đã chốt)

- Chromosome = ndarray int `(S, 6)`: `[pattern, slot1, slot2, room1, room2, prof]`, chỉ số cột lấy từ `config.GENE_*`.
- `pattern` trỏ vào `config.DAY_PATTERNS` (6 cặp ngày hợp lệ) → H2, H5 tự thỏa, không phạt.
- Ngày 0..4 = T2..T6; tiết 0..5; sáng = tiết 0–2, chiều = 3–5.
- 60 môn (mã 0..59), section `i` thuộc môn `i // 8` (đề ghi 1–50 là mâu thuẫn → ghi giả định trong báo cáo).
- `Penalty = W_H·(H1+H3a+H3b+H4+H6[+B2]) + Σ w·S + w_B1·B1`, `Fitness = 1/(1+Penalty)`; trọng số trong `config.WEIGHTS`.
- Số phòng là tham số: E1 = 20 phòng (cận dưới 360 buổi trùng phòng), E2 = 32/36/40 phòng.
- Kích thước lấy từ `inst` (`inst.n_sections`, `inst.n_rooms`, `inst.n_profs`), không dùng hằng số → unit test chạy được với instance nhỏ.
- Mọi random đi qua `np.random.Generator` được truyền vào (`rng`), không dùng `np.random.*` toàn cục → tái lập theo seed.
- Fitness phải vector hóa numpy (mục tiêu < 5 ms/cá thể); `validator.py` thì cố ý viết vòng lặp thuần để kiểm tra chéo.

## Kiểm chứng

- Mỗi ràng buộc có unit test với ví dụ nhỏ tự dựng, có đáp án tính tay (`tests/`).
- `hard_penalties` và `validate` phải ra cùng số trên lịch ngẫu nhiên (test kiểm tra chéo).
- Kết quả trong báo cáo chỉ lấy từ log thật trong `results/`, ghi kèm seed và config.
