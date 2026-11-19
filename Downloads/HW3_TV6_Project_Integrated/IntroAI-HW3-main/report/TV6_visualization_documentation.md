# TV6 — Trực quan hóa và tài liệu (nội dung để ghép báo cáo)

**Môn học:** CO3061 — Introduction to Artificial Intelligence  
**Đề tài:** Class Scheduling Using Genetic Algorithm  
**Phụ trách:** TV6 — *điền họ tên và MSSV từ danh sách nhóm đã xác nhận*.

## 7. Trực quan hóa và trình bày kết quả

### 7.1. Đồ thị tiến trình tối ưu

Module `src/visualize.py` triển khai `plot_history(history, path)`. Dữ liệu `history` là danh sách các bản ghi do module GA của TV5 trả về, gồm `gen`, `best_penalty`, `avg_penalty` và `hard_best`. Biểu đồ hiển thị ba chuỗi theo thế hệ:

- `best_penalty`: mức phạt của cá thể tốt nhất tại thế hệ được ghi log;
- `avg_penalty`: mức phạt trung bình của quần thể;
- `hard_best`: số vi phạm ràng buộc cứng của cá thể tốt nhất.

Hai chuỗi penalty sử dụng trục tung đối xứng logarithmic (`symlog`) để không lỗi khi penalty bằng 0; chuỗi vi phạm cứng sử dụng trục tung riêng theo số đếm. Cách này giúp quan sát mức độ cải thiện hàm mục tiêu lẫn chất lượng thỏa ràng buộc. **Chèn đồ thị từ lượt chạy GA thực tại đây, không dùng biểu đồ MOCK làm minh chứng kết quả.**

### 7.2. Heatmap mức sử dụng phòng học

Hàm `plot_room_heatmap(chrom, inst, path)` giải mã cá thể lịch học thành các buổi với khóa `(room, day, slot)`. Mỗi ô của heatmap biểu diễn một phòng tại một ngày và tiết học. Chú giải: **trắng** = 0 buổi, **xanh** = 1 buổi, **đỏ** = 2 buổi trở lên (trùng phòng), **xám** = phòng không khả dụng. Phòng không khả dụng được ưu tiên tô xám dù có buổi gán vào. Hệ thống vẫn giữ dữ liệu sự kiện để đánh dấu `room_unavailable` trong bảng lịch.

Heatmap có thể hỗ trợ phát hiện trực quan các vùng quá tải, xung đột phòng và vị trí sử dụng phòng không hợp lệ. Ở kịch bản 20 phòng, đề bài cần xếp 960 buổi vào nhiều nhất 600 ô phòng–thời gian (trước khi trừ lịch bận), dẫn đến cận dưới ít nhất **360** lần xung đột phòng theo cách đếm H6 = tổng `max(occupancy - 1, 0)`.

### 7.3. Thời khóa biểu cuối và các định dạng xuất

`export_schedule(chrom, inst, folder)` tạo ba tệp:

| File | Mục đích | Cấu trúc |
|---|---|---|
| `schedule.csv` | Dữ liệu có thể xử lý tự động | Một dòng ứng với một buổi, gồm mã môn, section, số buổi, ngày, tiết, phòng, GV, cỡ phòng và cờ vi phạm |
| `schedule.xlsx` | Xem và lọc thời khóa biểu | Ba sheet `By Room`, `By Professor`, `By Day`, có filter và đánh dấu đỏ các dòng vi phạm |
| `schedule.html` | Xem lịch trực quan | Lưới Thứ 2–6 × 6 tiết, menu lựa chọn tổng quan, từng phòng, từng GV, màu biểu diễn trạng thái |

Trong CSV/Excel/HTML, mã số hiển thị bắt đầu từ 1 để dễ đọc; hệ thống nội bộ sử dụng chỉ số từ 0. `conflict` đánh dấu một **buổi có ít nhất một vi phạm** trong bốn nhóm: trùng phòng, trùng GV, phòng không khả dụng, phòng không đủ cỡ. Đây **không** phải tổng điểm phạt H6 + H3a; các số liệu thí nghiệm phải lấy từ `evaluate()` và `validator()` của các gói tương ứng.

### 7.4. Bảng kết quả thí nghiệm

*Điền bằng đầu ra chạy thực TV5 sau khi hoàn thiện `run_ga` và `evaluate`. Không tự điền các trị số chưa đo được.*

| Kịch bản | Seed | Số phòng | Best penalty | Hard violations | Nhận xét |
|---|---:|---:|---:|---:|---|
| E1 | — | 20 | — | — | So sánh H6 với cận dưới 360 |
| E2 | — | 32/36/40 | — | — | Kiểm tra khả thi theo từng dữ liệu cụ thể |
| E3 | — | — | — | — | Ablation GA / repair / mutation |
| E4 | — | — | — | — | So sánh tham số |
| E5 | 1–5 | — | — | — | Trung bình ± độ lệch chuẩn |
| E6 | — | — | — | — | So sánh có/không bonus |

**Lưu ý:** 32 phòng chỉ là cận dưới tính theo tổng ô nếu không có phòng bận hoặc ràng buộc phân loại sức chứa; không bảo đảm tồn tại lịch hợp lệ trong mọi instance.

## Phụ lục: Tái lập và kiểm thử TV6

Cài đặt theo README gốc bằng `uv sync`. Chạy `uv run pytest tests/test_export_visualize.py -v` để kiểm tra định dạng file xuất, nội dung các cột và phát hiện xung đột. Chạy `uv run python -m src.demo_tv6` chỉ để tạo dữ liệu MOCK kiểm tra bố cục và đường dẫn trước khi TV5 bàn giao dữ liệu GA thật.

Giao diện tích hợp với TV1/TV5:

```python
best_chrom, history = run_ga(inst, params)
plot_history(history, 'results/E1/fitness.png')
plot_room_heatmap(best_chrom, inst, 'results/E1/room_heatmap.png')
export_schedule(best_chrom, inst, 'results/E1/schedule')
```

Trước khi nộp: nhóm hoàn tất thông tin thành viên, % đóng góp (tổng 100%), các chương 1–9, điền số liệu thí nghiệm thực, trích một phần thời khóa biểu, gắn đồ thị thực, rồi xuất chung thành PDF duy nhất trong `HW3_YOURNAME.zip`.
