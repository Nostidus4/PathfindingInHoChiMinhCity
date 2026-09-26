# Phạm vi dự án (M1)

> Owner: toàn nhóm. Tóm tắt từ *Scope Proposal*. Khi quyết định nào thay đổi thì cập nhật file này trước.

## 1. Đề bài

> **TOPIC 2: Pathfinding in Ho Chi Minh City.** Construct a map of at least 100 points of interest in
> HCMC. You define a heuristic that is function of vehicle density, travel speed, or flow rate… In other
> words, heuristic value at a point of interest is NOT a constant, but rather a function of different
> inputs (time-variant, constants, ...). Based on the collected data, propose the shortest/cheapest path
> from Point A to Point B in HCMC using A\* search. You should display your result on a map for
> visualization. Does the heuristic satisfy Admissibility and Consistency conditions? Note: You might as
> well use real-time data from different sources in HCMC. For example:
> <https://giaothong.hochiminhcity.gov.vn/>

## 2. Yêu cầu và cách đáp ứng

| # | Yêu cầu của thầy | Cách nhóm hiểu | Cách đáp ứng | Module | Code |
| --- | --- | --- | --- | --- | --- |
| R1 | Map ≥ 100 POI trong HCMC | Graph có ≥ 100 node là các điểm xe đi qua được (landmark, ngã tư, nút giao) trong Quận 1, 3, 5, Bình Thạnh, Phú Nhuận | Dataset khoảng 150 POI, ≥ 20 POI mỗi quận, mỗi POI có ID, tên, toạ độ, quận | M2, M3 | `src/data/`, `src/graph/` |
| R2 | Heuristic là hàm của density, speed, flow; không phải hằng số tại POI | $h(n, t)$ phụ thuộc thời gian $t$, và qua đó phụ thuộc density, speed, flow cùng các hằng số | Heuristic động `dynamic_ub` cùng các mode dùng để đối chiếu | M6 | `src/cost/heuristics/` |
| R3 | Đề xuất shortest/cheapest path A→B bằng A\* | "Cheapest" là thời gian đi ngắn nhất, có tính traffic tại thời điểm xe đi qua. Có thêm mode distance làm baseline phụ | Time-dependent A\*, so với time-dependent Dijkstra làm ground truth | M5, M7 | `src/search/` |
| R4 | Hiển thị kết quả trên bản đồ | Bản đồ có POI, route, ETA, thống kê | UI chia 3 tầng T0, T1, T2 | M9 | `src/viz/`, `src/cli.py`, `app/` |
| R5 | Heuristic có admissible và consistent không? | Phải trả lời kèm chứng minh và kiểm chứng bằng số | Chứng minh toán, test tự động, và phản ví dụ cho mode cố tình vi phạm | M8 | `src/validation/` |
| R6 | (Optional) dùng dữ liệu real-time | Dùng để hiệu chỉnh, không nằm trên đường găng | Interface `TrafficProvider` và khảo sát có time-box | M4 | `src/traffic/snapshot.py` |

## 3. Phát biểu bài toán

**Time-dependent traffic-aware pathfinding.** Cho đồ thị có hướng $G = (V, E)$ và thời điểm xuất phát
$t_0$. Tìm đường $P$ từ $A$ đến $B$ sao cho tổng thời gian đi là nhỏ nhất. Thời gian qua mỗi edge phụ thuộc
vào thời điểm xe **dự kiến** vào edge đó.

| Ký hiệu | Ý nghĩa |
| --- | --- |
| $\text{Traffic}(e, t) = \{v, k, q\}$ | Trạng thái giao thông của edge $e$ lúc $t$: tốc độ trung bình, mật độ, lưu lượng |
| $c(u, v, t) = \dfrac{\text{length}(u, v)}{v_{\text{eff}}(e, t)}$ | Chi phí edge, tính bằng giây |
| $g(n)$ | Thời gian tích luỹ từ $A$ tới $n$ |
| $t_n = t_0 + g(n)$ | Thời điểm xe tới $n$ |
| $h(n, t)$ | Ước lượng thời gian còn lại từ $n$ tới $B$ |
| $f(n, t) = g(n) + h(n, t)$ | Độ ưu tiên trong open set |

**Input:** `start`, `goal`, `departure_time`, `heuristic_mode`.

**Output (`RouteResult`):** `path`, `departure_time`, `estimated_arrival_time`, `total_travel_time`,
`total_distance`, `expanded_nodes`, `execution_time`, cộng thêm `trace` nếu bật.

Tên các trường này trong code nằm ở `src/models.py`:

| Proposal | `RouteResult` |
| --- | --- |
| `departure_time` | `departure_time_s` |
| `estimated_arrival_time` | `arrival_time_s` |
| `total_travel_time` | `travel_time_s` (property) |
| `total_distance` | `total_distance_m` |
| `execution_time` | `runtime_ms` |

## 4. Quyết định thiết kế

| # | Chủ đề | Quyết định | Trạng thái |
| --- | --- | --- | --- |
| D1 | Cost metric | Thời gian đi (giây). Mode `distance` là baseline phụ | Đề xuất |
| D2 | Nguồn traffic | Synthetic (Greenshields) là chính, real-time là optional | Đề xuất |
| D3 | Graph và POI | **Curated POI graph**: node là POI, edge là đoạn đường thật giữa hai POI kề nhau | ✅ Đã chốt |
| D4 | Phương tiện | Một profile, mặc định là xe máy, có thể đổi tham số | Đề xuất |
| D5 | Effective speed | Greenshields có giới hạn theo capacity. BPR là mode phụ | Đề xuất |
| D6 | Heuristic | 4 mode: `zero`, `static_vmax`, `dynamic_ub`, `dynamic_weighted` | ✅ Đã chốt |
| D7 | UI | T0 là CLI (bắt buộc), T1 là bản đồ tĩnh, T2 là bản đồ tương tác (extra) | Đề xuất |
| D8 | Trace mode | Engine ghi lại từng bước expand ngay từ đầu | Đề xuất |

Chi tiết D3 xem [graph_construction.md](graph_construction.md). D2 và D5 xem [traffic_model.md](traffic_model.md).
D6 xem [heuristic_proof.md](heuristic_proof.md).

## 5. Module, work package và phân công

| Người | WP | Module | Việc chính |
| --- | --- | --- | --- |
| P1 | WP1 | M2 | Dataset POI (khoảng 150 điểm, cân bằng 5 quận). Xong dataset thì khảo sát real-time (optional, time-box 1–2 ngày) và chọn các cặp A/B cho experiment |
| P2 | WP2 | M3 | Dựng graph có hướng từ POI và OSM, cache graph, kiểm tra liên thông và `length ≥ haversine` |
| P3 | WP3 | M4 | Traffic simulator (Greenshields), `TrafficProvider`, `get_traffic(edge, time)`, test FIFO |
| P4 | WP4 | M5, M6 | Effective speed, `edge_cost`, 4 heuristic, chứng minh admissibility và consistency |
| P5 | WP5 | M7, M8 | A\* engine, Dijkstra làm ground truth, trace mode, validator admissibility và consistency |
| P6 | WP6 | M9, M10 | CLI và UI (T0/T1/T2), experiment runner, integration test, tổng hợp báo cáo PDF |

**Cặp review chéo:** mỗi người review code và tài liệu của người kia trong cặp.

- **P1 ↔ P2:** dữ liệu POI và graph đi liền với nhau.
- **P3 ↔ P4:** heuristic dùng trực tiếp traffic. $V_{ub}(t)$ cần quét mọi edge ở mọi mốc thời gian, nên P3
  tính trước bảng tốc độ tối đa theo thời gian (`SpeedBounds`). Như vậy P4 không phải gọi `get_traffic` hàng nghìn lần.
- **P5 ↔ P6:** engine và tích hợp.

## 6. Phạm vi

**Trong phạm vi:** 5 quận trung tâm; ≥ 100 POI; time-dependent A\*; traffic giả lập theo Greenshields;
4 heuristic mode; validation admissibility và consistency; CLI và bản đồ; báo cáo.

**Ngoài phạm vi** (trừ khi dư thời gian): full road network toàn khu vực; nhiều loại phương tiện; đèn giao
thông, rẽ trái/phải, chi phí qua ngã tư; dự báo traffic bằng machine learning; xử lý ảnh camera để đếm mật độ;
deploy production.

## 7. Rủi ro và cách giảm

| Rủi ro | Cách giảm |
| --- | --- |
| Graph nhỏ nên A\* gần bằng Dijkstra | Nhắm khoảng 150 node; chạy experiment trên nhiều cặp A/B và báo cáo trung bình; chấp nhận chênh lệch nhỏ và giải thích trong báo cáo |
| $V_{ub}$ yếu do dùng suffix max | Đo trong experiment; thu hẹp cửa sổ mô phỏng hoặc thêm biến thể window |
| FIFO bị vi phạm | Dùng profile mượt; test bằng số trên mọi edge |
| Real-time không có dữ liệu số | Time-box; coi là optional; ghi lại kết quả khảo sát |
| Thầy hiểu "map" khác với nhóm | Hỏi thầy sớm (xem §9) |
| Ghép UI tốn thời gian | UI chỉ gọi engine; chia tầng T0/T1/T2 |
| Các WP phụ thuộc nhau, người sau phải chờ | Khoá interface sớm; mọi người dùng mock data từ ngày đầu; P1 và P2 giao bản dữ liệu thô sớm |
| Thiếu thời gian | Cắt theo thứ tự: T2 → real-time → BPR → T1 |

## 8. Tiêu chí hoàn thành

- [ ] Dataset có ≥ 100 POI, mỗi quận ≥ 20 POI; graph liên thông mạnh.
- [ ] A\* với `zero` cho cost bằng Dijkstra trên mọi cặp test.
- [ ] A\* với `static_vmax` và `dynamic_ub` cho cost tối ưu (bằng Dijkstra) và expand ít node hơn `zero`.
- [ ] Test tự động xác nhận `dynamic_ub` admissible và consistent; chỉ ra được ít nhất một ca `dynamic_weighted` vi phạm.
- [ ] Ít nhất một cặp A/B cho thấy đổi giờ xuất phát thì cost hoặc route thay đổi.
- [ ] Route hiển thị được trên bản đồ; CLI xử lý được input sai, không có đường đi, thiếu dữ liệu.

## 9. Sản phẩm bàn giao

1. Source code Python hoàn chỉnh, chạy được bằng CLI.
2. Dataset POI và graph (file cache).
3. Traffic simulator kèm tài liệu tham số.
4. Bản đồ hiển thị route (tối thiểu T1).
5. Bảng và biểu đồ experiment: so sánh 4 heuristic theo cost, expanded nodes, runtime; demo time-dependent (cùng A/B, khác giờ).
6. Kết quả validation admissibility và consistency, kèm phản ví dụ.
7. Báo cáo PDF, có phần giải thích thuật toán từng bước.

## 10. Việc còn treo

- [ ] (Không bắt buộc) Hỏi nhanh thầy: *"Graph gồm các POI, với edge là đường thật giữa chúng, có được không?"*
- [ ] Giao P1 khảo sát real-time sau khi xong dataset (time-box 1–2 ngày).
- [ ] Đóng băng interface (tag `interfaces-v1`), sau đó chia việc chính thức.
