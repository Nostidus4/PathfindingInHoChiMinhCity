# WP5 — Time-dependent A* & Heuristic Validation

Bộ source dành cho M7/M8 theo `Introduction-to-AI.pdf`, mục 7, 8, 11 và 14.
Chạy độc lập bằng mock data, rồi thay graph/cost/heuristic bằng interface của WP2–WP4.
Python >= 3.10, chỉ dùng thư viện chuẩn, không cần pip install.

## 1. Chạy ngay (Windows / Linux / macOS)

Giải nén, mở terminal trong thư mục `wp5`:

```bash
python demo.py --start S --goal G --time 08:00 --heuristic dynamic_ub --trace
python demo.py --validate --output outputs/validation.json
python -m unittest discover -s tests -v
```

Nếu máy dùng lệnh `python3`, thay `python` bằng `python3`. Trên Windows cũng có thể dùng `py`.
So sánh phản ví dụ:

```bash
python demo.py --heuristic dynamic_weighted --time 08:00
python demo.py --heuristic zero --time 08:00
```

S → U trả `route: null` vì không có đường đi; node không tồn tại và giờ sai được CLI báo lỗi.
`--output` xuất JSON đầy đủ; không bắt buộc để chạy demo.

## 2. Cấu trúc

- `algorithms/astar.py`: A* phụ thuộc thời gian, heap, loại entry cũ, reopen node, trace.
- `algorithms/dijkstra.py`: Dijkstra độc lập để đối chiếu (tương đương A* với h=0 về lý thuyết).
- `algorithms/result.py`: RouteResult dùng chung với WP6.
- `algorithms/contracts.py`: Protocol và kiểm tra giá trị đầu vào.
- `validation/validator.py`: admissibility, consistency, FIFO, so sánh cost và trích phản ví dụ.
- `examples/mock_data.py`: graph 6 node, traffic và 4 heuristic giả lập phục vụ WP5.
- `demo.py`: CLI minh họa, có thể chuyển cho WP6.
- `tests/test_wp5.py`: test chức năng và kiểm chứng thuật toán.
- `INTEGRATION.md`: hợp đồng interface và cách nối vào source nhóm.
- `REPORT_WP5.md`: ghi chú kỹ thuật để viết phần báo cáo WP5.
- `outputs/`: kết quả demo/validation và test đã chạy.

## 3. Quy ước thuật toán

Tất cả travel time/heuristic dùng **giây**, thời gian là **giây từ 00:00**, length dùng **mét**.
Ở node u: `entry_time = departure_time + g[u]`.
Ở node v mới được relax: `h(v, goal, departure_time + tentative_g, mode)`.
Không lấy traffic tại giờ khởi hành cho toàn bộ đường đi.

`astar(...)` / `dijkstra(...)` trả RouteResult hoặc `None` nếu không có đường đi.
RouteResult có path, departure_time, estimated_arrival_time, total_travel_time,
total_distance, expanded_nodes, execution_time (giây), trace, edge_ids.
`edge_ids` hỗ trợ graph có parallel edges; tổng khoảng cách lấy từ các edge thực sự được chọn.

`expanded_nodes` đếm lần pop entry hợp lệ, gồm cả goal; node được reopen có thể được đếm lại.
Trace ghi `node, g, h, f, arrival_time`, danh sách relaxed edges và open_set sau relax.
Entry stale không xuất hiện trong trace. Goal cũng có trace, nhưng không relax cạnh đi ra.
Trace mặc định tắt để tránh chi phí lưu nhiều snapshot.

## 4. Điều kiện để kết quả tối ưu

- Graph có hướng, các node ID hashable; edge length không âm, hữu hạn.
- Chi phí cạnh không âm; có thể dùng +inf cho cạnh bị chặn.
- **FIFO**: `t + c(e,t)` không giảm theo t; không xét hành động đứng chờ.
- Cost/heuristic deterministic trong một lần chạy, cùng một snapshot traffic.
- Heuristic không âm, hữu hạn, bằng 0 tại goal; admissible để bảo đảm tối ưu.
- Reopening xử lý heuristic admissible nhưng inconsistent; không khắc phục traffic non-FIFO.

Engine không tự quét FIFO trước mỗi route để tránh chi phí lớn. Chạy validator khi nhận data WP3.
Nếu FIFO vi phạm, sửa traffic model hoặc dùng thuật toán trạng thái thời gian/multiple labels;
không dùng output Dijkstra hiện tại làm ground truth cho mô hình non-FIFO.
Một profile mượt tự nó không bảo đảm FIFO.

`dynamic_weighted` cố tình có thể overestimate; engine vẫn chạy để phục vụ thí nghiệm,
nhưng không có bảo đảm optimality. Overestimate không bắt buộc gây route sai ở mọi cặp.

## 5. Kết quả kiểm chứng đóng gói

17 test PASS. Bao gồm:

- 6×6 cặp node × 97 thời điểm × 3 mode = 10.476 phép so cost với Dijkstra.
- zero, static_vmax, dynamic_ub: admissibility/consistency PASS trên mock.
- FIFO trên lưới dày 60 giây, kiểm tra biên clamp.
- 20 graph random FIFO, các cặp node ở hai giờ xuất phát.
- Phản ví dụ weighted: S → G đắt hơn S → A → G.
- Arrival-time cost, unreachable, start=goal, tie heap với ID khác kiểu,
  parallel edge, stale entry, reopen, zero-cost cycle và dữ liệu sai.

Số liệu và JSON của mock trong `outputs/`; runtime tùy máy.
Mock không phải road graph thực, không thay thế dataset >=100 POI của WP1/WP2.
Traffic mock không phải Greenshields; WP3/WP4 chịu trách nhiệm mô hình thật.
Không khẳng định A* luôn expand ít node hơn Dijkstra: phụ thuộc graph, heuristic và tie-breaking.

## 6. Khi nhận source các bạn

Làm theo `INTEGRATION.md`, chạy FIFO rồi validators trên graph/traffic thật.
Báo cáo riêng số ca checked/skipped; `valid=True` với zero samples không đủ kết luận.
Admissibility bỏ qua cặp unreachable và đếm skipped (chi phí thật của cặp đó là vô hạn).
Consistency kiểm tra cả h(goal,t)=0 và từng edge ở thời gian đến đích cạnh.
Validator vi phạm trả counterexample; input numeric sai phát sinh ValueError để sửa provider.
Các kiểm tra là **sampled evidence**, không phải chứng minh cho mọi thời điểm liên tục.
